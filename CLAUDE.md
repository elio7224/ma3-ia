# ma3-ia-V2 — Assistant IA pour grandMA3

Agent IA (API Anthropic + outils) qui pilote une console **grandMA3 onPC** (Windows) : lit le showfile
(index JSON + exports XML) et envoie des commandes par **OSC**. Le développeur parle français :
réponds, commente et nomme en **français**, explications courtes et simples.

## Lancer / tester
- App de bureau : `run.bat` (installe le venv la 1re fois, puis lance `pythonw desktop.py`) ou raccourci Bureau `MA3-IA`.
- Version navigateur : `run_web.bat` → http://127.0.0.1:8000.
- Python : `venv/Scripts/python.exe` (3.12). Tests : `venv/Scripts/python.exe -m pytest -q tests`.
- Après une modif Python : au minimum `venv/Scripts/python.exe -m py_compile <fichier>`.
- `.exe` : `construire_exe.bat` (PyInstaller → `dist/MA3-IA/`).

## Fichiers (lire seulement ce qui est utile à la tâche)
| Fichier | Rôle |
|---|---|
| `app.py` | FastAPI : `/api/chat` (boucle outils), `/api/sync` (rescan), `/api/status`, `/api/history`, `/api/reglages*`. |
| `outils.py` | Définitions `TOOLS` + `FUNCS` (partagées par `app.py` et `agent.py`). |
| `tools.py` | Implémentation des outils : index, export XML, macros, MAtricks, génération en masse. |
| `reglages.py` | Réglages (`%APPDATA%\ma3-ia\settings.json`), clé API (coffre Windows / keyring), tests OSC/plugin. |
| `desktop.py` | Fenêtre pywebview (WebView2) + serveur local sur port libre, barre de titre DWM, icône. |
| `config.py` | Modèles, prix, prompt système, calcul du coût. |
| `ma3.py` | Client OSC minimal (`/cmd`), sans retour. |
| `index.html` | Interface (chat, réglages, assistant de 1er lancement). ~30 Ko : utiliser Grep, pas Read entier. |
| `ai_index.lua` | Plugin console : écrit `gma3_library/ai_index.json`. |
| `agent.py` | Version CLI. `nettoyer_macros.py` : script autonome. `generer_icone.py` : génère `ma3ia.ico`. |

À ne pas lire : `memoire_chat.json` (historique, énorme), `venv/`, `build/`, `dist/`, `*.ico`, `__pycache__/`.

## Flux de données
1. `preparer_et_exporter_show()` vide les dossiers `Temp` puis envoie `Plugin "AI_Index" "<chemin>"` par OSC.
2. Le plugin écrit `C:\ProgramData\MALightingTechnology\gma3_library\ai_index.json`.
3. `charger_contexte_temp()` en fait le texte d'index injecté dans le prompt système.
4. `lire_xml_temp("macros/2002")` exporte puis attend le XML dans `gma3_library/datapools/macros/Temp/` (polling).

## Règles grandMA3
- **OSC à sens unique** : jamais de confirmation possible ; seul retour = fichiers (XML, JSON du plugin).
  Ne jamais prétendre avoir vérifié dans la console.
- Pas de guillemets doubles imbriqués dans les lignes de macro envoyées par OSC (utiliser des simples).
- Presets = `type.numéro` (ex `4.12`) ; les apparences sont dans ShowData, hors DataPool.
- Lua MA3 : `Printf`, `ErrPrintf`, `DataPool()`, `Root()`, `obj:Children()`, `obj.name`/`obj.no`, toujours sous `pcall`.
  En cas de doute : `docs/ma3/` ou **demander**, ne pas inventer.

## Conventions
- Noms en français (`lire_xml_temp`, `INDEX_OBJETS`). Lire l'index via `tools.INDEX_OBJETS` (réassigné au rescan).
- Un outil = fonction dans `tools.py` + entrée dans `outils.py`. Retourne toujours une **chaîne** ; erreurs → `"Erreur : ..."`.
- Actions de masse : `dry_run` + limite (`MAX_MACROS_PAR_APPEL`).
- Console Windows en cp1252 : stdout est reconfiguré en UTF-8 dans `app.py` (emojis dans les `print`).

## Sécurité
- Ne jamais lire, afficher ni committer `cle_api.txt`, `.env*` ou une clé `sk-ant-...`. Pas de clé en dur.

## Façon de travailler
- Petites étapes ; plan avant un changement multi-fichiers. Pas de `git push` sans demande explicite.
