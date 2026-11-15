---
description: Relire le code ou un diff sous l'angle grandMA3 (syntaxe, sécurité, OSC)
argument-hint: [fichier ou vide pour le diff courant]
---
Fais une revue pour ce projet grandMA3 de : $ARGUMENTS (si vide, revois le résultat de `git diff`). Vérifie :
- syntaxe des commandes grandMA3 envoyées (mots-clés, guillemets, options comme /noconfirm, /Path) ;
- actions destructrices (Delete, Store qui écrase) sans dry_run ni confirmation ;
- code qui suppose un retour de la console alors qu'OSC n'en donne aucun ;
- cohérence TOOLS / FUNCS / prompt système ;
- clés API ou secrets dans le code ;
- Lua : accès non protégés par pcall, API MA3 inventée.
Liste les problèmes par gravité, avec fichier:ligne et correction proposée. Ne modifie rien.
