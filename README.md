# MA3-IA — grandMA3 AI Control

Assistant IA (Claude, API Anthropic) qui pilote une console **grandMA3 onPC** sous Windows :
il lit ton showfile (index + exports XML) et envoie des commandes à la console par **OSC**.

> Projet indépendant, non affilié à MA Lighting. grandMA3 est une marque de MA Lighting Technology GmbH.

## Ce qu'il sait faire
- Répondre à des questions sur ton show (macros, séquences, presets, groupes, MAtricks, apparences).
- Créer et modifier des objets : macros (y compris en masse), MAtricks, grilles d'effets, commandes libres.
- Consulter le manuel officiel grandMA3 quand il doute d'une syntaxe.

## Prérequis
- Windows 10/11, Python 3.12, grandMA3 onPC.
- Une clé API Anthropic (https://console.anthropic.com).
- Dans la console : OSC entrant activé (UDP, adresse `/cmd`) et le plugin Lua `ai_index.lua` importé.

## Installation
1. Télécharge le projet puis double-clique sur `run.bat` (crée l'environnement Python, installe tout,
   crée un raccourci `MA3-IA` sur le Bureau).
2. Au premier lancement, un assistant demande la clé API, l'adresse OSC de la console et vérifie le plugin.

Détails (données, création du `.exe`, tests) : voir [README_BUREAU.md](README_BUREAU.md).

## Sécurité
- La clé API est rangée dans le coffre Windows (Credential Manager), jamais dans un fichier du projet.
- OSC est à sens unique : l'IA envoie les commandes mais ne peut pas confirmer qu'elles ont réussi.
  Teste d'abord sur une copie de ton show.
