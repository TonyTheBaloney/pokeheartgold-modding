# AI work log

> AI-generated; not affiliated with pret. See AI.md at the repository root.

One entry per AI session from 2026-10-21 to 2026-10-22: what changed, the model, and how it
was checked. Later work is described in the commit messages (`git log`).

## 2026-10-21 battle.h unk fields
- Location: include/battle/battle.h; users in src/battle/battle_main.c, battle_controller.c, battle_controller_opponent.c, battle_controller_player.c
- Result: MATCHING (HG and SS: all 4 checksums OK)
- Tool/model: claude-opus-5-5
- Notes:
  - Offsets confirmed by compiling an offsetof probe with mwccarm. Old names
    TrainerAIData.unk280/unk288 were really at 0x1DD0/0x1DD8, and BattleMon.unk76 at 0x7A.
  - Fields no code touches -> unused_<offset>: TrainerAIData 12/13/14/1DD0/1DD8,
    BattleMon 7A, BattleContext 60/310A, BattleHpBar 14 (Window) and 4F_2 (bit),
    OpponentData 24/84, BattleTerrain A/C, BattleSystemUnusedWords 0/4/8,
    BattleSystem 210, BallThrow 23.
  - Write-only: BattleContext.unused_34 (cleared at end of after-move sequence),
    BattleSystem.unused_2428 (copy of BattleSetup.unk_164).
  - OpponentData.unk1C -> unusedPokepic (read as a fallback in OpponentData_GetPokepic, never assigned).
  - OpponentData.unk8C -> controllerData (byte buffer: OAM ptr at 0, controller command at 8).
  - OpponentData.unk1A9 -> padding_1A9 (alignment padding).
  - BattleSystem.unk98/unk9C -> setupUnk128 / setupSub134 (pass-through of BattleSetup
    unk_128/unk_134); setupSub134 retyped to struct BattleSetupSub_134 *, which drops two casts.
  - Removed the unused typedef UnkBtlCmdStruct_CPM (no users; not in upstream).

## 2026-10-21 scrcmd_mart.c data labels + mart enums
- Location: src/scrcmd_mart.c, include/overlay_03.h, src/overlay_03/shop_menu.c, src/field/touch_mart_app.c
- Result: MATCHING (HG and SS: all 4 checksums OK)
- Tool/model: claude-opus-5-5
- Notes:
  - Special mart lists named from the map scripts that pass each VAR_SPECIAL_x8004 index
    to std_special_mart (map codes resolved through include/constants/maps.h).
  - Pokeathlon daily tables use pret upstream's names (sPokeathlonPrizeExchangePriceOverrides_*).
  - Seal mart lists kept as _0.._6: no HGSS script calls SealMart, so the meaning of the index is unverified.
  - MART_TYPE_1/3/4 -> DECOR / POKEATHLON_DAILY / DATA_CARDS; added MART_BUY/MART_SELL.
    Unlike upstream, the decoration mart passes MART_BUY (upstream passes MART_TYPE_NORMAL there).
  - For the Pokeathlon mart types Mart_Init ignores the item list, so
    sDecorationMartItems[date.week] reading out of bounds is harmless original behavior.
  - Enum renames in shop_menu.c / touch_mart_app.c are marked only at the enum definition.

## 2026-10-21 encounter_tables_narc.h
- Result: no change
- Notes: the _000000NN suffixes are NARC member names generated from gs_enc_data.json,
  and the ENCDATA_<map> macros already name every entry.

## 2026-10-21 docs/modding (design + guides)
- Location: docs/modding/{README,DESIGN,pokemon,maps-and-warps,npcs-and-scripts,wild-encounters}.md
- Result: docs only, no ROM change
- Tool/model: claude-opus-5-5
- Notes: written from four repo surveys, with the key claims spot-checked
  (warp anchor/dynamic warp in field_control.c, trainer sight types,
  script/init macros, msg bank numbers, wild JSON schema, GENDER_RATIO).
  User decisions: per-map folders, docs in repo, Python CLI + library (mapkit).
  Also disabled push to pret: `git remote set-url --push upstream DISABLED`.

## 2026-10-21 Phase 1: map_object constants, named event JSON, tools/mapkit
- Location: include/constants/map_object.h; files/fielddata/eventdata/zone_event.json.txt + zone_event/*.json;
  tools/mapkit/; docs/modding/*
- Result: MATCHING (HG and SS: all 4 checksums OK after the JSON conversion); mapkit tests 13/13 OK
- Tool/model: claude-opus-5-5
- Notes:
  - MOVEMENT_TYPE_* named from gMapObjectMovementCallbacks; path names checked against
    sDirectionTable14..37 (index = table id + 7). 25 and 26 share one direction table.
  - OBJECT_TYPE_* from MapObject_GetTrainerSightType and gMapObjectTypeBehavior*. Type 3 meaning unknown.
  - Event JSON movement/type/facingDirection/bg type/bg dir rewritten with a line-level regex
    (formatting unchanged); the template now includes constants/map_object.h.
  - mapkit validate: 0 errors on the clean repo for both versions; 6 duplicate object id
    warnings are retail data (temp-flag NPCs sharing an id).

## 2026-10-21 Phase 2 pilot + phase 3: Cherrygrove in data/maps, edit commands
- Location: data/maps/{maps.txt,meson.build,Cherrygrove/}; meson.build; files/fielddata/eventdata/meson.build;
  files/fielddata/script/meson.build; files/msgdata/msg/meson.build; src/data/map_headers.h; tools/mapkit
- Result: MATCHING (HG and SS: all 4 checksums OK after migration and after script renames)
- Tool/model: claude-opus-5-5
- Notes:
  - Layout follows pokeemerald per user request: map.json holds header + events with
    pokeemerald keys; scripts.inc / map_scripts.inc / text.json / ids.h.
  - Build: data/maps/meson.build (before files/) reads maps.txt, regenerates the
    zone_event JSON and the MapHeader entry from map.json, copies scripts/text back to
    their original base names. Generated zone_event JSON equals the original.
  - mwasm quirk: `-I../..` is ignored, `-I../../` works (needed to include data/maps/.../ids.h).
  - Several meson files are CRLF; edits must keep that (python newline="").
  - Cherrygrove script labels renamed to Cherrygrove_EventScript_* (names from content /
    existing flag names; 009 "Cameron" from FLAG_HIDE_CAMERON).
  - Demo mod (fisher NPC, moved NPC, Marill surf slot) built non-matching as expected;
    saved as a patch in the session scratchpad, then reverted.

## 2026-10-22 All maps migrated to data/maps; scripting design
- Location: data/maps/* (540 folders), meson.build (data on public_includes), files/fielddata/script/meson.build,
  files/fielddata/eventdata/meson.build, src/encounter.c, src/field/gymmick/{ecruteak,vermilion}.c,
  src/field/legend_cutscene_camera.c, src/field_move.c, src/field_use_item.c, asm/map_object_*.s; docs/modding
- Result: MATCHING (HG and SS: all 4 checksums OK); mapkit validate 0 errors; tests 20/20
- Tool/model: claude-opus-5-5
- Notes:
  - Shared placeholder banks: lowest map id owns (MAP_EVERYWHERE); others reference @Everywhere.
  - Event headers included by C/asm/other scripts are rewritten to "maps/<MapName>/ids.h";
    data/ added to include paths because mwcc/mwasm ignore -I../.. (but accept -I../../data).
  - Generated files depend on mapkit sources (stale-output bug found when the include path changed).
  - docs/modding/SCRIPTING.md: poryscript-style language proposal (not built). Research via
    poryscript README/CHANGELOG/emitter source.

## 2026-10-22 scripts.pory compiler (poryscript-style) in mapkit
- Location: tools/mapkit/mapkit/pory/{__init__,parser,compiler}.py, tools/mapkit/script_config.json,
  tools/mapkit/tests/{test_pory,pory_roundtrip}.py, data/maps/meson.build, data/maps/Cherrygrove/scripts.pory
- Result: MATCHING (HG and SS: all 4 checksums OK) with Cherrygrove built from scripts.pory and
  Cherrygrove_EventScript_MysticWaterMan rewritten as structured code; tests 35/35
- Tool/model: claude-opus-5-5
- Notes:
  - User choices: Python in mapkit; readable generated labels; lowercase pokeemerald-style command names.
  - Conditions/autovars/jumps from script_config.json, not hard-coded.
  - ScrDef order = raw ScrDef lines + script blocks in file order; a script block named in a raw
    ScrDef line keeps that slot (lets scripts be converted out of raw without renumbering).
  - pory init round-trips all 451 maps that own their scripts (command-by-command check in tests).
  - Event script numbers for pory maps come from the compiled ScrDef order (not ids.h).

## 2026-10-22 All maps converted to scripts.pory (decompiler)
- Location: tools/mapkit/mapkit/pory/decompile.py (new), pory/{__init__,compiler}.py, repo.py, edit.py,
  cli.py, scripts.py; tools/mapkit/tests/{test_pory,pory_roundtrip}.py; data/maps/*/scripts.pory (452);
  docs/modding/{SCRIPTING,DESIGN,README,maps-and-warps,npcs-and-scripts}.md, tools/mapkit/README.md
- Result: MATCHING (HG and SS: all 4 checksums OK, every map built from scripts.pory); mapkit validate
  0 errors (HG, SS); tests 13 + 8 + 19 OK
- Tool/model: claude-opus-5-5
- Notes:
  - `mapkit pory init` now decompiles: if/elif/else from Compare+GoToIf* / GoToIfSet / NoItemSpace,
    after-End blocks as deferred ifs (FIFO queue mirrors the compiler; positions must increase),
    movement blocks in place (<Map>_Movement_<offset>), lowercase commands. Every script is compiled
    back and fingerprint-compared (label args -> positions, macro defaults filled); fallbacks:
    no deferred ifs -> labels + if/goto -> labels -> raw. `--raw` keeps the old behavior; `--all`.
  - Results: 2403 structured, 13 without deferred ifs, 1 labels, 0 raw; 2496 movements.
  - Compiler: top-level movement blocks now emitted in place with `.balign 4, 0` (GAS pads .balign
    without a fill value with NOPs in code sections); every scripts_inc ends with `.balign 4, 0`
    (all 451 original banks did).
  - Kept as written because bytes depend on it: dead GoTo/End left by GF's compiler, shared tail
    labels, ScrDef table as raw when file order != number order (210 maps), aliases (two ScrDef
    names, one script) and fall-through scripts become labels inside the previous script.
  - repo.pory_entry follows @Owner for scripts (maps borrowing Everywhere's scripts); script add
    refuses on borrowers.
  - Cherrygrove regenerated by the decompiler; its hand-written MysticWaterMan came out identical.
  - Meson checks scripts.pory existence at configure time: `meson setup --reconfigure` was needed.

## 2026-10-22 scrdefs block for script order in scripts.pory
- Location: tools/mapkit/mapkit/pory/{parser,compiler,decompile}.py, tools/mapkit/tests/test_pory.py,
  data/maps/*/scripts.pory (209 raw ScrDef tables replaced), docs/modding/{SCRIPTING,DESIGN,npcs-and-scripts}.md
- Result: MATCHING (HG and SS: all 4 checksums OK); compiled commands/numbers/map scripts/text identical
  for all 452 maps x 2 versions before and after (fingerprint compare); tests 13 + 8 + 21 OK
- Tool/model: claude-opus-5-5
- Notes:
  - `scrdefs { A B C }`: listed scripts numbered 1..n; unlisted script blocks follow in file order.
    Errors: second block, duplicate name, name not defined (script, label in a script, raw label).
  - Raw `ScrDef` lines still count (back compat).
  - Goldenrod_GlobalTerminal_1F keeps a raw second `ScrDefEnd` (real bytes in the original bank).

## 2026-10-22 Dialog inline in scripts.pory
- Location: tools/mapkit/mapkit/pory/{inline_text (new),__init__,compiler}.py, repo.py, validate.py,
  edit.py, cli.py; tests test_pory.py/test_edit.py; data/maps/*/{scripts.pory,text.json}; docs
- Result: MATCHING (HG and SS: all 4 checksums OK; msg headers keep ids); validate 0 errors HG/SS;
  tests 13 + 8 + 24 OK
- Tool/model: claude-opus-5-5
- Notes:
  - User chose inline strings over text blocks.
  - text.json keeps every slot: {"id", "from": "<Script>#<n>"} (n-th string of the script, source
    order, numbered by compiler.number_texts so deferred ifs don't reorder) or "from": "text"
    (a `text <id>` block). merged_text fills slots keeping ids; unfilled -> empty message +
    validate warning `empty-text`; strings with no slot appended.
  - Inlined: 3907 (used once); text blocks: 217 (used by several commands); left in text.json:
    ~2600 (used from C/asm/other files, raw blocks, by number, or unused; garbage entries).
  - Each map compiled before/after in HG and SS: same command fingerprint, same ScrDef order, same
    bank (ids + text + garbage) or skipped (none skipped).
  - script rename rewrites "from" slots; pory init runs inline-text unless --raw.

## 2026-10-22 pokeemerald-style names for map scripts and movements
- Location: tools/mapkit/mapkit/pory/naming.py (new), tools/mapkit/npc_names.json (new), cli.py;
  data/maps/* (scripts.pory, text.json slots, ids.h, map.json), src/field_move.c (one _EV_ name),
  docs/modding/*, tools/mapkit/{README.md,tests/test_pory.py}
- Result: MATCHING (HG and SS: all 4 checksums OK); validate 0 errors; tests 13 + 8 + 28 OK.
  Before/after: identical command fingerprints, map scripts, text banks for all maps x 2 versions;
  event data identical except 2266 `_EV_<old> + 1` expressions now resolved to the same numbers.
- Tool/model: claude-opus-5-5
- Notes:
  - 4663 renames (2259 scripts, the rest movements). Conventions checked against pret/pokeemerald
    (SlateportCity, Route104 scripts.inc): <Map>_EventScript_<Who>, Man1/Man2 numbering, CitySign,
    RouteSign<Place>, TrainerTips, <Map>_OnTransition, <Map>_Movement_<Actor><Action>.
    Upstream pret/pokeheartgold has no named map scripts (all scr_seq_*).
  - Who: hand-chosen script name > npc_names.json characters > dialog speaker "Name:" > trainer
    battled > sprite class (classes derived from trainers.json class per sprite; leaders/E4 by gym).
  - ~14% generic (Sign/Trigger/Scene) need human names. Local jump labels unchanged.
  - map.json uses bare labels for own scripts; borrowers (@Everywhere) keep _EV_ form.

## 2026-10-22 Level-up learnsets and egg moves as JSON
- Location: tools/pokedata/{pokedata,test_pokedata}.py (new); files/poketool/personal/
  {level_up_learnsets,egg_moves}.json (new); wotbl.narc and kowaza_list.narc removed (built);
  meson.build, files/poketool/personal/meson.build, files/fielddata/sodateya/meson.build; docs
- Result: MATCHING (HG and SS: all 4 checksums OK with both archives built from JSON); tests 5 OK
- Tool/model: claude-opus-5-5
- Notes:
  - Formats modeled on pokeemerald src/data/pokemon/level_up_learnsets.h (LEVEL_UP_MOVE) and
    egg_moves.h, as JSON keyed by SPECIES_*; stored with personal.json/evo.json.
  - wotbl member: u16 move | level<<9, 0xFFFF, zero pad to 4; 508 members (species + forms).
    kowaza_list: one member, 20000+species markers, moves, 0xFFFF.
  - nitroarc (tools/nitroarc) re-packs both byte-identically from member files.
  - Limits enforced: 21 level-up moves (MAX_LEARNED_MOVES buffer, whole member is read), 16 egg
    moves, egg species markers within the first 2045 entries (retail fills exactly 2045).
  - Not enforced: ascending levels (retail Banette is out of order). Relearner buffer
    (LEVEL_UP_LEARNSET_MAX 21 u16) is already overrun by retail species with 20+ moves.

## 2026-10-22 Named constants: egg move table (start of magic-number pass)
- Location: include/constants/daycare.h (EGG_MOVES_SPECIES_OFFSET, EGG_MOVES_TERMINATOR,
  EGG_MOVES_TABLE_SIZE), src/get_egg.c LoadEggMoves; tools/pokedata/pokedata.py reads its limits
  from the headers; meson.build depend_files
- Result: MATCHING (HG checksums OK)
- Tool/model: claude-opus-5-5
- Notes: names follow pokeemerald daycare.c (EGG_MOVES_SPECIES_OFFSET, EGG_MOVES_TERMINATOR).

## 2026-10-22 Named constants: stat stages
- Location: include/constants/pokemon.h (MIN_STAT_STAGE 0, DEFAULT_STAT_STAGE 6, MAX_STAT_STAGE 12);
  src/battle/{battle_util,battle_command,trainer_ai,battle_controller_player}.c (file-level markers)
- Result: MATCHING (HG and SS: all 4 checksums OK)
- Tool/model: claude-opus-5-5
- Notes: upstream pret used BATTLE_SUBSCRIPT_UPDATE_STAT_STAGE (=12) as the max stat stage in 35
  places in battle_util.c (looks like a mass replace of the literal 12); those are MAX_STAT_STAGE now.
  Two more misuses restored to 12: the Amulet Coin case of the send-out state switch (cases 7..15)
  and Iron Fist's movePower * 12 / 10. Real subscript uses (3075, 3291, 6247, table at 6300) kept.
  Safari catch-rate stage (also 0..12) left as is.

## 2026-10-22 Named constants: literals replaced by existing constants (batch 2)
- Location: 61 files in src/ and include/ (file-level markers); constants/badge.h include added to
  src/battle/battle_controller_player.c
- Result: MATCHING (HG and SS: all 4 checksums OK)
- Tool/model: claude-opus-5-5
- Notes: each site read before editing (loop bodies checked for what they count). Replaced:
  MAX_MON_MOVES (33 move-slot loops), BATTLER_MAX (9 battler loops), PARTY_SIZE (34 loops, 14 arrays;
  partyOrder[BATTLER_MAX][PARTY_SIZE]), NUM_STATS (IV loop), MAX_LEVEL (~25, table[MAX_LEVEL + 1]),
  FRIENDSHIP_MAX / FRIENDSHIP_TIER_MID_MIN / FRIENDSHIP_TIER_HI_MIN (~22), NATURE_NUM (PID math; the
  one `25u` became `(u32)NATURE_NUM` to keep unsigned division), MAX_EVOS_PER_POKE, MAX_EV_SUM,
  MAX_EV_PER_STAT, BADGE_FOG/BADGE_MINERAL, SPECIES_BAD_EGG, NATIONAL_DEX_COUNT/MAX_SPECIES,
  JOHTO_DEX_COUNT, PC_BOX_SLOT_PARTY_START, MONS_PER_BOX, NUM_BOXES.
  Not changed (not what they looked like): pokemon_icon_idx.c 494-499 (icon-table indices, 499 =
  Unown icons), pc_box.c HM list loop, shiny-leaf and IV loops of 6, trainer item slots,
  aiSwitchedPartySlot/switchMonIndex "= 6" sentinels, frontier level sentinels 120/121 (need new names).

## 2026-10-22 Named constants: IVs, daycare and eggs (batch 3)
- Location: include/constants/pokemon.h (MAX_PER_STAT_IVS, MAX_IV_MASK, USE_RANDOM_IVS),
  include/constants/daycare.h (DAYCARE_BREED_CHECK_STEPS, DAYCARE_PRICE_PER_LEVEL, EGG_CYCLE_STEPS,
  EGG_CYCLE_STEPS_SPECIAL_DAY, EGG_HATCH_LEVEL, EGG_HATCH_FRIENDSHIP, EGG_NATURE_PID_ATTEMPTS,
  MASUDA_METHOD_REROLLS); 18 .c files; docs/modding/game-limits.md (new)
- Result: MATCHING (HG and SS: all 4 checksums OK)
- Tool/model: claude-opus-5-5
- Notes: get_egg.c locals that hold an egg's remaining cycles renamed friendship -> eggCycles and use
  MON_DATA_EGG_CYCLES (existing alias of MON_DATA_FRIENDSHIP). CreateMon fixedIV 32/0x20 -> USE_RANDOM_IVS
  in 18 calls. Remaining candidates listed at the end of game-limits.md.

## 2026-10-22 Save data documentation and tools/savemap
- Location: docs/modding/save-data.md (new), docs/modding/README.md, tools/savemap/savemap.py (new)
- Result: docs + tool only; ROM unaffected
- Tool/model: claude-opus-5-5
- Notes: chunk sizes read from the built game (each *_sizeof in main.nef symbols, evaluated from
  main.sbin; HG and SS identical), layout computed with src/save.c's rules: block 0 63016 bytes (16
  sectors), block 1 (PC) 74512 (19), 35/35 sectors; extras at SAVE_PAGE_MAX+0..11; sectors 47-63 of each
  64-sector half unused. Cross-checks: SaveVarsFlags 368*2+2912/8 = 1100; Bag 486*4+4 = 1948; PC box
  30*136+16 = 4096. Flag ranges from flags.h. Not verified: which FLAG_UNK_/VAR_UNK_ are free; heap
  headroom for a larger SAVE_PAGE_MAX.

## 2026-10-26 Experience and leveling guide
- Location: docs/modding/experience.md (new); links from docs/WIKI.md, docs/modding/README.md,
  gyms.md, game-limits.md, level-scaling.md
- Result: docs only; ROM unaffected (HG: all 4 checksums OK after the recipe test was reverted)
- Tool/model: claude-opus-5-5
- Notes: growth tables, BtlCmd_CalcExpGain / Task_GetExp, Exp. Share, Lucky Egg, level-up flow, Rare
  Candy, Day-Care. Recipes (party-wide Exp. Share, Gen 5 scaling, exp on catch via a resumeWork field
  on GetterWork, level caps by badge count incl. Rare Candy) were applied together, compiled and linked
  into a HeartGold ROM, then reverted. Not play-tested (no emulator available). Cap table values are
  each next leader's highest level from trainers.json.

## 2026-10-26 Player movement guide
- Location: docs/modding/player-movement.md (new); links from docs/WIKI.md, docs/modding/README.md,
  overworld-sprites.md, gyms.md
- Result: docs only; ROM unaffected (HG: all 4 checksums OK after the recipe test was reverted)
- Tool/model: claude-opus-5-5
- Notes: PlayerAvatar_FootStep / bike / forced movement, Running Shoes and the touch-screen lock,
  allow_running (runningAllowed_Unused, read by nothing; 34 maps false), bike rules, ledge/one-way/
  stairs/ice/spin behaviors (ledge collision counted in data/landdata), the three HM paths. Recipes
  (running gated by allow_running, shoes in init, B-speed surfing, HM fallback to the lead via
  _HMUserOrLead incl. a key-item variant, Surf and Waterfall C checks) compiled and linked into a
  HeartGold ROM, then reverted. Bike recipes not built. Not play-tested (no emulator available).

## 2026-10-26 Status conditions guide
- Location: docs/modding/status-conditions.md (new); links from docs/WIKI.md, docs/modding/README.md
- Result: docs only; ROM unaffected (HG: all 4 checksums OK after the recipe test was reverted)
- Tool/model: claude-opus-5-5
- Notes: status bits (bits 0-11 used, new status at bit 12; Quick Feet/Hydration test the low byte,
  roamers save a u8), CONDITION_* numbers shared with the HP bar and status animations, inflicting
  subscript + MOVE_SUBSCRIPT_PTR + effect script, UMC end-of-turn state, special-damage halving in
  CalcMoveDamage, icons (Pokemon_GetStatusIconId / a/0/3/9 still binary; HP bar tiles in
  battle_hp_bar_data.h, hpicon.py round-trips FRZ), freeze cures extended to frostbite (no spare item
  flag), Shed Skin/Hydration names, following-Pokémon assert, Psycho Shift. Frostbite recipe (Ice Beam
  given the effect) compiled and linked into a HeartGold ROM, then reverted; Facade/Refresh change not
  built. Not play-tested (no emulator available).

## 2026-10-26 Side-feature guides
- Location: docs/modding/pokeathlon.md, pokewalker.md, safari-zone.md, battle-frontier.md,
  bug-catching-contest.md, apricorns-and-kurt.md, berry-pots.md, pokegear.md, following-pokemon.md
  (new); links from docs/WIKI.md (new "Side features and minigames" section), docs/modding/README.md
  (guide table and data-status table)
- Result: docs only; no source, data or build change
- Tool/model: claude-opus-5-5 (one subagent per guide, citations then checked mechanically: every
  file:line exists, links and anchors resolve; three stale line numbers fixed)
- Notes: corrections to older guides found on the way: items.md (berries aren't planted from the bag),
  encounter-mechanics.md (Bug Contest slots are 20/20/10/10/10/10/5/5/5/5%, not equal; Safari equal),
  wild-encounters.md (Safari objects give points, not levels; Pokéwalker courses found in
  asm/pokewalker_data.s), adding-a-species.md (second Pokéathlon table gPokeathlonPerformanceFileIds).
  Misleading names noted in the guides, not renamed: PERFORMANCE_*/ARCPERF_* stat order,
  MAPOBJECTFLAG_VISIBLE (means hidden), FLAG_UNK_996 (contest running), Safari Bait/Mud controller
  names, BattleArcade_GetWonBattlePoints (a board score). Retail quirks recorded: Heavy Ball tests
  catchRate instead of weight, Kurt ignores hasspaceforitem, Apricorn lost at 99, berries grow only
  while the pots screen is open. Binary data decoded but not converted: a/0/6/6 (berry growth),
  a/2/2/0-1 (follower rules/scripts, packer round-trips 7,120 rules), a/2/0/2-4 (Frontier; nitroarc
  round-trip). No recipe was built and nothing was play-tested.

## 2026-10-26 Move tutors and Move Relearner guide
- Location: docs/modding/move-tutors.md (new); links from docs/WIKI.md, docs/modding/README.md,
  pokemon.md, moves.md
- Result: docs only; ROM unaffected (HG: all 4 checksums OK after the recipe test was reverted)
- Tool/model: claude-opus-5-5
- Notes: relearner (level-up moves at or below the current level, not known, deduplicated; Heart
  Scale taken only on success), shared overlay-68 screen for relearner and one-move tutors
  (movetutorinit checks nothing; Wilma/ultimate-move checks are in the script), Frontier tutors
  (sTutorMoves index = TUTOR_* bit, waza_oshie.bin 505 x 8 bytes, menu rows from the caller's
  msg file), Headbutt tutor, Move Deleter (HMs forgettable only there). Retail issues found by
  reading C and objdump: eligibleMoves freed before the app reads it; LEVEL_UP_LEARNSET_MAX 21
  overflows for 20-21-move learnsets and leaves 21-move lists unterminated; tutor page count wrong
  for exactly 12/18 moves (uninitialized showNextButton); GetMoveTutorLearnsetIndex returns an
  uninitialized index that matches species by register allocation. Recipes 6.2-6.4 and 6.6 (Drain
  Punch as tutor bit 52 with its own NPC id, script in the Blackthorn house) built with make
  release, then reverted. Not play-tested (no emulator available). Section 7 lists the four retail
  problems with their fixes.
