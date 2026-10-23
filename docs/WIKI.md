<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Modding wiki

> AI-generated, local to this fork. Do not upstream.

Every process documented in this fork, by task. Each row points to the guide and
the command, if there is one. Commands run from the repository root;
`mapkit` means `tools/mapkit/mapkit.sh`.

## Building

| I want to... | Guide | Command |
|---|---|---|
| build a modified ROM | [modding/README.md](modding/README.md#building-a-modified-rom) | `make release` (SoulSilver: `GAME_VERSION=SOULSILVER`) |
| check the unmodified tree still matches | [modding/README.md](modding/README.md#building-a-modified-rom) | `make` (runs the checksum tests) |
| know what is editable as text | [modding/README.md](modding/README.md#status-of-each-data-type) | |
| check my data before building | [mapkit README](../tools/mapkit/README.md#what-validate-checks) | `mapkit validate`, `mapkit format check`, `mapkit terrain check` |

## Maps

| I want to... | Guide | Command |
|---|---|---|
| find a map's files | [maps-and-warps.md](modding/maps-and-warps.md#finding-a-maps-files) | `mapkit show Cherrygrove` |
| change music, weather, map type, flags of a map | [maps-and-warps.md](modding/maps-and-warps.md#map-header-top-of-mapjson) | edit `data/maps/<Map>/map.json` |
| add or link warps | [maps-and-warps.md](modding/maps-and-warps.md#warps-warp_events) | `mapkit warp link A:0 B:0`, `mapkit warp add` |
| add signs, hidden items | [maps-and-warps.md](modding/maps-and-warps.md#signs-and-hidden-items-bg_events) | |
| add trigger zones | [maps-and-warps.md](modding/maps-and-warps.md#trigger-zones-coord_events) | |
| change a map's grid of cells | [maps-and-warps.md](modding/maps-and-warps.md#map-grid-datalayouts) | edit `data/layouts/<Layout>/layout.json` |
| paint collision and tile behaviors | [maps-and-warps.md](modding/maps-and-warps.md#terrain-datalanddata) | `tools/mapeditor/mapeditor.sh <Map>` |
| place props (buildings, trees) | [maps-and-warps.md](modding/maps-and-warps.md#terrain-datalanddata) | edit `props.json` |
| change or make 3D terrain | [terrain.md](modding/terrain.md) | `mapkit terrain export` / `import` |
| change walking heights | [terrain.md](modding/terrain.md#heights) | `mapkit heights decompile / generate / at` |
| add a new map | [maps-and-warps.md](modding/maps-and-warps.md#adding-a-new-map) | |
| use the map editor | [mapeditor README](../tools/mapeditor/README.md) | `tools/mapeditor/mapeditor.sh <Map>` |

## NPCs, scripts and text

| I want to... | Guide | Command |
|---|---|---|
| move, hide or add an NPC | [npcs-and-scripts.md](modding/npcs-and-scripts.md#adding-an-npc) | `mapkit npc move / set / add` |
| pick a movement type | [npcs-and-scripts.md](modding/npcs-and-scripts.md#movement-types) | |
| write event scripts | [SCRIPTING.md](modding/SCRIPTING.md) | edit `scripts.pory`; `mapkit pory show <Map>` |
| add a script | [npcs-and-scripts.md](modding/npcs-and-scripts.md#adding-a-script) | `mapkit script add` |
| run a script on map load | [npcs-and-scripts.md](modding/npcs-and-scripts.md#init--level-scripts-mapscripts) | |
| move NPCs in a cutscene | [npcs-and-scripts.md](modding/npcs-and-scripts.md#movement-scripts) | |
| show a multichoice or list menu from a script | [ui.md](modding/ui.md#menus-from-scripts) | `multichoiceinit` ... `multichoiceexec` |
| add or edit dialogue | [npcs-and-scripts.md](modding/npcs-and-scripts.md#text), [SCRIPTING.md](modding/SCRIPTING.md#text) | `mapkit text add` |
| find a free flag or var | [unknown-flags-vars.md](modding/unknown-flags-vars.md#free-flags) | `tools/flagusage` |
| find where a flag, var or sprite is used | [mapkit README](../tools/mapkit/README.md#commands) | `mapkit refs FLAG_X` |

## Story and gyms

| I want to... | Guide | Command |
|---|---|---|
| understand flag and var ranges (hide flags, scene vars, temp, daily) | [story-progression.md](modding/story-progression.md#how-progress-is-stored) | |
| find what blocks a route and what opens it | [story-progression.md](modding/story-progression.md#story-beats) | `mapkit refs VAR_X` |
| change the order of story events or skip one | [story-progression.md](modding/story-progression.md#changing-progression) | |
| know what unlocks after the League (`FLAG_GAME_CLEAR`) | [story-progression.md](modding/story-progression.md#elite-four-and-game-clear) | |
| change which badge an HM needs, or obedience levels | [gyms.md](modding/gyms.md#what-badges-do) | |
| change a leader's reward, entry gate or puzzle | [gyms.md](modding/gyms.md#summary) | |
| require badges for a gate | [gyms.md](modding/gyms.md#changing-gyms) | `checkbadge`, `countbadges` |

## Trainers and battles

| I want to... | Guide | Command |
|---|---|---|
| change a trainer's party | [npcs-and-scripts.md](modding/npcs-and-scripts.md#trainers) | edit `files/poketool/trainer/trainers.json` |
| change a move's power, type, effect | [moves.md](modding/moves.md#move-data-battle_movesjson) | edit `battle_moves.json` |
| add a move | [moves.md](modding/moves.md#adding-a-new-move) | |
| find move special cases in C | [moves.md](modding/moves.md#moves-named-in-c) | |
| add a trainer class (name, gender, prize money, music) | [trainer-classes.md](modding/trainer-classes.md#adding-a-class) | |
| change or add a trainer's battle sprite | [trainer-classes.md](modding/trainer-classes.md#trainer-sprites) | PNG in `graphics/trainers/front_pics/`; `trainer_pics.py check` |
| animate a trainer sprite | [trainer-classes.md](modding/trainer-classes.md#animation) | `"anims"` in `data/trainer_graphics/front_pics.json` |

## Pokémon

| I want to... | Guide | Command |
|---|---|---|
| change base stats, types, abilities, TM compatibility | [pokemon.md](modding/pokemon.md#base-stats-types-abilities-items-tmhm) | edit `personal.json` |
| change evolutions | [pokemon.md](modding/pokemon.md#evolutions) | edit `evo.json` |
| change level-up or egg moves | [pokemon.md](modding/pokemon.md#level-up-learnsets) | |
| change Pokédex entries | [pokemon.md](modding/pokemon.md#pokédex-data) | |
| replace sprites and icons | [pokemon.md](modding/pokemon.md#graphics) | PNG files |
| add a species | [pokemon.md](modding/pokemon.md#adding-a-new-species) | |
| change wild encounters | [wild-encounters.md](modding/wild-encounters.md) | `mapkit wild set` |
| change headbutt, Safari, Bug Contest, roamers | [wild-encounters.md](modding/wild-encounters.md#headbutt-trees) | |
| add an ability | [abilities.md](modding/abilities.md#adding-an-ability) | |
| find where an ability's effect is coded | [abilities.md](modding/abilities.md#where-an-ability-can-act) | `grep -rn ABILITY_X src files/battledata` |

## Items

| I want to... | Guide | Command |
|---|---|---|
| change an item's price, name, description, pocket | [items.md](modding/items.md#changing-an-item) | edit `data/items/items.json` |
| change what an item does when used or held | [items.md](modding/items.md#the-fields) | |
| add an item | [items.md](modding/items.md#adding-an-item) | `python3 tools/pokedata/items.py check data/items/items.json --include include` |
| change or add an icon | [items.md](modding/items.md#icons) | PNG in `files/itemtool/itemdata/item_icon/` |
| change what shops sell | [items.md](modding/items.md#marts) | `src/scrcmd_mart.c` |

## Game rules and save data

| I want to... | Guide | Command |
|---|---|---|
| change a hard-coded limit (level cap, IVs, egg steps) | [game-limits.md](modding/game-limits.md) | |
| know what a change costs in save space | [save-data.md](modding/save-data.md#what-common-mods-cost) | |
| understand the save layout | [save-data.md](modding/save-data.md) | |

## Code

| I want to... | Guide | Command |
|---|---|---|
| make a new screen or menu | [ui.md](modding/ui.md#adding-a-new-application), [checklist](modding/ui.md#11-checklist-for-a-new-screen) | |
| open a screen from the field | [ui.md](modding/ui.md#launching-an-application) | |
| decompile or match a function | [DECOMP-NOTES.md](DECOMP-NOTES.md) | |

## File formats (for tool writers)

| Topic | Document |
|---|---|
| the map file format (gen4map 1.1) | [gen4map/FORMAT.md](gen4map/FORMAT.md) |
| what the files become in the ROM | [gen4map/BINARY.md](gen4map/BINARY.md) |
| drawing and writing NSBMD/NSBTX | [gen4map/RENDERING.md](gen4map/RENDERING.md) |
| why the map files are laid out this way | [modding/DESIGN.md](modding/DESIGN.md), [CHANGE-0001](gen4map/CHANGE-0001-maps-as-files.md), [CHANGE-0002](gen4map/CHANGE-0002-terrain-authoring.md) |
| plans for a standalone Gen 4 tool | [gen4map/ROADMAP.md](gen4map/ROADMAP.md) |

## Ideas (not built)

| Idea | Notes |
|---|---|
| shiny colors for Pokémon icons; shiny and IVs on the naming screen | [ideas/shiny-icons.md](ideas/shiny-icons.md) |

## Not documented yet

Compared with what the pokeemerald wiki and pret tooling cover, these have no
guide here yet, in rough order of how often a hack needs them:

| Topic | State in this fork | pokeemerald equivalent |
|---|---|---|
| **Trainer battle text** | binary (`trtbl.narc`); classes and sprites are in [trainer-classes.md](modding/trainer-classes.md) | |
| **Level scaling** of trainers and wild Pokémon | levels are fixed (`src/trainer_data.c`, `src/field/encounter_check.c`) | "Set trainer / wild levels dynamically" |
| **New game**: start location, starting flags, starter choice | code only (`src/choose_starter.c`) | "Modifying the start location", "Change starter Pokémon" |
| **Graphics in general**: NCGR/NCLR/NCER, overworld sprites, battle backgrounds | `tools/nitrogfx` exists, no guide | sprite, tileset and battle background guides |
| **Area textures**: add textures for terrain | binary NSBTX; needs a writer | tileset PNGs (`tiles.png`, palettes) |
| **Music and sound** (SDAT) | binary `gs_sound_data.sdat` | m4a / Porydaw guides |
| **Battle scripts and move animations** | battle scripts are text (`files/battledata/script`), animations binary | battle script and animation guides |
| **Map sections, fly points, Town Map** | not listed | "New mapsec / map popup" |
| **Debugging**: printf, breakpoints, a debug menu | not covered | "Add a debug menu", "Debugging using printf / gdb" |
| **Map editor**: props, layout resize, object sprites | editor shows them, can't edit | Porymap |
