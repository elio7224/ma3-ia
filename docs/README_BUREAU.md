# MA3-IA — documentation technique

Fenêtre native (pywebview : WebView2 sous Windows, WebKit sous macOS) qui affiche l'interface web. Un serveur FastAPI local démarre
en arrière-plan sur un port libre ; rien n'est exposé hors de 127.0.0.1.

## Organisation du dépôt
| Dossier | Contenu |
|---|---|
| `ma3ia/` | Tout le code Python : `app.py` (serveur), `desktop.py` (fenêtre), `tools.py` / `outils.py` (outils de l'IA), `reglages.py`, `config.py` (prompt), `i18n.py`, `journal.py`, `doc_ma3.py`, `version.py`, `agent.py` (version terminal) |
| `ma3ia/web/` | Interface (`index.html`) |
| `ma3ia/assets/` | Icône de l'application |
| `plugin/` | `ai_index.lua`, le plugin à importer dans la console |
| `scripts/` | Windows : `run.bat`, `run_web.bat`, `construire_exe.bat`, `creer_raccourci.bat` ; macOS : `run.command`, `construire_app.sh` ; `generer_icone.py`, `nettoyer_macros.py` |
| `installeur/` | Script Inno Setup, fiche de version, notes de Release |
| `docs/` | Cette doc, le README anglais, les captures d'écran |
| `tests/` | Tests pytest (sans console ni vraie API) |

Les modules de `ma3ia/` s'importent par leur nom (`import tools`) : lancer les scripts depuis `ma3ia/`
(`python ma3ia/desktop.py`) suffit, et `tests/conftest.py` ajoute ce dossier au chemin de Python.

## Lancer
- **Raccourci `MA3-IA` du Bureau** : ouvre l'app sans fenêtre noire (créé par `scripts\run.bat` à la première
  installation, ou par `scripts\creer_raccourci.bat`).
- **`scripts\run.bat`** : la première fois, crée le venv et installe les dépendances ; ensuite il ouvre juste l'app.
- Ou : `venv\Scripts\python.exe ma3ia\desktop.py`.
- Version navigateur : `scripts\run_web.bat` (http://127.0.0.1:8000).
- **macOS** : double-clic sur `scripts/run.command`. Il utilise un Python 3.10+ déjà installé (python.org, Homebrew) ;
  sinon il télécharge `uv` et un Python 3.12 privé dans `.outils/` (ignoré par git, supprimé avec le projet).
  Ou : `venv/bin/python ma3ia/desktop.py` ; navigateur : `venv/bin/python ma3ia/app.py`.

## Premier lancement
Un assistant guide en 3 étapes : clé API → connexion console (IP / port OSC) → plugin `AI_Index`.
Il se relance depuis **⚙ Réglages → Relancer l'assistant**.

## Où sont rangées les données
| Donnée | Emplacement |
|---|---|
| Clé API | Coffre du système via `keyring`, service `ma3-ia` (Windows : Credential Manager ; macOS : Trousseau). Repli : variable `ANTHROPIC_API_KEY`, puis ancien `cle_api.txt` à la racine. Jamais dans `settings.json`. |
| Réglages (modèle, OSC, dossier `gma3_library`, thème, langue, plafond, sauvegarde auto) | `<config>/settings.json` |
| Historique du chat (mode bureau) | `<config>/memoire_chat.json` |
| Journal des commandes envoyées | `<config>/journal_actions.jsonl` |
| Pages du manuel consultées par l'IA (cache) | `<config>/doc_ma3/` |

`<config>` = `%APPDATA%\ma3-ia` sous Windows, `~/Library/Application Support/ma3-ia` sous macOS.
Bibliothèque `gma3_library` par défaut : `C:\ProgramData\MALightingTechnology\gma3_library` sous Windows,
`~/MALightingTechnology/gma3_library` sous macOS (commune à toutes les versions de grandMA3 onPC installées).

La variable `MA3IA_CONFIG_DIR` change le dossier de config (utile pour les tests). Avec le Python du Microsoft Store,
Windows redirige `%APPDATA%` vers `%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.12_…\LocalCache\Roaming`.

## Créer l'installateur
- Sur ton PC : double-clic sur `scripts\construire_exe.bat` (Inno Setup requis : `winget install JRSoftware.InnoSetup`).
  Résultat : `dist\MA3-IA\MA3-IA.exe` (application) et `dist\MA3-IA-Setup-<version>.exe` (installateur).
- Pour publier une version, **sans commande** : mettre à jour `installeur/notes_release.md` (modifiable sur github.com),
  puis onglet **Actions → Publier une version → Run workflow**, taper le numéro (ex : `1.5.0`). Le workflow
  `publier.yml` met `ma3ia/version.py` à jour, crée le commit et le tag, puis lance `release.yml`.
  À la main, c'est équivalent : changer `VERSION` dans `ma3ia/version.py`, committer, puis
  `git tag v<version>` et `git push origin v<version>`. GitHub Actions (`.github/workflows/release.yml`) lance les tests,
  construit l'installateur et crée la Release avec son empreinte SHA-256 et une attestation de provenance.
- Choix anti-« faux virus » : PyInstaller en mode dossier (pas d'exe unique), sans compression UPX, fiche de version
  remplie (`installeur/generer_version.py`), installation sans droits administrateur, construction publique par GitHub.
- Prérequis sur le PC cible : Windows 10/11 64 bits avec Microsoft Edge WebView2 (présent par défaut sous Windows 11).

### macOS
- Sur un Mac : `./scripts/construire_app.sh`. Résultat : `dist/MA3-IA.app` et `dist/MA3-IA-<version>.dmg`
  (glisser l'app dans Applications). L'icône `ma3ia/assets/ma3ia.icns` est générée par
  `python scripts/generer_icone.py ma3ia/assets/ma3ia.icns` (à refaire seulement si l'icône change).
- L'app est construite pour l'architecture du Mac qui la construit (Apple Silicon sur GitHub Actions).
- Signature ad hoc seulement (pas de compte Apple Developer) : au premier lancement, clic droit → Ouvrir.
  L'`Info.plist` contient `NSLocalNetworkUsageDescription` : macOS demande l'accès au réseau local pour l'OSC
  vers une console distante.
- La Release GitHub (`release.yml`) construit aussi le `.dmg` sur macOS et l'ajoute à la Release avec
  `SHA256SUMS-macos.txt`. Le workflow `tests.yml` lance les tests sous Windows et macOS à chaque push.

## Manuel grandMA3
Le manuel n'est pas inclus dans le dépôt. `ma3ia/memo_grandma3.md` est un aide-mémoire rédigé pour ce projet
(syntaxe de base, vérifiée avec le manuel 2.5) ; l'outil `doc_grandma3` télécharge à la demande la page publique
d'un mot-clé sur help.malighting.com et la garde en cache sur le PC de l'utilisateur.

## Tests
`venv\Scripts\python.exe -m pytest -q`

## Limites connues
- OSC est à sens unique : « Tester la connexion » envoie `Echo 'ma3-ia : test de connexion'` ; seule la console peut montrer qu'il est arrivé.
- Installation du plugin (`ma3ia/plugin_ma3.py`) : confirmée seulement par l'index produit ensuite (OSC sans retour).
  Version du plugin : `VERSION_PLUGIN` dans `plugin/ai_index.lua` = `VERSION_ATTENDUE` dans `ma3ia/plugin_ma3.py`
  (à augmenter ensemble à chaque modification du plugin ; un test le vérifie).
- Les résultats bruts des outils (panneau « Actions ») restent en français : ils sont destinés à l'IA.
- Création de macros : l'app écrit un XML par macro (`ma3ia_tmp_<n>_<ms>.xml`, sans Guid) dans
  `gma3_library\datapools\macros\`, puis envoie `Import Macro <n> "<fichier>" /Overwrite`. Les guillemets des lignes sont
  donc protégés par le XML (`&quot;`). Les fichiers temporaires de plus d'une heure sont supprimés au prochain appel
  (pas tout de suite : en mode validation l'import part plus tard). OSC étant à sens unique, « Succès » veut dire
  « commandes envoyées », pas « macros vérifiées ». Testé sur la console jusqu'à 200 macros en une génération.
