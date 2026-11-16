## Nouveautés de la 1.4.0 / What's new in 1.4.0

**Macros**
- Création de macros par **import XML** : les lignes peuvent contenir des guillemets (`Lua "…"`) sans être cassées ni vides.
- Génération en masse testée jusqu'à 200 macros d'un coup ; refuse d'écraser des macros existantes (sauf demande) et exige un aperçu au-delà de 50.
- Première ligne de macro correctement créée (`Insert` avant chaque ligne).
- Outil `generate_fx_grid` retiré (syntaxe non vérifiée, doublon de la génération de macros).

**Interface / Interface**
- Les actions s'affichent **au fil de l'eau** pendant que l'IA travaille, avec un bouton **⏹ Stop**.
- L'historique du chat garde un résumé des actions de chaque tour.

**Sécurité / Safety**
- Sauvegarde automatique du show aussi avant `Delete` avec `+` ou `*`, et avant `Store /Overwrite`.

**IA / AI**
- Aide-mémoire : `Select` pour sélectionner une séquence, une page ou un exécuteur (manuel 2.5).

*English summary:* macros are now created through XML import (quotes such as `Lua "…"` no longer break lines; tested up to 200 macros in one go, overwrite protection, preview required above 50); live action stream with a Stop button; chat history keeps an action summary; auto backup extended to `Delete` with `+`/`*` and `Store /Overwrite`; `Select` hint added; `generate_fx_grid` removed.

---

## Installation / Install

1. Télécharge / Download **`MA3-IA-Setup-x.y.z.exe`** ci-dessous / below.
2. Lance-le / Run it. Aucun droit administrateur requis / No admin rights needed.

### « Windows a protégé votre ordinateur » / "Windows protected your PC"
L'installateur n'est pas encore signé numériquement : Windows SmartScreen affiche cet avertissement pour tout
nouveau logiciel non signé. Clique sur **Informations complémentaires → Exécuter quand même**.

The installer is not code-signed yet, so SmartScreen warns about any new unsigned program.
Click **More info → Run anyway**.

### Vérifier le fichier / Verify the file
- Ce fichier est construit automatiquement par GitHub Actions à partir du code de ce dépôt (voir l'onglet *Actions*).
  This file is built automatically by GitHub Actions from this repository's source code (see the *Actions* tab).
- Empreinte / Checksum : voir `SHA256SUMS.txt`. Sous Windows / On Windows :
  `Get-FileHash .\MA3-IA-Setup-x.y.z.exe -Algorithm SHA256`

---
Projet indépendant, non affilié à MA Lighting. / Independent project, not affiliated with MA Lighting.
