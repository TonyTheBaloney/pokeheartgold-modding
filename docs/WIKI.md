<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

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
| change a terrain texture (grass, road, water...) | [area-textures.md](modding/area-textures.md#4-changing-a-texture) | edit `data/area_textures/NNN/textures/*.png`, `palettes/*.pal` |
| add a texture for terrain | [area-textures.md](modding/area-textures.md#5-adding-a-texture) | `mapkit areatex add SET image.png` |
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
| understand what each HM checks (party menu, A prompt, while moving) | [player-movement.md](modding/player-movement.md#6-field-moves-hms) | `scr_seq_0146.s`, `src/field_move.c` |
| use HMs without a Pokémon that knows the move (or with a key item) | [player-movement.md](modding/player-movement.md#hms-without-a-pokémon-that-knows-the-move) | `Call _HMUserOrLead` in `scr_seq_0146.s` |
| change a leader's reward, entry gate or puzzle | [gyms.md](modding/gyms.md#summary) | |
| require badges for a gate | [gyms.md](modding/gyms.md#changing-gyms) | `checkbadge`, `countbadges` |

## Music and sound

| I want to... | Guide | Command |
|---|---|---|
| change a map's music | [music.md](modding/music.md#changing-which-music-plays) | edit `music_day` / `music_night` in `map.json` |
| change battle music (by trainer class, one trainer, species, map, or from a script) | [battle-music.md](modding/battle-music.md#4-recipes) | `src/battle_intro_config.c` |
| change victory or trainer eyes-meet music | [battle-music.md](modding/battle-music.md#3-victory-music) | |
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
| add a double-battle pair (Twins) or a tag pair of trainers | [double-battles.md](modding/double-battles.md#3-double-and-tag-battles-from-trainers-who-spot-you) | `"double": 2`, `std_trainer` + `std_trainer_2` |
| a multi battle with an AI partner (like Lance in the Rocket Hideout) | [double-battles.md](modding/double-battles.md#recipe-a-new-multi-battle) | `multibattle(partner, T1, T2, 0)` |
| a partner who joins every battle (Diamond/Pearl escort mode) | [double-battles.md](modding/double-battles.md#5-escort-mode-a-partner-for-every-battle) | `setescortmode`, `VAR_FOLLOWER_TRAINER_NUM` |
| make a trainer smarter, change AI | [trainers.md](modding/trainers.md#the-ai) | `"ai_flags"` in `trainers.json` |
| change a move's power, type, effect | [moves.md](modding/moves.md#move-data-battle_movesjson) | edit `battle_moves.json` |
| add a move | [moves.md](modding/moves.md#adding-a-new-move) | |
| find move special cases in C | [moves.md](modding/moves.md#moves-named-in-c) | |
| read or edit a move's animation | [move-animations.md](modding/move-animations.md#3-reading-and-editing-them) | edit `data/battle_anims/moves/NNNN_<MOVE>.anim`, `make` |
| give a new move an animation | [move-animations.md](modding/move-animations.md#81-a-new-move-with-an-existing-animation) | copy a `.anim` file in `data/battle_anims/moves/`, or remap in `BattleAnimSystem_StartMove` |
| change a status, weather or stat-change animation | [move-animations.md](modding/move-animations.md) | `data/battle_anims/effects/` |
| add an effect function or command for animation scripts | [move-animations.md](modding/move-animations.md#84-a-new-effect-function) | `gBattleAnimFuncTable` |
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
| change who learns tutor moves (Frontier tutors, Headbutt) | [move-tutors.md](modding/move-tutors.md#waza_oshiejson) | edit `waza_oshie.json` |
| change tutor prices, or add a tutor move | [move-tutors.md](modding/move-tutors.md#65-add-a-move-to-the-frontier-tutors) | `sTutorMoves` in `src/field/scrcmd_move_tutor.c` |
| add a new move tutor NPC | [move-tutors.md](modding/move-tutors.md#66-a-new-one-move-tutor-that-uses-waza_oshiejson) | `movetutorinit(slot, MOVE_X)` + `moverelearnergetresult(VAR)` |
| change the Move Relearner (price, which moves it lists) | [move-tutors.md](modding/move-tutors.md#1-the-move-relearner) | `MoveRelearner_GetEligibleLevelUpMoves` in `src/move_relearner.c` |
| fix the retail tutor/relearner bugs (freed list, 21-move learnsets, tutor page count) | [move-tutors.md](modding/move-tutors.md#7-problems-in-the-original-game) | |
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
| see what changes a Pokémon's form (Griseous Orb, Gracidea, Rotom, Deoxys, Burmy, battle) | [forms.md](modding/forms.md#4-what-changes-a-form) | |
| change a form's stats, learnset or sprites | [forms.md](modding/forms.md#6-changing-the-existing-forms) | `DEOXYS_ATK`... in `personal.json`; `otherpoke/<species>/` |
| add a form to a species | [forms.md](modding/forms.md#5-adding-a-form) | `ResolveMonForm`, `SanitizeMonForm` in `src/pokemon.c` |
| change wild encounters | [wild-encounters.md](modding/wild-encounters.md) | `mapkit wild set` |
| change how often encounters happen (rate math, Repel, Cleanse Tag, flutes, abilities) | [encounter-mechanics.md](modding/encounter-mechanics.md#2-the-step-encounter-roll) | `FieldSystem_EncounterRateRoll` in `src/field/encounter_check.c` |
| change fishing bite chance or reel timing | [encounter-mechanics.md](modding/encounter-mechanics.md#7-fishing) | rod `rate` in the table; `sReelWindow` in `src/field/fishing.c` |
| change swarms, or start one from a script | [encounter-mechanics.md](modding/encounter-mechanics.md#8-swarms) | `sSwarmMapLUT` in `src/swarm.c`; `enablemassoutbreaks` |
| switch a map's wild Pokémon from a script (event tables, radio sounds) | [encounter-mechanics.md](modding/encounter-mechanics.md#10-switching-tables-from-a-script) | new script command |
| change headbutt, Safari, Bug Contest | [wild-encounters.md](modding/wild-encounters.md#headbutt-trees); more in [safari-zone.md](modding/safari-zone.md), [bug-catching-contest.md](modding/bug-catching-contest.md) | |
| scale wild levels to the player | [level-scaling.md](modding/level-scaling.md#wild-pokémon) | edit `FieldSystem_GenerateRegularEncounter` |
| give a Pokémon from a script | [gift-pokemon-and-trades.md](modding/gift-pokemon-and-trades.md#1-givemon) | `givemon(SPECIES_X, level, item, form, ability, VAR)` |
| give one with set IVs, nature, shiny, ball, moves, met location | [gift-pokemon-and-trades.md](modding/gift-pokemon-and-trades.md#3-custom-gifts-givecustommon) | add `givecustommon` |
| give an egg | [gift-pokemon-and-trades.md](modding/gift-pokemon-and-trades.md#4-gift-eggs-giveegg) | `giveegg(SPECIES_X, MAPLOC(METLOC_X))` |
| change or add an in-game trade | [gift-pokemon-and-trades.md](modding/gift-pokemon-and-trades.md#5-in-game-trades) | edit `data/npc_trades.json`, then `python3 tools/npctrade/npctrade.py build` |
| find every static/legendary encounter, its level and flags | [static-encounters.md](modding/static-encounters.md#3-the-static-encounters) | `grep -rn 'wildbattle(' data/maps` |
| make a legendary catchable again after knocking it out or running | [static-encounters.md](modding/static-encounters.md#41-catchable-again-after-a-loss-a-knockout-or-running-away) | hide it in the map's `OnLoad` only when `VAR_BATTLE_RESULT` is `BATTLE_OUTCOME_MON_CAUGHT` |
| change a static Pokémon's level or moves | [static-encounters.md](modding/static-encounters.md#42-change-its-level) | `wildbattle(SPECIES_X, level, 0)`; add `setwildmonmoves` |
| add a new static encounter | [static-encounters.md](modding/static-encounters.md#44-add-a-new-one) | object + `wildbattle` + `FLAG_ENGAGING_STATIC_POKEMON` in `OnLoad` |
| change shiny odds, or see who can be shiny (wild, statics, gifts, eggs, trades, trainers) | [shiny.md](modding/shiny.md) | `SHINY_CHECK` in `src/pokemon.c`, `SHINY_ODDS` |
| add a Shiny Charm, a force-shiny flag or shiny-locked encounters | [shiny.md](modding/shiny.md#6-recipes) | `generateWildNonShinyAndAddToParty` in `src/field/encounter_check.c` |
| change or remove the shiny Red Gyarados | [shiny.md](modding/shiny.md#3-the-red-gyarados) | `wildbattle(SPECIES_GYARADOS, 30, 1)` in `data/maps/LakeOfRage/scripts.pory` |
| change roamers: species, level, routes, encounter chance, how they move | [roamers.md](modding/roamers.md) | `src/field_roamer.c` |
| change breeding: egg chance, Everstone, IV inheritance, Destiny Knot, egg moves, egg level, hatch steps | [breeding.md](modding/breeding.md) | `src/get_egg.c`, `constants/daycare.h` |
| change a species' growth rate or experience yield | [experience.md](modding/experience.md#1-growth-rates) | `growthRate`, `expYield` in `personal.json` |
| change a growth curve, or add one | [experience.md](modding/experience.md#changing-a-curve) | edit `files/poketool/personal/growtbl.csv` |
| understand who gets experience and how much (Exp. Share, Lucky Egg, trainer and traded bonus) | [experience.md](modding/experience.md#2-experience-in-battle) | `BtlCmd_CalcExpGain`, `Task_GetExp` in `src/battle/battle_command.c` |
| make the Exp. Share party-wide (Gen 6) | [experience.md](modding/experience.md#5-recipe-party-wide-exp-share) | |
| scale experience by level difference (Gen 5) | [experience.md](modding/experience.md#6-recipe-gen-5-level-scaling) | |
| give experience for catching | [experience.md](modding/experience.md#7-recipe-experience-for-catching) | new states in `Task_GetPokemon` |
| add level caps by badge count (battle and Rare Candy) | [experience.md](modding/experience.md#8-recipe-level-caps-by-badge-count) | `GetLevelCap` |
| add an ability | [abilities.md](modding/abilities.md#adding-an-ability) | |
| find where an ability's effect is coded | [abilities.md](modding/abilities.md#where-an-ability-can-act) | `grep -rn ABILITY_X src files/battledata` |
| add a status condition (Frostbite) | [status-conditions.md](modding/status-conditions.md) | |
| find every place a status is checked | [status-conditions.md](modding/status-conditions.md#what-to-change) | `grep -rn STATUS_BURN src files/battledata` |
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

## Side features and minigames

| I want to... | Guide | Command |
|---|---|---|
| change a Pokémon's Pokéathlon stars | [pokeathlon.md](modding/pokeathlon.md#9-how-to-change-a-species-stats) | `nitroarc -xf files/poketool/personal/performance.narc` |
| change which events a Pokéathlon course has | [pokeathlon.md](modding/pokeathlon.md#10-how-to-change-course-composition) | `gPokeathlonCourseEventIds` in `asm/pokeathlon_course_data.s` |
| change Pokéathlon scoring, Athlete Points or the Athlete Shop | [pokeathlon.md](modding/pokeathlon.md#11-how-to-change-scoring-and-prizes), [shop](modding/pokeathlon.md#8-the-athlete-shop-and-data-cards) | `src/pokeathlon/pokeathlon_event_points.c`; `sPokeathlonPrizeExchangePriceOverrides` in `src/scrcmd_mart.c` |
| change the Pokémon or items on a Pokéwalker course | [pokewalker.md](modding/pokewalker.md#change-a-courses-pokémon) | `sPokewalkerCourses` bytes in `asm/pokewalker_data.s` |
| change when Pokéwalker courses unlock | [pokewalker.md](modding/pokewalker.md#change-watts-needed-or-the-national-dex-gate) | `PokewalkerApp_UnlockNextCourse` |
| change the experience or friendship from a Stroll | [pokewalker.md](modding/pokewalker.md#change-experience-or-friendship-on-return) | `PokewalkerApp_AddStrollExp` |
| see what the ROM can't change on the Pokéwalker | [pokewalker.md](modding/pokewalker.md#10-what-the-rom-cant-change) | |
| change the Pokémon in a Safari Zone area, or its bonus Pokémon | [safari-zone.md](modding/safari-zone.md#change-an-areas-encounters) | edit `files/arc/safari_enc.json` |
| understand Safari object points, area age and bonus Pokémon | [safari-zone.md](modding/safari-zone.md#6-object-points-area-age-and-bonus-pokémon) | `sObjectLevelBoosts` in `src/safari_zone_encounters.c` |
| add a Safari object, or unlock objects and the Area Customizer sooner | [safari-zone.md](modding/safari-zone.md#add-an-object), [unlocks](modding/safari-zone.md#change-when-objects-and-the-customizer-unlock) | `SafariZone_SetObjectUnlockLevel` |
| change Safari Balls, the fee, objects per area, Bait/Mud odds | [safari-zone.md](modding/safari-zone.md#change-the-limits), [odds](modding/safari-zone.md#battle-actions) | |
| change Battle Frontier opponents or their sets | [battle-frontier.md](modding/battle-frontier.md#13-how-tos) | `nitroarc -xf` a copy of `files/a/2/0/3` (sets) / `files/a/2/0/2` (trainers) |
| change a Frontier Brain's team | [battle-frontier.md](modding/battle-frontier.md#change-the-brain-teams) | trainers 305-314 in `files/a/2/0/2` |
| change the Frontier's banned species | [battle-frontier.md](modding/battle-frontier.md#change-the-banned-species) | `sBattleFrontierBanlist` in `src/pokemon.c` |
| change BP rewards, BP prizes or Factory rental pools | [battle-frontier.md](modding/battle-frontier.md#8-battle-points), [rentals](modding/battle-frontier.md#9-battle-factory-rental-pools) | |
| change the Bug-Catching Contest days, time limit or Sport Balls | [bug-catching-contest.md](modding/bug-catching-contest.md#12-how-to) | `scr_seq_0151.s`; `sport_balls` in `src/overlay_bug_contest.c` |
| add a Bug Contest Pokémon, change scoring or prizes | [bug-catching-contest.md](modding/bug-catching-contest.md#add-a-contest-pokémon), [scoring](modding/bug-catching-contest.md#8-scoring-your-catch) | `files/data/mushi/mushi_encount.csv`; `BugContest_JudgePlayerMon` |
| run the Bug Contest on another map | [bug-catching-contest.md](modding/bug-catching-contest.md#run-the-contest-on-another-map) | |
| add an Apricorn tree or change its colour | [apricorns-and-kurt.md](modding/apricorns-and-kurt.md#add-an-apricorn-tree-to-a-map) | `sTreeApricorns` in `src/apricorn_tree_sys.c` |
| change Apricorn regrowth | [apricorns-and-kurt.md](modding/apricorns-and-kurt.md#change-regrowth) | `ApricornTrees_RegrowEmpty` |
| make Kurt faster, give more balls, or make other balls | [apricorns-and-kurt.md](modding/apricorns-and-kurt.md#kurt-faster-more-balls-other-balls) | `data/maps/Azalea_KurtHouse/scripts.pory`; `sApricornBallItems` |
| change what Level/Lure/Moon/Love/Heavy/Fast/Friend Ball do | [apricorns-and-kurt.md](modding/apricorns-and-kurt.md#5-apricorn-balls-in-battle) | `grep -n "case ITEM_.*_BALL" src/battle/battle_command.c` |
| change a berry's growth time or yield | [berry-pots.md](modding/berry-pots.md#change-one-berrys-growth-time-drain-or-yield) | `berry_param.py` on a copy of `files/a/0/6/6` |
| make all berries grow faster, change mulch, add pots | [berry-pots.md](modding/berry-pots.md#make-berries-grow-faster-globally), [mulch](modding/berry-pots.md#change-moisture-or-mulch-behaviour), [pots](modding/berry-pots.md#add-more-pots) | |
| change what a radio show says, or add episodes | [pokegear.md](modding/pokegear.md#change-what-a-show-says) | `files/msgdata/msg/msg_0411`-`msg_0420.json` |
| change where or when a radio station can be heard | [pokegear.md](modding/pokegear.md#change-where-or-when-a-station-can-be-heard) | `radio_signal` in `map.json`; `Radio_GetAvailableChannels` |
| add a radio station | [pokegear.md](modding/pokegear.md#add-a-station) | new `shows/*.c` + a row in `sRadioShowFuncs` |
| give or take Pokégear cards (map, radio) | [pokegear.md](modding/pokegear.md#cards) | `registerpokegearcard(1)` map, `(2)` radio |
| understand Town Map markings, memos and roamer icons | [pokegear.md](modding/pokegear.md#markings-and-memos) | `pokegear_map_markings.c` |
| let a large Pokémon follow indoors | [following-pokemon.md](modding/following-pokemon.md#81-let-a-large-species-follow-indoors) | `FollowMon_GetPermissionBySpeciesAndMap` in `src/follow_mon.c` |
| turn following on or off on a map | [following-pokemon.md](modding/following-pokemon.md#82-enable-or-disable-following-on-a-map) | `"follow_mode"` in `data/maps/<Map>/map.json` |
| add something new the follower says | [following-pokemon.md](modding/following-pokemon.md#83-add-an-interaction) | `msg_0265.json` + `files/a/2/2/0`, `a/2/2/1` |
| keep the follower in its ball during a scene | [following-pokemon.md](modding/following-pokemon.md#6-script-commands) | `followmonrecall`, `setfollowmoninhibitstate(1)` |
| make following a switch the player can turn off | [following-pokemon.md](modding/following-pokemon.md#85-make-following-toggleable) | |

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
| understand which transition a battle plays (wild, trainer, cave, night) | [battle-visuals.md](modding/battle-visuals.md#1-how-a-transition-is-picked) | `EncounterEffect_GetDefaultEffect` |
| give a class another transition, or pick one from a script | [battle-visuals.md](modding/battle-visuals.md#4-recipes) | `sTrainerBattleIntroParams`; `VAR_BATTLE_TRANSITION` |
| redraw a gym leader / Elite Four / Rocket mugshot | [battle-visuals.md](modding/battle-visuals.md#3-changing-a-mugshot-picture) | `files/a/1/0/9` with `nitroarc` + `nitrogfx` |
| add a mugshot for a new trainer or class | [battle-visuals.md](modding/battle-visuals.md#43-a-new-mugshot) | new effect id 47, `gEncounterEffectFuncs` |
| make a trainer class (or one trainer) use another Poké Ball | [battle-visuals.md](modding/battle-visuals.md#5-which-ball-a-trainers-pokémon-come-out-of) | `TrainerClass_GetBall`; `"ball"` in `trainers.json` |
| redraw a Poké Ball, or find every graphic a new ball needs | [battle-visuals.md](modding/battle-visuals.md#6-poké-ball-graphics) | `graphics/battle_sprites/balls/` |

## Screens and menus

General framework (applications, windows, text, sprites, input): [ui.md](modding/ui.md).

| I want to... | Guide | Command |
|---|---|---|
| show IVs or EVs on the summary screen | [summary-screen.md](modding/summary-screen.md#4-showing-ivs-and-evs) | `PokemonSummary_PrintStats` |
| change the nature colors on the summary screen | [summary-screen.md](modding/summary-screen.md#3-nature-colors) | `PokemonSummary_PrintStatLabel`, `gNatureStatMods` |
| add a page or change labels on the summary screen | [summary-screen.md](modding/summary-screen.md#5-other-edits) | `msg_0302` |
| add an option to the Options menu | [options-menu.md](modding/options-menu.md#3-worked-example-auto-run) | |
| add a choice to an option, change text speeds or defaults | [options-menu.md](modding/options-menu.md#4-changing-existing-options) | `Options_Init` |
| change the naming screen's keyboard | [naming-screen.md](modding/naming-screen.md#6-how-to-change-a-keyboard-page) | `sKeyboardRow_*` |
| change a name's maximum length | [naming-screen.md](modding/naming-screen.md#7-how-to-change-the-maximum-length) | |
| change the default player or rival names | [naming-screen.md](modding/naming-screen.md#8-how-to-change-the-default-names) | `msg_0254` |
| skip or force the nickname prompt | [naming-screen.md](modding/naming-screen.md#9-how-to-skip-or-force-the-nickname-prompt) | |
| skip the intro movie, or make it skippable sooner | [intro-title-credits.md](modding/intro-title-credits.md#6-how-to-skip-the-intro-movie) | `gApplication_IntroMovie`, `skipAllowed` |
| skip the title screen | [intro-title-credits.md](modding/intro-title-credits.md#7-how-to-skip-the-title-screen) | `gApplication_CheckSave` |
| change the title screen (logo, cry, music, timeout, hidden button combos) | [intro-title-credits.md](modding/intro-title-credits.md#8-how-to-change-the-title-screen) | `files/demo/title/titledemo/` |
| change Professor Oak's speech, skip the info menu, fix the gender or name | [intro-title-credits.md](modding/intro-title-credits.md#9-how-to-change-professor-oaks-speech) | `msg_0219`, `OakSpeech_DoMainTask` |
| skip Oak's speech entirely (default name and gender) | [intro-title-credits.md](modding/intro-title-credits.md#10-how-to-skip-oaks-speech-entirely) | |
| change the credits text or timing, or make them skippable | [intro-title-credits.md](modding/intro-title-credits.md#11-how-to-change-the-credits) | `msg_0440`, `sCreditMsgLines` |
| add, rename, hide or reorder a start menu entry | [start-menu.md](modding/start-menu.md#4-how-to) | |
| make a start menu entry run a script | [start-menu.md](modding/start-menu.md#worked-example-an-entry-that-runs-a-script) | |
| add an entry to the bag's item menu | [bag.md](modding/bag.md#add-an-entry-to-the-item-menu) | `BagApp_PrepareContextMenu`, `gItemActionFuncs` |
| change a bag pocket's size, or add a pocket | [bag.md](modding/bag.md#change-a-pockets-capacity), [pockets](modding/bag.md#add-remove-rename-or-reorder-a-pocket) | `NUM_BAG_*` |
| open the bag from new code and read the result | [bag.md](modding/bag.md#2-opening-the-bag) | `Bag_CreateView`, `BagView_Init` |
| change the number of PC boxes | [pc-storage.md](modding/pc-storage.md#changing-the-number-of-boxes) | `NUM_BOXES` |
| add a box wallpaper | [pc-storage.md](modding/pc-storage.md#adding-a-wallpaper) | |
| show more in the PC's info panel, add a PC menu entry, change release rules | [pc-storage.md](modding/pc-storage.md#4-how-tos) | |

## Game rules and save data

| I want to... | Guide | Command |
|---|---|---|
| change the hours of morning, day and night | [day-night-and-rtc.md](modding/day-night-and-rtc.md#change-the-hours-of-morning-day-and-night) | edit `sTimeOfDayByHour` in `src/gf_rtc.c` |
| change the outdoor lighting by time | [day-night-and-rtc.md](modding/day-night-and-rtc.md#the-light-files) | edit `files/data/area00light.txt` |
| make an event happen at night, on a weekday, or once a day | [day-night-and-rtc.md](modding/day-night-and-rtc.md#7-recipes) | `getcurrenttimeofday`, `getweekday`, a `FLAG_DAILY_*` |
| know what happens when the DS clock is changed | [day-night-and-rtc.md](modding/day-night-and-rtc.md#6-changing-the-clock-the-penalty) | |
| change walking, running or surfing speed | [player-movement.md](modding/player-movement.md#1-how-a-step-happens) | `PlayerAvatar_FootStep` |
| stop running on some maps (make `allow_running` work) | [player-movement.md](modding/player-movement.md#no-running-on-chosen-maps) | `MapHeader_IsRunningAllowed` |
| start with the Running Shoes | [player-movement.md](modding/player-movement.md#running-shoes-from-the-start) | `GiveRunningShoes` in `scr_seq_0149.s` |
| change where the bike works, its speed, Cycling Road | [player-movement.md](modding/player-movement.md#4-the-bicycle) | `allow_cycling`, `ItemCheckUseFunc_Bicycle`, `setbikestatelock` |
| add ledges, one-way edges, stairs, ladders, ice, spin tiles | [player-movement.md](modding/player-movement.md#5-tiles-that-change-movement) | paint the behavior in `permissions.txt` |
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
| the map file format (gen4map 1.2) | [gen4map/FORMAT.md](gen4map/FORMAT.md) |
| what the files become in the ROM | [gen4map/BINARY.md](gen4map/BINARY.md) |
| drawing and writing NSBMD/NSBTX | [gen4map/RENDERING.md](gen4map/RENDERING.md) |
| why the map files are laid out this way | [modding/DESIGN.md](modding/DESIGN.md), [CHANGE-0001](gen4map/CHANGE-0001-maps-as-files.md), [CHANGE-0002](gen4map/CHANGE-0002-terrain-authoring.md), [CHANGE-0003](gen4map/CHANGE-0003-area-textures.md) |
| plans for a standalone Gen 4 tool | [gen4map/ROADMAP.md](gen4map/ROADMAP.md) |
| battle animation scripts (`a/0/1/0`, `a/0/6/1`): words, opcodes, jumps, inline emitter data | [modding/move-animations.md §2](modding/move-animations.md#2-the-file-format), [§4](modding/move-animations.md#4-the-commands) |

## Ideas (not built)

| Idea | Notes |
|---|---|
| shiny colors for Pokémon icons; shiny and IVs on the naming screen | [ideas/shiny-icons.md](ideas/shiny-icons.md) |

## Not documented yet

Compared with what the pokeemerald wiki and pret tooling cover, these have no
guide here yet, in rough order of how often a hack needs them:

| Topic | State in this fork | pokeemerald equivalent |
|---|---|---|
| **Map editor**: props, layout resize, object sprites | editor shows them, can't edit | Porymap |
