<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# Modding wiki

> AI-generated; not affiliated with pret. See AI.md at the repository root.

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
| add a new map | [adding-a-map.md](modding/adding-a-map.md) | id in `maps.h`, folder, `maps.txt` line, `map_headers.h` entry |
| change an existing map (name, Town Map spot, layout, folder) | [adding-a-map.md](modding/adding-a-map.md#changing-a-map) | |
| remove a map | [removing-a-map.md](modding/removing-a-map.md) | ids and banks are positions: cut it off or stub it |
| rename or add a map section (the name popup, met location) | [town-map-and-fly.md](modding/town-map-and-fly.md#1-map-sections) | `msg_0279.json`; `townmap.py follow-rules` for a new one |
| move or add a place on the Town Map | [town-map-and-fly.md](modding/town-map-and-fly.md#2-the-town-map) | `sLocationSpecs` in `pokegear_map.c`; `townmap.py render` |
| change the Town Map picture | [town-map-and-fly.md](modding/town-map-and-fly.md#3-changing-the-town-map-picture) | `pgmap_gra_00000010.png` + `.NSCR` |
| change where Fly lands or where you wake up after a blackout | [town-map-and-fly.md](modding/town-map-and-fly.md#changing-a-fly-point) | `sSpawnPoints` in `src/spawn_warp.c` |
| add a fly point | [town-map-and-fly.md](modding/town-map-and-fly.md#adding-a-fly-point) | `sSpawnPoints`, `gMapFlypointParams`, the Fly screen sprite count |
| use the map editor | [mapeditor README](../tools/mapeditor/README.md) | `tools/mapeditor/mapeditor.sh <Map>` |
| give a map weather (rain, snow, dark cave) | [weather.md](modding/weather.md#3-giving-a-map-weather) | set `"weather"` (a number) in `map.json` |
| change the weather from a script, or make it depend on an event | [weather.md](modding/weather.md#5-changing-weather-from-a-script) | add a command like `FlashEffect` |
| tune or add a weather effect | [weather.md](modding/weather.md#6-changing-or-adding-a-weather) | `sWeatherEntries` in `src/field/weather_manager.c` |

## NPCs, scripts and text

| I want to... | Guide | Command |
|---|---|---|
| move, hide or add an NPC | [npcs-and-scripts.md](modding/npcs-and-scripts.md#adding-an-npc) | `mapkit npc move / set / add` |
| pick a movement type | [npcs-and-scripts.md](modding/npcs-and-scripts.md#movement-types) | |
| change an NPC's sprite graphics, or add a new sprite | [overworld-sprites.md](modding/overworld-sprites.md#2-changing-or-adding-a-sprite-mapkit-sprite) | `mapkit sprite export / import / add` |
| add a movement action (a step for `applymovement`) | [overworld-sprites.md](modding/overworld-sprites.md#3-movement-actions) | |
| add a movement type (an NPC's own behaviour) | [overworld-sprites.md](modding/overworld-sprites.md#4-movement-types) | |
| learn scripting from scratch (tutorial: talk, give an item once, yes/no, movement, signs, triggers) | [scripting-basics.md](modding/scripting-basics.md) | |
| write event scripts | [SCRIPTING.md](modding/SCRIPTING.md) | edit `scripts.pory`; `mapkit pory show <Map>` |
| find the script command for something (HGSS has no specials) | [script-commands.md](modding/script-commands.md), [full list](modding/script-commands-list.md) | `python3 tools/scriptcmds/scriptcmds.py --find <word>` |
| give an item, heal, check the party, play a fanfare from a script | [script-commands.md](modding/script-commands.md#3-commands-by-task) | |
| use a standard script (Nurse Joy, mart, save prompt, item gift) | [script-commands.md](modding/script-commands.md#5-standard-scripts-callstd) | `callstd(std_x)` |
| add a new script command | [script-commands.md](modding/script-commands.md#6-adding-a-command) | append to `gScriptCmdTable` |
| add a script | [npcs-and-scripts.md](modding/npcs-and-scripts.md#adding-a-script) | `mapkit script add` |
| run a script on map load | [npcs-and-scripts.md](modding/npcs-and-scripts.md#init--level-scripts-mapscripts) | |
| move NPCs in a cutscene | [npcs-and-scripts.md](modding/npcs-and-scripts.md#movement-scripts) | |
| show a multichoice or list menu from a script | [ui.md](modding/ui.md#menus-from-scripts) | `multichoiceinit` ... `multichoiceexec` |
| add or edit dialogue | [npcs-and-scripts.md](modding/npcs-and-scripts.md#text), [SCRIPTING.md](modding/SCRIPTING.md#text) | `mapkit text add` |
| look up a text code (`{STRVAR_1 ...}`, `{COLOR n}`, `{PAUSE n}`, `\r`, `\f`) | [text-and-messages.md](modding/text-and-messages.md#4-control-codes) | |
| put a name, item or number into a message | [text-and-messages.md](modding/text-and-messages.md#5-string-buffers-strvar) | `bufferitemname(0, ...)`, then `{STRVAR_1 8, 0, 0}` |
| check a line fits in the text box | [text-and-messages.md](modding/text-and-messages.md#8-line-width) | `mapkit validate -w` (`text-width`) |
| color text, change fonts | [text-and-messages.md](modding/text-and-messages.md#6-colors) | `{COLOR 1}...{COLOR 0}` |
| add a message bank, find which bank holds a name | [text-and-messages.md](modding/text-and-messages.md#1-message-banks) | |
| find a free flag or var | [unknown-flags-vars.md](modding/unknown-flags-vars.md#free-flags) | `tools/flagusage` |
| find where a flag, var or sprite is used | [mapkit README](../tools/mapkit/README.md#commands) | `mapkit refs FLAG_X` |

## Story and gyms

| I want to... | Guide | Command |
|---|---|---|
| change where a new game starts | [new-game.md](modding/new-game.md#2-start-location) | |
| give starting flags, items, money or Pokémon | [new-game.md](modding/new-game.md#3-starting-flags-items-money-and-pokémon) | |
| change the three starters (and the rival's team to match) | [new-game.md](modding/new-game.md#4-the-starter) | |
| understand flag and var ranges (hide flags, scene vars, temp, daily) | [story-progression.md](modding/story-progression.md#how-progress-is-stored) | |
| find what blocks a route and what opens it | [story-progression.md](modding/story-progression.md#story-beats) | `mapkit refs VAR_X` |
| change the order of story events or skip one | [story-progression.md](modding/story-progression.md#changing-progression) | |
| know what unlocks after the League (`FLAG_GAME_CLEAR`) | [story-progression.md](modding/story-progression.md#elite-four-and-game-clear) | |
| change which badge an HM needs, or obedience levels | [gyms.md](modding/gyms.md#what-badges-do) | |
| change a leader's reward, entry gate or puzzle | [gyms.md](modding/gyms.md#summary) | |
| require badges for a gate | [gyms.md](modding/gyms.md#changing-gyms) | `checkbadge`, `countbadges` |

## Music and sound

| I want to... | Guide | Command |
|---|---|---|
| change a map's music | [music.md](modding/music.md#changing-which-music-plays) | edit `music_day` / `music_night` in `map.json` |
| add a song from a MIDI | [music.md](modding/music.md#adding-a-song) | `python3 tools/sound/sdat.py header sound/sound_data.json include/constants/sndseq.h` |
| add instruments from WAV samples | [music.md](modding/music.md#new-instruments) | |
| see or hear a game song or sample | [music.md](modding/music.md#whats-in-sound) | `sseq.py to-midi`, `swar.py extract` |
| check the sound tools | [music.md](modding/music.md#the-tools) | `python3 tools/sound/test_sound.py` |

## Trainers and battles

| I want to... | Guide | Command |
|---|---|---|
| change a trainer's party, levels or IVs | [trainers.md](modding/trainers.md#changing-a-party) | edit `files/poketool/trainer/trainers.json` |
| add a trainer | [trainers.md](modding/trainers.md#adding-a-trainer) | |
| start a trainer battle from a script | [trainers.md](modding/trainers.md#starting-a-battle) | `trainerbattle(...)`, `checkbattlewon` |
| change rematch teams | [trainers.md](modding/trainers.md#rematches) | `sTrainerRematchSets` |
| understand how phone rematches work (calls, days, tiers, gifts) | [phone.md](modding/phone.md#6-rematches) | |
| give a trainer a phone number and rematches | [phone.md](modding/phone.md#7-example-give-a-route-trainer-a-phone-number) | `pmtel_book.json` + C tables |
| change what callers say, or when the phone rings | [phone.md](modding/phone.md#4-what-route-trainers-say) | `sGenericPhoneCallHeaders`; [§5](modding/phone.md#5-when-the-phone-rings) |
| change a trainer's rematch day or time | [phone.md](modding/phone.md#8-quick-changes) | `rematchWeekday` / `rematchTimeOfDay` in `pmtel_book.json` |
| change or add a trainer's battle text (intro, defeat, after, mid-battle, rematch, gloat) | [trainer-text.md](modding/trainer-text.md) | edit `messages` in `trainers.json`, then `python3 tools/trmsg/trmsg.py build` |
| see what a trainer says | [trainer-text.md](modding/trainer-text.md#5-the-tool) | `python3 tools/trmsg/trmsg.py show TRAINER_X` |
| scale trainer levels to the player | [level-scaling.md](modding/level-scaling.md#trainer-pokémon) | edit `CreateNPCTrainerParty` |
| make a trainer smarter, change AI | [trainers.md](modding/trainers.md#the-ai) | `"ai_flags"` in `trainers.json` |
| change a move's power, type, effect | [moves.md](modding/moves.md#move-data-battle_movesjson) | edit `battle_moves.json` |
| add a move | [moves.md](modding/moves.md#adding-a-new-move) | |
| find move special cases in C | [moves.md](modding/moves.md#moves-named-in-c) | |
| add a trainer class (name, gender, prize money, music) | [trainer-classes.md](modding/trainer-classes.md#adding-a-class) | |
| change or add a trainer's battle sprite | [trainer-classes.md](modding/trainer-classes.md#trainer-sprites) | PNG in `graphics/trainers/front_pics/`; `trainer_pics.py check` |
| animate a trainer sprite | [trainer-classes.md](modding/trainer-classes.md#animation) | `"anims"` in `data/trainer_graphics/front_pics.json` |
| understand how a battle runs (server, clients, turn order) | [battle-engine.md](modding/battle-engine.md) | |
| read or write a battle script, find a script variable | [battle-engine.md](modding/battle-engine.md#5-battle-scripts) | macros in `asm/macros/btlcmd.inc` |
| add a battle script command | [battle-engine.md](modding/battle-engine.md#adding-a-script-command) | append to `sBattleScriptCommandTable` |
| show something new in battle (a client command) | [battle-engine.md](modding/battle-engine.md#6-adding-a-client-command) | |
| look up a battle term (`status2`, `battlerIdStatChange`...) | [battle-engine.md](modding/battle-engine.md#7-glossary) | |

## Pokémon

| I want to... | Guide | Command |
|---|---|---|
| change base stats, types, abilities, TM compatibility | [pokemon.md](modding/pokemon.md#base-stats-types-abilities-items-tmhm) | edit `personal.json` |
| change evolutions | [pokemon.md](modding/pokemon.md#evolutions) | edit `evo.json` |
| look up what an evolution method checks, and when | [evolutions.md](modding/evolutions.md#the-methods) | |
| add an evolution method | [evolutions.md](modding/evolutions.md#adding-a-method) | `GetMonEvolution` in `src/pokemon.c` |
| make Magnezone, Leafeon, Glaceon obtainable | [evolutions.md](modding/evolutions.md#example-2-location-evolutions-magnezone-leafeon-glaceon) | `MapHeader_GetMapEvolutionMethod` in `src/map_header.c` |
| change level-up or egg moves | [pokemon.md](modding/pokemon.md#level-up-learnsets) | |
| change Pokédex entries | [pokemon.md](modding/pokemon.md#pokédex-data) | |
| change the Johto Pokédex (which species, their order) | [pokedex.md](modding/pokedex.md#3-the-johto-order) | edit the `johto` list, regenerate `johtozukan.narc` |
| give the Pokédex, or unlock the National Dex, at another time | [pokedex.md](modding/pokedex.md#2-getting-the-pokédex) | `givepokedex` + `setflag(FLAG_GOT_POKEDEX)`; `natdexflagaction(1, VAR)` |
| mark a species seen or caught from a script | [pokedex.md](modding/pokedex.md#5-seen-and-caught) | `setmonseenflag(SPECIES_X)`; add `setmoncaughtflag` |
| replace sprites and icons | [pokemon.md](modding/pokemon.md#graphics) | PNG files |
| add a species (after Arceus, number 494) | [adding-a-species.md](modding/adding-a-species.md) | |
| change wild encounters | [wild-encounters.md](modding/wild-encounters.md) | `mapkit wild set` |
| change headbutt, Safari, Bug Contest | [wild-encounters.md](modding/wild-encounters.md#headbutt-trees) | |
| scale wild levels to the player | [level-scaling.md](modding/level-scaling.md#wild-pokémon) | edit `FieldSystem_GenerateRegularEncounter` |
| give a Pokémon from a script | [gift-pokemon-and-trades.md](modding/gift-pokemon-and-trades.md#1-givemon) | `givemon(SPECIES_X, level, item, form, ability, VAR)` |
| give one with set IVs, nature, shiny, ball, moves, met location | [gift-pokemon-and-trades.md](modding/gift-pokemon-and-trades.md#3-custom-gifts-givecustommon) | add `givecustommon` |
| give an egg | [gift-pokemon-and-trades.md](modding/gift-pokemon-and-trades.md#4-gift-eggs-giveegg) | `giveegg(SPECIES_X, MAPLOC(METLOC_X))` |
| change or add an in-game trade | [gift-pokemon-and-trades.md](modding/gift-pokemon-and-trades.md#5-in-game-trades) | edit `data/npc_trades.json`, then `python3 tools/npctrade/npctrade.py build` |
| change roamers: species, level, routes, encounter chance, how they move | [roamers.md](modding/roamers.md) | `src/field_roamer.c` |
| change breeding: egg chance, Everstone, IV inheritance, Destiny Knot, egg moves, egg level, hatch steps | [breeding.md](modding/breeding.md) | `src/get_egg.c`, `constants/daycare.h` |
| add an ability | [abilities.md](modding/abilities.md#adding-an-ability) | |
| find where an ability's effect is coded | [abilities.md](modding/abilities.md#where-an-ability-can-act) | `grep -rn ABILITY_X src files/battledata` |
| add a type (Fairy) | [adding-a-type.md](modding/adding-a-type.md) | |
| change the type chart (matchups) | [adding-a-type.md](modding/adding-a-type.md#3-the-type-chart) | `sTypeEffectiveness` in `src/battle/battle_util.c` |
| make Pokémon and moves Fairy (Gen 6 retypes) | [adding-a-type.md](modding/adding-a-type.md#7-giving-the-type-to-pokémon-and-moves) | edit `personal.json`, `battle_moves.json` |

## Items

| I want to... | Guide | Command |
|---|---|---|
| change an item's price, name, description, pocket | [items.md](modding/items.md#changing-an-item) | edit `data/items/items.json` |
| change what an item does when used or held | [items.md](modding/items.md#the-fields) | |
| add an item | [items.md](modding/items.md#adding-an-item) | `python3 tools/pokedata/items.py check data/items/items.json --include include` |
| change or add an icon | [items.md](modding/items.md#icons) | PNG in `files/itemtool/itemdata/item_icon/` |
| change what shops sell | [items.md](modding/items.md#marts) | `src/scrcmd_mart.c` |
| add a new kind of "Use" from the bag (or the Y button) | [party-menu-and-item-use.md](modding/party-menu-and-item-use.md#adding-a-new-kind-of-field-use) | `sItemFieldUseFuncs` |
| find why a medicine says "It won't have any effect", or shows the wrong message | [party-menu-and-item-use.md](modding/party-menu-and-item-use.md#what-decides-what) | `CanUseItemOnPokemon`, `ItemId_GetPartyUseType` |
| change what an item does in battle, add a ball | [party-menu-and-item-use.md](modding/party-menu-and-item-use.md#4-using-an-item-in-battle) | `BattleSystem_RecoverStatus`, `BattleSystem_CalculateBallShakes` |
| add or change a held item's effect | [party-menu-and-item-use.md](modding/party-menu-and-item-use.md#5-held-items) | `grep -rn HOLD_EFFECT_X src` |
| open the party menu for a new purpose, add a field move | [party-menu-and-item-use.md](modding/party-menu-and-item-use.md#2-the-party-menu) | `PartyMenuArgs`, `sFieldMoves` |

## Graphics

| I want to... | Guide | Command |
|---|---|---|
| understand NCGR, NCLR, NSCR, NCER, NANR and which graphics are PNG | [graphics.md](modding/graphics.md#1-the-file-types) | |
| find which archive and member a screen loads | [graphics.md](modding/graphics.md#3-finding-the-graphics-a-screen-uses) | `grep -n GfGfxLoader_ src/...`, or gdb `break GfGfxLoader_LoadCharData` |
| change a graphic inside a binary NARC (`files/a/...`) | [graphics.md](modding/graphics.md#4-changing-a-binary-archive) | `nitroarc -xf` / `-cf`, `nitrogfx` (in `build/heartgold.us/tools/`) |
| pick the right `nitrogfx` flags so the file rebuilds identically | [graphics.md](modding/graphics.md#5-picking-nitrogfxs-flags), [all of them](modding/graphics-sources.md#9-the-flags-read-from-the-headers) | `narcgfx.py flags ARCHIVE`, or `xxd -l 48 X.NCGR` then `cmp` |
| understand the PNG folders the build packs into archives (`graphics/battle_backgrounds/`, `graphics/battle_sprites/`) | [graphics-sources.md](modding/graphics-sources.md#4-an-archive-folder) | `members.json` |
| find a battle sprite or background's file (type icons, balls, HP boxes, move backgrounds, touch screen) | [graphics-sources.md §5](modding/graphics-sources.md#5-graphicsbattle_backgrounds-a007), [§6](modding/graphics-sources.md#6-graphicsbattle_sprites-a008) | |
| turn another binary archive (a menu) into such a folder | [graphics-sources.md](modding/graphics-sources.md#8-converting-another-archive) | `narcgfx.py export`, `move`, `cells` |
| edit a sprite's cells or animation | [graphics.md](modding/graphics.md#8-cells-and-animations) | `nitrogfx X.NCER X.json` |
| change which battle background a map uses | [battle-backgrounds.md](modding/battle-backgrounds.md#the-background) | `"battle_scene"` in `map.json` |
| understand which platforms a battle shows, and what else terrain changes | [battle-backgrounds.md](modding/battle-backgrounds.md#the-platforms-terrain) | |
| redraw a battle background (and its evening/night palettes) | [battle-backgrounds.md](modding/battle-backgrounds.md#4-changing-a-background) | `graphics/battle_backgrounds/backgrounds/<name>/`; layout rules in [§3](modding/battle-backgrounds.md#3-how-the-picture-is-laid-out) |
| redraw a battle platform | [battle-backgrounds.md](modding/battle-backgrounds.md#5-changing-a-platform) | `graphics/battle_sprites/platforms/<name>/` |
| add a battle background or platform | [battle-backgrounds.md](modding/battle-backgrounds.md#6-adding-a-background), [platform](modding/battle-backgrounds.md#7-adding-a-platform) | |

## Game rules and save data

| I want to... | Guide | Command |
|---|---|---|
| change the hours of morning, day and night | [day-night-and-rtc.md](modding/day-night-and-rtc.md#change-the-hours-of-morning-day-and-night) | edit `sTimeOfDayByHour` in `src/gf_rtc.c` |
| change the outdoor lighting by time | [day-night-and-rtc.md](modding/day-night-and-rtc.md#the-light-files) | edit `files/data/area00light.txt` |
| make an event happen at night, on a weekday, or once a day | [day-night-and-rtc.md](modding/day-night-and-rtc.md#7-recipes) | `getcurrenttimeofday`, `getweekday`, a `FLAG_DAILY_*` |
| know what happens when the DS clock is changed | [day-night-and-rtc.md](modding/day-night-and-rtc.md#6-changing-the-clock-the-penalty) | |
| change a hard-coded limit (level cap, IVs, egg steps, money, coins, bag size) | [game-limits.md](modding/game-limits.md) | |
| keep old saves working after an update (or migrate them) | [save-compatibility.md](modding/save-compatibility.md) | `tools/savemap/savemap.py` |
| know what a change costs in save space | [save-data.md](modding/save-data.md#what-common-mods-cost) | |
| understand the save layout | [save-data.md](modding/save-data.md) | |

## Code

| I want to... | Guide | Command |
|---|---|---|
| understand the main loop, tasks, overlays and heaps | [engine.md](modding/engine.md) | |
| run code every frame (a SysTask) or as a field event (a field task) | [engine.md](modding/engine.md#3-systasks), [field tasks](modding/engine.md#4-field-tasks) | |
| pick an overlay for new code, check free RAM | [engine.md](modding/engine.md#5-overlays) | |
| find why a new screen crashes at once or runs out of memory | [engine.md](modding/engine.md#loading-and-unloading), [heaps](modding/engine.md#6-heaps) | |
| print debug messages from C | [debugging.md](modding/debugging.md#3-printf) | `DebugPrintf`, or gdb `dprintf` |
| set breakpoints, step through code, find a crash | [debugging.md](modding/debugging.md#4-gdb) | `gdb -x tools/debug/pokeheartgold.gdb build/heartgold.us/main.nef` |
| see failed asserts (silent in normal play) | [debugging.md](modding/debugging.md#5-assertions) | `break GF_AssertFail` |
| add a debug menu | [debugging.md](modding/debugging.md#6-a-debug-menu) | |
| make a wave, ripple or wipe (per-scanline effect) | [scanline-effects.md](modding/scanline-effects.md) | `ScanlineEffect_StartWave`, `HBlankSystem_StartTask` |
| make a new screen or menu | [ui.md](modding/ui.md#adding-a-new-application), [checklist](modding/ui.md#11-checklist-for-a-new-screen) | |
| open a screen from the field | [ui.md](modding/ui.md#launching-an-application) | |
| decompile or match a function | [DECOMP-NOTES.md](DECOMP-NOTES.md) | |
| find a function under its old name (renamed to pret's) | [pret-names.md](modding/pret-names.md) | |

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
| **Area textures**: add textures for terrain | binary NSBTX; needs a writer | tileset PNGs (`tiles.png`, palettes) |
| **Move animations** | binary (`files/a/0/1/0`); battle scripts are covered in [battle-engine.md](modding/battle-engine.md#5-battle-scripts) | animation guides |
| **Map editor**: props, layout resize, object sprites | editor shows them, can't edit | Porymap |
