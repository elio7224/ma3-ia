---
description: Créer ou modifier un plugin Lua grandMA3
argument-hint: <ce que le plugin doit faire>
---
Plugin Lua grandMA3 à écrire ou modifier : $ARGUMENTS

Contraintes :
- Structure `return function(display_handle, argument) ... end` comme `ai_index.lua`.
- N'utilise que des fonctions de l'API MA3 déjà présentes dans le projet ou dans `docs/` ; si tu as besoin d'une autre fonction, dis-le et demande-moi de vérifier dans le manuel plutôt que d'inventer.
- Protège chaque accès objet par `pcall`, logue avec `Printf` / `ErrPrintf` préfixés du nom du plugin.
- Si le plugin doit renvoyer des données à Python, écris un fichier JSON dans `gma3_library` (OSC n'a pas de retour).
- Termine par la procédure de test : import du plugin dans onPC, commande à taper, sortie attendue dans la ligne de commande.
