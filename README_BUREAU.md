# Application de bureau MA3-IA

Fenêtre native Windows (pywebview / WebView2) qui réutilise l'interface web existante. Un serveur FastAPI local démarre
en arrière-plan sur un port libre ; rien n'est exposé hors de 127.0.0.1.

## Lancer
- **Double-clic sur le raccourci `MA3-IA` du Bureau** : ouvre l'app sans fenêtre noire (créé par `run.bat` à la première installation, ou par `creer_raccourci.bat`).
- **`run.bat`** : la première fois, crée le venv et installe les dépendances (fenêtre noire le temps de l'installation) ; ensuite il ouvre juste l'app.
- Ou : `venv\Scripts\python.exe desktop.py`.
- L'ancienne version navigateur reste disponible : `run_web.bat` (http://127.0.0.1:8000).

## Premier lancement
Un assistant guide en 3 étapes : clé API → connexion console (IP / port OSC) → plugin `AI_Index`.
Il se relance depuis **⚙ Réglages → Relancer l'assistant**.

## Où sont rangées les données
| Donnée | Emplacement |
|---|---|
| Clé API | Coffre Windows (Credential Manager, service `ma3-ia`). Repli : variable `ANTHROPIC_API_KEY`, puis ancien `cle_api.txt`. Jamais dans `settings.json`. |
| Réglages (modèle, OSC, dossier `gma3_library`, thème, tours d'outils) | `%APPDATA%\ma3-ia\settings.json` |
| Historique du chat (mode bureau) | `%APPDATA%\ma3-ia\memoire_chat.json` |

La variable `MA3IA_CONFIG_DIR` change le dossier de config (utile pour les tests).

## Créer le .exe
Double-clic sur `construire_exe.bat` (ou : `pyinstaller --noconfirm --windowed --name MA3-IA --add-data "index.html;." --add-data "ai_index.lua;." --collect-submodules keyring.backends desktop.py`).
Résultat : `dist\MA3-IA\MA3-IA.exe` ; copier tout le dossier `dist\MA3-IA` pour le déplacer. Prérequis sur le PC cible : Microsoft Edge WebView2 (présent par défaut sous Windows 11).

## Tests
`venv\Scripts\python.exe -m pytest -q`

## Limites connues
- OSC est à sens unique : « Tester la connexion » envoie `Echo 'ma3-ia : test de connexion'` ; seule la console peut montrer qu'il est arrivé (syntaxe `Echo` non vérifiée sur onPC).
- L'import du plugin `ai_index.lua` dans la console reste manuel (instructions dans l'assistant).
