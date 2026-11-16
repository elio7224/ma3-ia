# Aide-mémoire grandMA3 (ligne de commande, vérifié avec le manuel 2.5)

## Structure d'une commande
`[Fonction] [Objet] [Numéro] [Options]` — ex : `Store Group 5 /Overwrite`.
Sans fonction, un **groupe ou une fixture** est sélectionné (`Group 3`, `Fixture 5`) ; `At` applique une valeur.
**Sélectionner un autre objet** (séquence, exécuteur, page, monde, datapool…) : mot-clé `Select` (raccourci `Sel`) — `Select Sequence 2`, `Select Executor 105`, `Select Page 2`. Écrire seulement `Sequence 2` ou `Page 2` ne sélectionne pas : il faut `Select`.
- Plages : `Thru` (`Fixture 101 Thru 110`), ajout `+`, retrait `-` (`Group 1 + Group 2 - Fixture 105`).
- Sous-fixtures : `Fixture 101.1`. Presets : `Preset <pool>.<numéro>` (ex `Preset 4.12`).
- Cues : `Cue 5 Sequence 3`. Exécuteurs : `Page 1.201` (page 1, exécuteur 201). Lignes de macro : `Macro 3.2`.
- Noms entre guillemets : `Group "Front"`. Dans une ligne de macro envoyée par OSC : préfère TOUJOURS les guillemets simples à l'intérieur ; des guillemets doubles ne sont à utiliser que si la ligne l'exige vraiment (ils ne sont plus bloqués, mais peuvent casser la commande).

## Pools de presets
1 Dimmer · 2 Position · 3 Gobo · 4 Color · 5 Beam · 6 Focus · 7 Control · 8 Shapers · 9 Video · 21–25 All 1 à All 5.
Préfixes vus dans les exports : `g` = global, `s` = sélectif, `u` = universel (ex `AbsPreset=gColor.10`).

## Fonctions courantes
| But | Exemple |
|---|---|
| Sélection + valeur | `Group 3 At 50`, `Fixture 1 Thru 10 At Full`, `Group 2 At Preset 4.3` |
| Sélectionner séquence / page / exécuteur | `Select Sequence 2`, `Select Page 2`, `Select Executor 105` (la séquence sélectionnée est la cible de `Store Cue 4`) |
| Attribut précis | `Attribute "Pan" At 20` |
| Enregistrer | `Store Cue 5 Sequence 3`, `Store Preset 4.12`, `Store Group 7` |
| Options de Store | `/Merge`, `/Overwrite`, `/Remove`, `/NoConfirmation` |
| Nommer | `Label Group 7 "Face"`, `Label Cue 5 Sequence 3 "Refrain"` |
| Assigner | `Assign Sequence 3 At Page 1.201`, `Assign Appearance 26 At Macro 2002` |
| Copier / déplacer | `Copy Group 1 At 10`, `Move Macro 5 At 20` |
| Supprimer | `Delete Group 3 /NoConfirmation` (destructif) |
| Propriété | `Set Macro 3.1 Property "Command" "ClearAll"`, `Set MAtricks 2 Property "XGroup" 2` |
| Lecture | `Go+ Sequence 3`, `Go- Sequence 3`, `Goto Cue 5 Sequence 3`, `Off Sequence 3`, `Top Sequence 3` |
| Macro / plugin | `Go+ Macro 12`, `Plugin "AI_Index"`, ligne `Lua "Cmd('Go+ Macro 3')"` |
| Programmer | `ClearSelection`, `ClearActive`, `ClearAll` (vide le programmer) |
| Sécurité | `Blind` (travailler hors scène), `Highlight` |

## Notions
- **Tracking** : une cue ne contient que ce qui change ; les valeurs précédentes continuent (sauf cue de type Release / `Off`).
- **Programmer** : valeurs en cours d'édition ; `Store` les enregistre, `ClearAll` les efface.
- **Phaser** : effet = suite de steps sur un attribut, stocké dans un preset ou une cue (pas de pool d'effets séparé).
- **MAtricks** : ordre/regroupement de la sélection (`XGroup`, `XBlock`, `XWings`, `Interleave`) pour décaler phasers et fades.
- **Apparences** : couleurs/images des boutons de pool, dans ShowData (hors DataPool), assignées par `Assign Appearance`.
- **Macro** : lignes exécutées dans l'ordre ; propriété `Wait` = secondes ou `Go` (attend un Go).

## Sauvegarde automatique (faite par l'app)
- Avant une action de masse (generate_macros_from_template, run_command avec Delete/Store/Copy/Move … Thru …),
  l'app envoie `SaveShow` (réglable). grandMA3 crée alors une copie datée dans **Backup Shows** (10 max par show).
- Pour revenir en arrière : Menu → Backup → Load → Backup Shows → choisir la copie d'avant l'action.
- Si le résultat d'un outil indique la sauvegarde, dis-le en une phrase à l'utilisateur.

## Format compact renvoyé par lire_xml_temp
- Une ligne par élément, indentée : `Cue Name=Refrain No=5` → `Part` → `PresetData` → phasers.
- `[ID 401-412] Phaser Attribute=Dimmer AbsPreset=uDimmer.70 Fade=1.50 -> Step Absolute=*70` :
  les fixtures 401 à 412 ont exactement cette valeur. `301.1.1-8` = sous-fixtures 1 à 8 de 301.1.
- `Dépendances : PresetPools.Color.10` : presets utilisés, lisibles à part avec `presets/4.10`.

## En cas de doute
Syntaxe générale : `[Fonction] [Objet] ["Nom" ou Numéro] (/Option)` (manuel 2.5, vérifié).
Pour tout autre mot-clé ou option : outil `doc_grandma3` (page officielle du manuel). Sinon, dis-le et
conseille de tester en `Blind` ou sur un objet de test avant le spectacle.
