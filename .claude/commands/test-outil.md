---
description: Écrire et lancer des tests pytest pour un outil de tools.py, sans console grandMA3
argument-hint: <nom_de_la_fonction>
---
Écris des tests pytest pour la fonction `$ARGUMENTS` de `tools.py`, dans `tests/test_$ARGUMENTS.py`.

- Remplace `tools.ma3` par un faux client (fixture `monkeypatch`) dont `send(cmd)` ajoute `cmd` à une liste et renvoie "envoyé".
- Si la fonction lit des fichiers de la bibliothèque MA3, redirige `tools.DOSSIERS_TEMP_MA3` et le chemin d'index vers `tmp_path`, avec un faux `ai_index.json` / faux XML.
- Vérifie les commandes grandMA3 exactes envoyées, les cas d'erreur (renvoient une chaîne "Erreur..."), et l'absence de guillemets doubles imbriqués.
- Crée `tests/conftest.py` si besoin. Lance `venv/Scripts/python.exe -m pytest -q tests` et corrige les tests (pas le code) sauf si tu trouves un vrai bug : dans ce cas, explique-le et demande avant de modifier `tools.py`.
