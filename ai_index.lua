return function(display_handle, chemin)
    local FICHIER_PAR_DEFAUT = "C:/ProgramData/MALightingTechnology/gma3_library/ai_index.json"
    if chemin == nil or chemin == "" then
        chemin = FICHIER_PAR_DEFAUT
    end
    local MAX_PAR_POOL = 20000

    local function lire(objet, cle)
        local ok, valeur = pcall(function() return objet[cle] end)
        if ok then
            return valeur
        end
        return nil
    end

    local function enfants_de(objet)
        local ok, liste = pcall(function() return objet:Children() end)
        if ok and liste ~= nil then
            return liste
        end
        return {}
    end

    local function nom_de(objet)
        return tostring(lire(objet, "name") or "?")
    end

    local function numero(objet)
        for _, cle in ipairs({ "no", "No", "NO", "number" }) do
            local v = tonumber(lire(objet, cle))
            if v ~= nil then
                if math.type(v) == "float" and v == math.floor(v) then
                    v = math.tointeger(v)
                end
                return v
            end
        end
        return nil
    end

    local function echapper(texte)
        texte = tostring(texte or "")
        texte = texte:gsub("\\", "\\\\")
        texte = texte:gsub('"', '\\"')
        texte = texte:gsub("\n", "\\n")
        texte = texte:gsub("\r", "\\r")
        texte = texte:gsub("\t", "\\t")
        texte = texte:gsub("%c", " ")
        return texte
    end

    local function noms_de(liste)
        local noms = {}
        for _, o in ipairs(liste) do
            noms[#noms + 1] = nom_de(o)
        end
        return table.concat(noms, ", ")
    end

    local function est_apparence(objet)
        return string.find(string.lower(nom_de(objet)), "appearance", 1, true) ~= nil
    end

    -- Les apparences sont au niveau du show, pas dans le DataPool : on cherche depuis la racine
    local function chercher_apparences()
        local trouves = {}
        local ok, racine = pcall(Root)
        if not ok or racine == nil then
            return trouves, nil
        end
        local show = lire(racine, "ShowData")

        if show ~= nil then
            local direct = lire(show, "Appearances")
            if direct ~= nil then
                trouves[#trouves + 1] = direct
            end
        end

        if #trouves == 0 then
            for _, n1 in ipairs(enfants_de(racine)) do
                if est_apparence(n1) then
                    trouves[#trouves + 1] = n1
                end
                for _, n2 in ipairs(enfants_de(n1)) do
                    if est_apparence(n2) then
                        trouves[#trouves + 1] = n2
                    end
                end
            end
        end
        return trouves, show
    end

    local ok_dp, dp = pcall(DataPool)
    if not ok_dp or dp == nil then
        ErrPrintf("%s", "AI_Index : DataPool() indisponible")
        return
    end

    local pools_racine = enfants_de(dp)
    Printf("%s", "AI_Index : pools du DataPool : " .. noms_de(pools_racine))

    local a_traiter = {}
    local deja = {}
    for _, p in ipairs(pools_racine) do
        a_traiter[#a_traiter + 1] = p
        deja[string.lower(nom_de(p))] = true
    end

    local apparences, show = chercher_apparences()
    local apparences_ajoutees = 0
    for _, p in ipairs(apparences) do
        if not deja[string.lower(nom_de(p))] then
            a_traiter[#a_traiter + 1] = p
            deja[string.lower(nom_de(p))] = true
            apparences_ajoutees = apparences_ajoutees + 1
        end
    end

    if apparences_ajoutees > 0 then
        Printf("%s", "AI_Index : pool d'apparences trouve hors du DataPool")
    elseif not deja["appearances"] then
        local vus = ""
        if show ~= nil then
            vus = noms_de(enfants_de(show))
        end
        ErrPrintf("%s", "AI_Index : aucun pool Appearances trouve. Enfants de ShowData : " .. vus)
    end

    local morceaux = {}
    local resume = {}
    local sans_numero = 0
    local premier_sans_numero = nil

    for _, pool in ipairs(a_traiter) do
        local nom_pool = nom_de(pool)
        local lignes = {}
        local nombre = 0
        local est_preset = string.find(string.lower(nom_pool), "preset", 1, true) ~= nil

        for i, enfant in ipairs(enfants_de(pool)) do
            if i > MAX_PAR_POOL then
                break
            end
            if est_preset then
                local no_type = numero(enfant)
                for _, pr in ipairs(enfants_de(enfant)) do
                    local n = numero(pr)
                    local no_texte = tostring(no_type or "?") .. "." .. tostring(n or "?")
                    lignes[#lignes + 1] = '{"no":"' .. no_texte .. '","name":"' .. echapper(nom_de(pr)) .. '"}'
                    nombre = nombre + 1
                end
            else
                local n = numero(enfant)
                local no_json = "null"
                if n ~= nil then
                    no_json = tostring(n)
                else
                    sans_numero = sans_numero + 1
                    if premier_sans_numero == nil then
                        premier_sans_numero = enfant
                    end
                end
                lignes[#lignes + 1] = '{"no":' .. no_json .. ',"name":"' .. echapper(nom_de(enfant)) .. '"}'
                nombre = nombre + 1
            end
        end

        morceaux[#morceaux + 1] = '{"pool":"' .. echapper(nom_pool) .. '","count":' .. nombre
            .. ',"items":[' .. table.concat(lignes, ",") .. ']}'
        resume[#resume + 1] = nom_pool .. "=" .. nombre
    end

    local ok_io, fichier, erreur = pcall(io.open, chemin, "w")
    if not ok_io or not fichier then
        ErrPrintf("%s", "AI_Index : impossible d'ecrire " .. tostring(chemin) .. " : " .. tostring(fichier or erreur))
        return
    end
    fichier:write('{"version":1,"pools":[' .. table.concat(morceaux, ",") .. ']}')
    fichier:close()

    Printf("%s", "AI_Index : " .. table.concat(resume, " | "))
    Printf("%s", "AI_Index : fichier ecrit -> " .. tostring(chemin))

    if sans_numero > 0 then
        ErrPrintf("%s", "AI_Index : " .. sans_numero .. " objet(s) sans numero lisible. Proprietes du premier :")
        pcall(function() premier_sans_numero:Dump() end)
    end
end
