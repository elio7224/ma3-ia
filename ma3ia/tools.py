import os
import re
import json
import ast
import time
import shutil
import operator
import xml.etree.ElementTree as ET
from itertools import product
from ma3 import MA3
from i18n import tr

ma3 = MA3()

DOSSIERS_TEMP_MA3 = [
    r"C:\ProgramData\MALightingTechnology\gma3_library\datapools\groups\Temp",
    r"C:\ProgramData\MALightingTechnology\gma3_library\datapools\layouts\Temp",
    r"C:\ProgramData\MALightingTechnology\gma3_library\datapools\macros\Temp",
    r"C:\ProgramData\MALightingTechnology\gma3_library\datapools\sequences\Temp",
    r"C:\ProgramData\MALightingTechnology\gma3_library\datapools\presets\Temp",
    r"C:\ProgramData\MALightingTechnology\gma3_library\datapools\shapes\Temp",
    r"C:\ProgramData\MALightingTechnology\gma3_library\datapools\matricks\Temp",
    r"C:\ProgramData\MALightingTechnology\gma3_library\appearances\Temp"  # 📌 Ajout indispensable pour les apparences
]


def appliquer_reglages(hote: str, port: int, bibliotheque: str) -> None:
    """Reconfigure le client OSC et les dossiers de la bibliothèque (appelé par l'app depuis les réglages)."""
    global ma3
    from reglages import dossiers_temp
    ma3 = MA3(hote, int(port))
    DOSSIERS_TEMP_MA3[:] = dossiers_temp(bibliotheque)

# ======================================================================
#  INDEX VIA PLUGIN LUA  +  EXPORT XML À LA DEMANDE
# ======================================================================

PLUGIN_NOM = "AI_Index"      
DELAI_MAX_PLUGIN = 15        
DELAI_MAX_EXPORT = 10        

MOTS_CLES_MA3 = {
    "groups": "Group", 
    "layouts": "Layout", 
    "macros": "Macro", 
    "sequences": "Sequence",
    "presets": "Preset", 
    "shapes": "Shape", 
    "matricks": "MAtricks",
    "appearances": "Appearance"  # 📌 Mappé pour autoriser l'export des apparences
}

INDEX_OBJETS = {}
VERSION_PLUGIN_CONSOLE = None   # version du plugin qui a produit l'index (1 = ancien, sans le champ)
AUTRES_POOLS = []            


def _nom_section(dossier: str) -> str:
    return os.path.basename(os.path.dirname(dossier)).lower()


def _dossier_section(section: str):
    for d in DOSSIERS_TEMP_MA3:
        if _nom_section(d) == section:
            return d
    return None


def _fichier_index() -> str:
    bibliotheque = os.path.dirname(os.path.dirname(os.path.dirname(DOSSIERS_TEMP_MA3[0])))
    return os.path.join(bibliotheque, "ai_index.json")


def _section_pour_pool(nom_pool: str):
    n = nom_pool.lower().replace(" ", "")
    for cle, section in (
        ("preset", "presets"), 
        ("matrick", "matricks"), 
        ("macro", "macros"),
        ("group", "groups"), 
        ("sequence", "sequences"), 
        ("layout", "layouts"),
        ("shape", "shapes"),
        ("appearance", "appearances")  # 📌 Reconnaissance du pool d'apparences
    ):
        if cle in n:
            return section
    return None


def _lancer_plugin_index():
    fichier = _fichier_index()
    try:
        if os.path.exists(fichier):
            os.remove(fichier)
    except OSError as e:
        return tr(f"Impossible de supprimer l'ancien index ({e}).", f"Cannot delete the old index ({e}).")

    chemin_lua = fichier.replace("\\", "/")
    ma3.send(f'Plugin "{PLUGIN_NOM}" "{chemin_lua}"')

    debut = time.time()
    while time.time() - debut < DELAI_MAX_PLUGIN:
        if os.path.exists(fichier):
            try:
                with open(fichier, "r", encoding="utf-8-sig", errors="replace") as f:
                    json.load(f)
                return None
            except (ValueError, OSError):
                pass            
        time.sleep(0.25)
    return tr(f"Le plugin '{PLUGIN_NOM}' n'a pas produit {fichier} en {DELAI_MAX_PLUGIN} s.", f"The '{PLUGIN_NOM}' plugin did not produce {fichier} within {DELAI_MAX_PLUGIN} s.")


def preparer_et_exporter_show() -> str:
    for dossier in DOSSIERS_TEMP_MA3:
        if os.path.exists(dossier):
            for element in os.listdir(dossier):
                chemin = os.path.join(dossier, element)
                try:
                    if os.path.isfile(chemin) or os.path.islink(chemin):
                        os.unlink(chemin)
                    elif os.path.isdir(chemin):
                        shutil.rmtree(chemin)
                except Exception as e:
                    print(f"Impossible de supprimer {chemin}: {e}")
        else:
            try:
                os.makedirs(dossier, exist_ok=True)
            except Exception:
                pass

    print(f"🔌 Lancement du plugin '{PLUGIN_NOM}' dans la console...")
    erreur = _lancer_plugin_index()
    if erreur:
        print("⚠️ " + erreur)
        return erreur
    return tr("Index régénéré par le plugin, cache Temp vidé.", "Index rebuilt by the plugin, Temp cache cleared.")


def _cle_tri(numero: str):
    try:
        return tuple(int(x) for x in numero.split("."))
    except ValueError:
        return (10 ** 9, numero)


def charger_contexte_temp() -> str:
    global INDEX_OBJETS, AUTRES_POOLS, VERSION_PLUGIN_CONSOLE
    INDEX_OBJETS, AUTRES_POOLS = {}, []
    VERSION_PLUGIN_CONSOLE = None

    fichier = _fichier_index()
    if not os.path.exists(fichier):
        return "INDEX INDISPONIBLE : le plugin de la console n'a pas produit de fichier d'index."
    try:
        with open(fichier, "r", encoding="utf-8-sig", errors="replace") as f:
            data = json.load(f)
    except (ValueError, OSError) as e:
        return f"INDEX ILLISIBLE ({e})."
    VERSION_PLUGIN_CONSOLE = data.get("plugin", 1)

    sans_numero = 0
    for pool in data.get("pools", []):
        nom_pool = str(pool.get("pool", ""))
        items = pool.get("items", [])
        section = _section_pour_pool(nom_pool)
        if section is None:
            if items:
                AUTRES_POOLS.append((nom_pool, len(items)))
            continue
        dest = INDEX_OBJETS.setdefault(section, {})
        for it in items:
            no = it.get("no")
            if no is None:
                sans_numero += 1
                continue
            dest[str(no)] = str(it.get("name", ""))

    texte = ("INDEX DES ÉLÉMENTS DU SHOWFILE (lu directement dans la console).\n"
             "Format : numéro=\"nom\". Les NUMÉROS sont les vrais numéros des pools de la console.\n"
             "Un numéro absent de la liste est un emplacement libre.\n")
    for section in sorted(MOTS_CLES_MA3):
        objets = INDEX_OBJETS.get(section, {})
        if objets:
            paires = [f'{n}="{objets[n]}"' for n in sorted(objets, key=_cle_tri)]
            texte += f"\n- SECTION {section.upper()} ({len(objets)} objets) :\n  " + " | ".join(paires) + "\n"
        else:
            texte += f"\n- SECTION {section.upper()} : aucun objet.\n"
    if AUTRES_POOLS:
        texte += "\nAutres pools détectés (non gérés) : " + ", ".join(f"{n} ({c})" for n, c in AUTRES_POOLS) + "\n"
    if sans_numero:
        texte += f"\n⚠️ {sans_numero} objet(s) sans numéro lisible ont été ignorés.\n"
    resume = ", ".join(f"{sec}={len(INDEX_OBJETS.get(sec, {}))}" for sec in sorted(MOTS_CLES_MA3))
    print(f"📚 Index chargé depuis {fichier} : {resume}")
    return texte


def _section_depuis(txt: str, sections):
    t = txt.strip().lower()
    for s in sections:
        if t == s or t == s.rstrip("s"):
            return s
    return None


def _exporter_objet(section: str, numero: str):
    dossier = _dossier_section(section)
    if dossier is None:
        return None
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, f"{numero}.xml")
    if os.path.exists(chemin):
        try:
            os.remove(chemin)
        except OSError:
            pass
    ma3.send(f'Export {MOTS_CLES_MA3[section]} {numero} "{numero}" /Path "Temp"')

    debut, taille_prec = time.time(), -1
    while time.time() - debut < DELAI_MAX_EXPORT:
        if os.path.exists(chemin):
            taille = os.path.getsize(chemin)
            if taille > 0 and taille == taille_prec:      
                return chemin
            taille_prec = taille
        time.sleep(0.15)
    return None


# ----------------------------------------------------------------------
#  Compaction du XML exporté (le XML brut de grandMA3 est très bavard)
# ----------------------------------------------------------------------

TAILLE_PARTIE = 60000   # caractères envoyés au modèle par appel (~15-20k tokens)

# Attributs techniques sans intérêt pour le modèle.
ATTRIBUTS_IGNORES = {
    "Guid", "Cooked", "Size", "GridPosMatr", "AlignRangeX", "AlignRangeY", "AlignRangeZ",
    "PreserveGridPositions", "MAgic", "RelAddr", "RelAddrNum", "AddressNum", "IDType", "Selective",
}
# Valeurs par défaut répétées partout : omises.
VALEURS_PAR_DEFAUT = {"Action": "Pool Default", "Mode": "0"}
# Attributs qui changent d'un projecteur à l'autre : ignorés pour regrouper les Phaser identiques.
ATTRIBUTS_PAR_PROJECTEUR = {"ID", "GridPos"}


def _citer(v: str) -> str:
    """Entoure une valeur contenant des espaces, sans échapper ses guillemets internes."""
    if not re.search(r"[\s=]", v):
        return v
    for g1, g2 in (('"', '"'), ("'", "'"), ("«", "»")):
        if g1 not in v:
            return f"{g1}{v}{g2}"
    return f"«{v}»"


def _attributs(e, sauf=()) -> str:
    return " ".join(f"{k}={_citer(v.strip())}" for k, v in e.attrib.items()
                    if k not in ATTRIBUTS_IGNORES and k not in sauf and v.strip() != ""
                    and VALEURS_PAR_DEFAUT.get(k) != v.strip())


def _ligne(e, sauf=()) -> str:
    return f"{e.tag} {_attributs(e, sauf)}".rstrip()


def _plages(ids) -> str:
    """['401','402','403','410'] -> '401-403, 410' ; ['301.1.1','301.1.2'] -> '301.1.1-2'."""
    res, groupe = [], None          # groupe = [préfixe, début, fin]
    for i in ids:
        prefixe, _, dernier = i.rpartition(".")
        if dernier.isdigit():
            n = int(dernier)
            if groupe and groupe[0] == prefixe and n == groupe[2] + 1:
                groupe[2] = n
                continue
            if groupe:
                res.append(groupe)
            groupe = [prefixe, n, n]
        else:
            if groupe:
                res.append(groupe); groupe = None
            res.append(i)
    if groupe:
        res.append(groupe)
    textes = []
    for g in res:
        if isinstance(g, str):
            textes.append(g)
        else:
            base = f"{g[0]}." if g[0] else ""
            textes.append(f"{base}{g[1]}" if g[1] == g[2] else f"{base}{g[1]}-{g[2]}")
    return ", ".join(textes)


def _signature_phaser(p) -> str:
    """Texte d'un Phaser sans ce qui varie par projecteur (pour regrouper les identiques)."""
    etapes = " ; ".join(_ligne(s) for s in p)
    return f"{_ligne(p, ATTRIBUTS_PAR_PROJECTEUR)} -> {etapes}" if etapes else _ligne(p, ATTRIBUTS_PAR_PROJECTEUR)


def _compacter(e, niveau: int, lignes: list):
    retrait = "  " * niveau
    if e.tag == "DependencyExport":
        cibles = [d.get("Address", "?").replace("ShowData.DataPools.Default.", "") for d in e]
        lignes.append(f"{retrait}Dépendances (non détaillées, lisibles à part) : " + ", ".join(cibles))
        return
    lignes.append(retrait + _ligne(e))
    # Les Phaser identiques (même valeur sur plusieurs projecteurs) sont regroupés sur une ligne,
    # à la place du premier d'entre eux ; l'ordre des autres enfants est conservé.
    groupes, ordre = {}, []
    for enf in e:
        if enf.tag == "Phaser":
            sig = _signature_phaser(enf)
            if sig not in groupes:
                groupes[sig] = []
                ordre.append(("phaser", sig))
            groupes[sig].append(enf.get("ID", "?"))
        else:
            ordre.append(("noeud", enf))
    for genre, val in ordre:
        if genre == "phaser":
            lignes.append(f"{retrait}  [ID {_plages(groupes[val])}] {val}")
        else:
            _compacter(val, niveau + 1, lignes)


def compacter_xml(chemin: str) -> str:
    """Convertit un export XML grandMA3 en texte indenté compact. Renvoie le XML brut s'il est illisible."""
    try:
        racine = ET.parse(chemin).getroot()
    except (ET.ParseError, OSError):
        with open(chemin, "r", encoding="utf-8-sig", errors="ignore") as f:
            return f.read()
    lignes = []
    for enf in racine:          # saute la balise <GMA3>
        _compacter(enf, 0, lignes)
    return "\n".join(lignes)


def _decouper(texte: str, taille: int = TAILLE_PARTIE) -> list:
    """Découpe en parties d'environ `taille` caractères, sans couper une ligne en deux (sauf ligne géante)."""
    parties, courant, n = [], [], 0
    for ligne in texte.split("\n"):
        while len(ligne) > taille:
            if courant:
                parties.append("\n".join(courant)); courant, n = [], 0
            parties.append(ligne[:taille]); ligne = ligne[taille:]
        if n + len(ligne) + 1 > taille and courant:
            parties.append("\n".join(courant)); courant, n = [], 0
        courant.append(ligne); n += len(ligne) + 1
    if courant:
        parties.append("\n".join(courant))
    return parties or [""]


def lire_xml_temp(nom_objet: str = "", partie: int = 1) -> str:
    if not nom_objet or not nom_objet.strip():
        return tr("Aucun objet spécifié pour la lecture.", "No object given to read.")
    if not INDEX_OBJETS:
        charger_contexte_temp()
    if not INDEX_OBJETS:
        return tr("Index indisponible.", "Index unavailable.")

    sections_connues = list(MOTS_CLES_MA3)
    requete = nom_objet.strip().lower()
    section_txt = None

    if "/" in requete:
        section_txt, requete = [p.strip() for p in requete.split("/", 1)]
    else:
        m = re.match(r"^([a-z]+)\s+(\d+(?:\.\d+)?)$", requete)
        if m and _section_depuis(m.group(1), sections_connues):
            section_txt, requete = m.group(1), m.group(2)

    section = None
    if section_txt:
        section = _section_depuis(section_txt, sections_connues)
        if not section:
            return tr(f"Section '{section_txt}' inconnue.", f"Unknown section '{section_txt}'.")
    sections = [section] if section else sections_connues

    trouves = []   
    if re.match(r"^\d+(?:\.\d+)?$", requete):
        for s in sections:
            if requete in INDEX_OBJETS.get(s, {}):
                trouves.append((s, requete, INDEX_OBJETS[s][requete]))
    else:
        exacts, partiels = [], []
        for s in sections:
            for numero, nom in INDEX_OBJETS.get(s, {}).items():
                if nom.lower() == requete:
                    exacts.append((s, numero, nom))
                elif requete in nom.lower():
                    partiels.append((s, numero, nom))
        trouves = exacts or partiels

    if not trouves:
        return tr(f"Aucun objet '{nom_objet}' trouvé.", f"No object '{nom_objet}' found.")
    if len(trouves) > 1:
        liste = "\n".join(f'- {s}/{n} ("{nom}")' for s, n, nom in trouves[:30])
        return tr("Plusieurs objets correspondent :", "Several objects match:") + f"\n{liste}"

    s, numero, nom = trouves[0]
    chemin = _exporter_objet(s, numero)
    if chemin is None:
        return tr(f"L'export de {s}/{numero} n'a pas produit de fichier.", f"Exporting {s}/{numero} produced no file.")
    try:
        contenu = compacter_xml(chemin)
    except Exception as e:
        return tr(f"Erreur de lecture : {e}", f"Read error: {e}")
    parties = _decouper(contenu, TAILLE_PARTIE)
    try:
        partie = int(partie)
    except (TypeError, ValueError):
        partie = 1
    if not 1 <= partie <= len(parties):
        return tr(f"Partie {partie} inexistante : {s}/{numero} a {len(parties)} partie(s).", f"Part {partie} does not exist: {s}/{numero} has {len(parties)} part(s).")
    entete = f'--- {s}/{numero} « {nom} » (format compact'
    if len(parties) > 1:
        entete += f", partie {partie}/{len(parties)}"
    entete += ") ---"
    texte = f"{entete}\n{parties[partie - 1]}"
    if partie < len(parties):
        texte += "\n... " + tr(f"[Suite : partie {partie + 1}/{len(parties)}. Si la réponse en dépend, rappelle "
                                f"lire_xml_temp avec partie={partie + 1} toi-même, sans demander à l'utilisateur]",
                                f"[Continued: part {partie + 1}/{len(parties)}. If the answer depends on it, call "
                                f"lire_xml_temp with partie={partie + 1} yourself, without asking the user]")
    return texte


def create_macro(number: int = 1, name: str = "Macro Sans Nom", lines: list[str] = None) -> str:
    if lines is None:
        lines = []
        
    cmds = [f"Store Macro {number}", f"ChangeDestination Macro {number}"]
    for i, line in enumerate(lines, start=1):
        cmds.append("Insert")
        cmds.append(f'Set {i} Property "Command" "{line}"')
    cmds.append("ChangeDestination Root")
    cmds.append(f'Label Macro {number} "{name}"')
    for c in cmds:
        ma3.send(c)
    return tr(f"Macro {number} créée avec succès ({len(lines)} lignes).", f"Macro {number} created ({len(lines)} lines).")


def configure_matricks(number: int = 1, name: str = "MAtricks", xgroup: int = None, xblock: int = None, xwings: int = None, interleave: int = None) -> str:
    cmds = [f"Store MAtricks {number}"]
    if name:
        cmds.append(f'Label MAtricks {number} "{name}"')
    if xgroup is not None:
        cmds.append(f'Set MAtricks {number} Property "XGroup" "{xgroup}"')
    if xblock is not None:
        cmds.append(f'Set MAtricks {number} Property "XBlock" "{xblock}"')
    if xwings is not None:
        cmds.append(f'Set MAtricks {number} Property "XWings" "{xwings}"')
    if interleave is not None:
        cmds.append(f'Set MAtricks {number} Property "Interleave" "{interleave}"')
        
    for c in cmds:
        ma3.send(c)
    return tr(f"MAtricks {number} ('{name}') configuré avec succès.", f"MAtricks {number} ('{name}') configured.")


# ----------------------------------------------------------------------
#  Sauvegarde automatique du show avant les actions de masse
#  (manuel 2.5 : à chaque SaveShow, grandMA3 garde une copie datée dans « Backup Shows », 10 max par show)
# ----------------------------------------------------------------------

SAUVEGARDE_INTERVALLE_S = 120          # pas plus d'une sauvegarde toutes les 2 min (préserve les 10 copies de la console)
_derniere_sauvegarde = [0.0]
_MOTIF_MASSE = re.compile(r"^\s*(delete|store|copy|move)\b.*\bthru\b", re.IGNORECASE)


def est_commande_de_masse(cmd: str) -> bool:
    """Delete / Store / Copy / Move sur une plage (… Thru …)."""
    return bool(_MOTIF_MASSE.search(cmd or ""))


def sauvegarder_avant_masse() -> str:
    """Envoie SaveShow avant une action de masse. Renvoie une ligne à ajouter au résultat de l'outil."""
    try:
        from reglages import charger
        actif = charger().get("sauvegarde_auto", True)
    except Exception:
        actif = True
    if not actif:
        return tr("(Sauvegarde automatique désactivée dans les Réglages : aucune copie faite.)", "(Automatic backup turned off in Settings: no copy made.)")
    if time.time() - _derniere_sauvegarde[0] < SAUVEGARDE_INTERVALLE_S:
        return tr("(Show déjà sauvegardé il y a moins de 2 minutes : pas de nouvelle copie.)", "(Show already saved less than 2 minutes ago: no new copy.)")
    ma3.send("SaveShow")
    _derniere_sauvegarde[0] = time.time()
    time.sleep(1.0)                    # laisse la console écrire le fichier avant la suite
    return tr("💾 Show sauvegardé (SaveShow) avant l'action : grandMA3 garde une copie datée dans Backup Shows "
              "(Menu > Backup > Load > Backup Shows pour revenir en arrière).",
              "💾 Show saved (SaveShow) before the action: grandMA3 keeps a dated copy in Backup Shows "
              "(Menu > Backup > Load > Backup Shows to go back).")


def run_command(cmd: str = "") -> str:
    if not cmd:
        return tr("Aucune commande fournie.", "No command given.")
    if est_commande_de_masse(cmd):
        note = sauvegarder_avant_masse()
        return f"{note}\n{ma3.send(cmd)}"
    return ma3.send(cmd)


def generate_fx_grid(start_macro: int = 1, group_start: int = 1, group_count: int = 1, phases: list[int] = None) -> str:
    if phases is None:
        phases = [0]
    note = sauvegarder_avant_masse()

    current_macro = start_macro
    total_created = 0
    for g in range(group_start, group_start + group_count):
        for phase in phases:
            macro_name = f"G{g} Phase {phase}°"
            lines = [
                f"Selection Group {g}",
                f"Attribute 'Pan' Property 'XPhase' '{phase}'"
            ]
            create_macro(current_macro, macro_name, lines)
            current_macro += 1
            total_created += 1
    return f"{note}\n" + tr(f"Succès ! {total_created} macros générées.", f"Done: {total_created} macros generated.")


MAX_MACROS_PAR_APPEL = 1000

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}


def _eval_expr(expr: str, variables: dict):
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.Name) and n.id in variables:
            return variables[n.id]
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            g, d = ev(n.left), ev(n.right)
            if not (isinstance(g, (int, float)) and isinstance(d, (int, float))):
                raise ValueError(f"Calcul impossible sur du texte dans {{{expr}}}")
            return _OPS[type(n.op)](g, d)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        raise ValueError(f"Expression non autorisée : {{{expr}}}")
    return ev(ast.parse(expr.strip(), mode="eval"))


def _rendre(modele: str, variables: dict) -> str:
    return re.sub(r"\{([^{}]+)\}", lambda m: str(_eval_expr(m.group(1), variables)), modele)


def _valeurs_boucle(boucle: dict) -> list:
    if "values" in boucle and boucle["values"] is not None:
        return list(boucle["values"])
    debut = int(boucle.get("start", 1))
    nombre = int(boucle.get("count", 1))
    pas = int(boucle.get("step", 1))
    return [debut + k * pas for k in range(nombre)]


def _commandes_macro(number, name, lines):
    cmds = [
        f"Delete Macro {number} /noconfirm",
        f"Store Macro {number}",
        f"ChangeDestination Macro {number}"
    ]
    for i, line in enumerate(lines, start=1):
        if i > 1:
            cmds.append("Insert")
        cmds.append(f'Set {i} Property "Command" "{line}"')
    cmds.append("ChangeDestination Root")
    cmds.append(f'Label Macro {number} "{name}"')
    return cmds


def generate_macros_from_template(start_macro: int = 1, name_template: str = "Macro {macro}",
                                  line_templates: list = None, loops: list = None,
                                  macro_step: int = 1, dry_run: bool = False,
                                  delai_ms: int = 10) -> str:
    if not line_templates:
        return tr("Erreur : line_templates est vide.", "Error: line_templates is empty.")
    loops = loops or []

    noms = [b.get("var") for b in loops]
    if any(not n for n in noms) or len(set(noms)) != len(noms):
        return tr("Erreur : chaque boucle doit avoir un 'var' unique.", "Error: each loop needs a unique 'var'.")
    if any(n in ("macro", "idx") for n in noms):
        return tr("Erreur : 'macro' et 'idx' sont réservés.", "Error: 'macro' and 'idx' are reserved.")
    try:
        listes = [_valeurs_boucle(b) for b in loops]
    except Exception as e:
        return tr(f"Erreur dans les boucles : {e}", f"Error in the loops: {e}")
    combinaisons = list(product(*listes)) if listes else [()]

    total = len(combinaisons)
    if total > MAX_MACROS_PAR_APPEL:
        return tr(f"Refusé : {total} macros demandées, maximum {MAX_MACROS_PAR_APPEL}.", f"Refused: {total} macros requested, maximum {MAX_MACROS_PAR_APPEL}.")

    macros = []
    try:
        for idx, combi in enumerate(combinaisons):
            variables = dict(zip(noms, combi))
            variables["macro"] = start_macro + idx * macro_step
            variables["idx"] = idx
            nom = _rendre(name_template, variables)
            lignes = [_rendre(t, variables) for t in line_templates]
            for l in lignes + [nom]:
                if '"' in l:
                    return tr(f"Erreur : guillemets doubles interdits : {l}.", f"Error: double quotes are not allowed: {l}.")
            macros.append((variables["macro"], nom, lignes))
    except Exception as e:
        return tr(f"Erreur de modèle : {e}", f"Template error: {e}")

    premier, dernier = macros[0][0], macros[-1][0]
    if dry_run:
        apercu = []
        for num, nom, lignes in macros[:3] + (macros[-1:] if total > 3 else []):
            apercu.append(f"Macro {num} « {nom} » :\n" + "\n".join(f"    {i}. {l}" for i, l in enumerate(lignes, 1)))
        return tr(f"APERÇU : {total} macros, numéros {premier} à {dernier}.", f"PREVIEW: {total} macros, numbers {premier} to {dernier}.") + "\n\n" + "\n\n".join(apercu)

    note = sauvegarder_avant_masse()
    delai = max(0, delai_ms) / 1000.0
    for num, nom, lignes in macros:
        for c in _commandes_macro(num, nom, lignes):
            ma3.send(c)
            if delai:
                time.sleep(delai)
    return f"{note}\n" + tr(f"Succès : {total} macros envoyées, numéros {premier} à {dernier}.", f"Done: {total} macros sent, numbers {premier} to {dernier}.")


def nettoyer_macros_existantes(start_macro: int, end_macro: int) -> str:
    nettoyees = 0
    for num in range(start_macro, end_macro + 1):
        key = str(num)
        if key not in INDEX_OBJETS.get("macros", {}):
            continue
        nom = INDEX_OBJETS["macros"][key]
        
        chemin = _exporter_objet("macros", str(num))
        if not chemin or not os.path.exists(chemin):
            continue
            
        try:
            with open(chemin, encoding="utf-8", errors="ignore") as f:
                contenu = f.read()
                
            matchs = re.findall(r'(?:Command|command)="([^"]*)"', contenu)
            lignes_valides = [m for m in matchs if m.strip()]
            
            if lignes_valides:
                create_macro(num, nom, lignes_valides)
                nettoyees += 1
        except Exception as e:
            print(f"Erreur nettoyage macro {num} : {e}")
            
    return tr(f"Succès : {nettoyees} macros nettoyées.", f"Done: {nettoyees} macros cleaned.")