## Nouveautés de la 1.5.3 / What's new in 1.5.3

- **Messages d'erreur plus clairs** (français et anglais) : pas de connexion Internet, délai dépassé, crédit Anthropic
  épuisé, API surchargée, clé sans droit sur le modèle.
- **Console éteinte ou mauvais port OSC** : le message indique quoi vérifier (console allumée, plugin AI_Index, adresse
  et port dans les Réglages).

*English summary:* clearer, translated error messages for no network, timeouts, exhausted credit, overloaded API, and
a console that does not answer (what to check: console on, AI_Index plugin, OSC address and port).

---

## Nouveautés de la 1.5.2 / What's new in 1.5.2

- **Interface épurée** : palette graphite avec un seul accent doré, plus de dégradés, de bulles ni d'avatar ;
  les réponses de l'IA sont du texte simple dans une colonne centrée. Thème clair adapté.
- **Nouveau logo** (graphite et doré), écran de chargement et barre de titre assortis.
- Captures d'écran du README mises à jour.

*English summary:* cleaner, simpler interface (graphite palette, single gold accent, no gradients or chat bubbles),
new logo, matching loading screen and title bar.

---

## Nouveautés de la 1.5.1 / What's new in 1.5.1

- **Écran de chargement** : la fenêtre s'ouvre tout de suite avec un indicateur « MA3-IA démarre… » au lieu de rester
  invisible pendant le démarrage.
- **Numéro de version** affiché dans l'en-tête de l'app (pastille `v1.5.1`).

*English summary:* a loading screen appears immediately at launch, and the installed version number is shown in the header.

---

## Nouveautés de la 1.5.0 / What's new in 1.5.0

**🍎 MA3-IA sur Mac / MA3-IA on Mac**
- MA3-IA fonctionne maintenant sur **macOS** (Mac Apple Silicon) avec grandMA3 onPC pour Mac : télécharge le `.dmg`,
  glisse l'app dans Applications, c'est prêt.
- Sur Mac : bibliothèque `~/MALightingTechnology/gma3_library` détectée par défaut, clé API rangée dans le **Trousseau**,
  langue de l'interface suivant celle de macOS, barre de titre claire ou sombre selon le thème.

**Installation / Install**
- Depuis le code source sur Mac : un double-clic sur `scripts/run.command` suffit, même sans Python installé
  (un Python 3.12 privé est téléchargé dans le dossier du projet, sans droits administrateur).

*English summary:* MA3-IA now runs on **macOS** (Apple Silicon) with grandMA3 onPC for Mac: download the `.dmg` and drag
the app into Applications. The `gma3_library` folder is detected automatically, the API key is stored in the Keychain,
and the interface follows the macOS language. From source, `scripts/run.command` sets everything up, even without Python.

---

## Installation / Install

### Windows
1. Télécharge / Download **`MA3-IA-Setup-x.y.z.exe`** ci-dessous / below.
2. Lance-le / Run it. Aucun droit administrateur requis / No admin rights needed.

**« Windows a protégé votre ordinateur » / "Windows protected your PC"**
L'installateur n'est pas encore signé numériquement : Windows SmartScreen affiche cet avertissement pour tout
nouveau logiciel non signé. Clique sur **Informations complémentaires → Exécuter quand même**.

The installer is not code-signed yet, so SmartScreen warns about any new unsigned program.
Click **More info → Run anyway**.

### macOS (Apple Silicon : M1, M2, M3, M4…)
1. Télécharge / Download **`MA3-IA-x.y.z.dmg`** ci-dessous / below.
2. Ouvre-le et glisse **MA3-IA** dans **Applications** / Open it and drag **MA3-IA** into **Applications**.

**« MA3-IA ne peut pas être ouvert » / "MA3-IA can't be opened"**
L'app n'est pas encore notarisée par Apple. Au premier lancement : clic droit sur MA3-IA → **Ouvrir** → **Ouvrir**.
Si macOS refuse encore : **Réglages Système → Confidentialité et sécurité → Ouvrir quand même**, ou dans le Terminal :
`xattr -dr com.apple.quarantine /Applications/MA3-IA.app`

The app is not notarized by Apple yet. On first launch: right-click MA3-IA → **Open** → **Open**.
If macOS still refuses: **System Settings → Privacy & Security → Open Anyway**, or run the command above in Terminal.

Si la console est sur une autre machine, accepte la demande d'accès au **réseau local** (OSC).
If the console runs on another machine, allow **local network** access (OSC).

### Vérifier le fichier / Verify the file
- Ces fichiers sont construits automatiquement par GitHub Actions à partir du code de ce dépôt (voir l'onglet *Actions*).
  These files are built automatically by GitHub Actions from this repository's source code (see the *Actions* tab).
- Empreintes / Checksums : `SHA256SUMS.txt` (Windows), `SHA256SUMS-macos.txt` (macOS).
  Windows : `Get-FileHash .\MA3-IA-Setup-x.y.z.exe -Algorithm SHA256` — macOS : `shasum -a 256 MA3-IA-x.y.z.dmg`

---
Projet indépendant, non affilié à MA Lighting. / Independent project, not affiliated with MA Lighting.
