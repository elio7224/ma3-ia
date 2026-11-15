# MA3-IA — grandMA3 AI Control

🇬🇧 [English version](README.en.md)

Assistant IA (Claude, API Anthropic) qui pilote une console **grandMA3 onPC** sous Windows :
il lit ton showfile (index + exports XML) et envoie des commandes à la console par **OSC**.

> ⚠️ **Projet indépendant, non affilié à MA Lighting Technology GmbH**, ni approuvé ou soutenu par elle.
> Voir [Mentions](#mentions).

## Ce qu'il sait faire
- Répondre à des questions sur ton show (macros, séquences, presets, groupes, MAtricks, apparences).
- Créer et modifier des objets : macros (y compris en masse), MAtricks, grilles d'effets, commandes libres.
- Consulter le manuel officiel grandMA3 quand il doute d'une syntaxe.
- **Journal des commandes** : tout ce qui a été envoyé à la console, avec l'heure et l'outil de l'IA qui l'a envoyé.
- **Garde-fou de coût** : plafond de dépense par session, alerte à 80 %, blocage au plafond.
- **Interface en français et en anglais** (automatique selon Windows, modifiable dans les Réglages).

## Prérequis
- Windows 10/11 (64 bits), grandMA3 onPC. Python 3.12 seulement pour la version « code source ».
- Une clé API Anthropic (https://console.anthropic.com).
- Dans la console : OSC entrant activé (UDP, adresse `/cmd`) et le plugin Lua `ai_index.lua` importé.

## Installation
**Le plus simple : l'installateur** (aucun Python à installer)
1. Télécharge `MA3-IA-Setup-x.y.z.exe` dans les [Releases](https://github.com/elio7224/ma3-ia/releases).
2. Lance-le : il s'installe pour ton compte Windows, sans droits administrateur, avec raccourcis et désinstallation.
3. Au premier lancement, un assistant demande la clé API, l'adresse OSC de la console et vérifie le plugin.

> **« Windows a protégé votre ordinateur » ?** L'installateur n'est pas encore signé numériquement, et Windows
> SmartScreen avertit pour tout nouveau logiciel non signé. Clique sur **Informations complémentaires → Exécuter quand même**.
> Pour vérifier le fichier : il est construit par GitHub Actions directement depuis ce code (onglet *Actions*),
> et son empreinte SHA-256 est publiée avec la Release (`Get-FileHash .\MA3-IA-Setup-x.y.z.exe`).

**Depuis le code source** : télécharge le projet puis double-clique sur `run.bat` (crée l'environnement Python,
installe tout, crée un raccourci `MA3-IA` sur le Bureau).

Détails (données, création du `.exe`, tests) : voir [README_BUREAU.md](README_BUREAU.md).

## Sécurité
- La clé API est rangée dans le coffre Windows (Credential Manager), jamais dans un fichier du projet.
- OSC est à sens unique : l'IA envoie les commandes mais ne peut pas confirmer qu'elles ont réussi.
  Teste d'abord sur une copie de ton show.
- Ton historique de chat, tes réglages et le journal restent sur ton PC (dossier de configuration de l'app),
  jamais dans le dossier du projet.

## Licence
Code sous licence [MIT](LICENSE) : libre d'utilisation, de modification et de redistribution, en gardant la mention de copyright.

## Mentions
- Ce projet est **indépendant** : il n'est ni affilié à **MA Lighting Technology GmbH**, ni approuvé, sponsorisé ou soutenu par elle.
- « grandMA3 » et « MA Lighting » sont des marques de MA Lighting Technology GmbH, citées uniquement pour indiquer
  avec quel matériel l'application fonctionne.
- Le manuel grandMA3 n'est pas inclus : l'outil `doc_grandma3` télécharge à la demande les pages publiques
  de help.malighting.com, pour un usage local.
- L'application est fournie sans garantie (voir la licence). Teste toujours sur une copie de ton show avant un spectacle.

