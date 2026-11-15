---
description: Ajouter un nouvel outil à l'agent grandMA3 (tools.py + TOOLS/FUNCS)
argument-hint: <description de l'outil>
---
Ajoute un nouvel outil à l'agent : $ARGUMENTS

Étapes :
1. Propose d'abord la signature, les commandes grandMA3 qui seront envoyées et le schéma JSON, puis attends ma validation.
2. Implémente la fonction dans `tools.py` (noms en français, renvoie toujours une chaîne, `dry_run` si action de masse, pas de guillemets doubles dans les commandes OSC imbriquées).
3. Ajoute l'entrée dans `TOOLS` et `FUNCS` (app.py, et outils.py s'il existe), avec une description claire pour le modèle.
4. Si utile, mets à jour le prompt système (règles d'usage de l'outil).
5. Vérifie avec `py_compile` et écris un test avec le faux client OSC (voir /test-outil).
6. Rappelle-moi ce que je dois tester à la main sur grandMA3 onPC.
