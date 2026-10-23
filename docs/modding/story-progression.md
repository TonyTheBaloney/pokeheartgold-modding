<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# Flags, vars and story progression

> AI-generated; not affiliated with pret. See AI.md at the repository root.

How the game remembers story progress, and every story roadblock from New Game to
Red: what blocks you, which flag or var opens it, and where. Gyms and badges are
in [gyms.md](gyms.md).

Map scripts are `data/maps/<Map>/scripts.pory`, written below as `Map:line`.
"Trigger" means a `coord_events` entry in `map.json` (runs when you step on it while
its var equals its value). "Frame script" means an `INIT_SCRIPT_ON_FRAME_TABLE`
entry (runs as soon as its var has the given value). See
[npcs-and-scripts.md](npcs-and-scripts.md) and [SCRIPTING.md](SCRIPTING.md).

## How progress is stored

### Flags

2,912 one-bit flags (`NUM_FLAGS`), named in `include/constants/flags.h`. The file
is split by range; each range behaves differently:

| Range | Section in `flags.h` | Behavior |
|---|---|---|
| `0x001`-`0x03F` | `FLAG_MAPTEMP_*` | cleared on every warp (Cut trees, rocks, one-off scene guards) |
| `0x040`-`0x063` | (same section, unnamed) | not cleared; mostly free |
| `0x064`-`0x18F` | story flags: `FLAG_GOT_*`, `FLAG_UNK_*`, ... | persistent |
| `0x190`-`0x31F` | hide/show flags, `FLAG_HIDE_*` | persistent; an object with this flag is not spawned while it is set |
| `0x320`-`0x41F` | hidden items (`0x320` + index, 231 used) | |
| `0x420`-`0x54F` | item balls (`FLAG_HIDE_ITEMBALL_*`) | |
| `0x550`-`0x95F` | trainers (`TRAINER_FLAG_BASE` + trainer id, 738 used) | set when beaten: `settrainerflag` / `defeated()` |
| `0x960`-`0xA9F` | system flags (`FLAG_SYS_*`, `FLAG_GAME_CLEAR`, fly points) | mostly read by C |
| `0xAA0`-`0xB5F` | daily flags | cleared at midnight |
| `0x4000`+ | `FLAG_TEMP_*` (64, not saved) | |

Story flags do appear outside their section (many `FLAG_UNK_*` in the hide range are
story steps). Sizes and save cost are in
[save-data.md](save-data.md#whats-in-the-chunks-modders-touch-most).

**Hide flags are inverted:** set = hidden. A story NPC who appears later starts
with its flag set by the new-game script `files/fielddata/script/scr_seq/scr_seq_0149.s`
(about 145 `SetFlag FLAG_HIDE_*` lines), and a script clears it to bring them in.
In this document `init` means that script.

### Vars

368 saved 16-bit vars (`0x4000`-`0x416F`, `include/constants/vars.h`):

- `0x4000`-`0x401F` temp vars (`VAR_TEMP_*`), cleared on warp. `VAR_BATTLE_RESULT`
  is one of them.
- `0x4020`-`0x402F` object graphics vars.
- `0x4030`+ persistent. Story steps are kept in **scene vars**
  (`VAR_SCENE_*` and many `VAR_UNK_*`). Each one counts through the steps of one
  event, and triggers and frame scripts fire on exact values.
- `0x8000`-`0x800D` special vars (`VAR_SPECIAL_RESULT`, `VAR_SPECIAL_LAST_TALKED`),
  not saved.

### Commands

| In `.pory` | Does |
|---|---|
| `setflag(F)`, `clearflag(F)`, `flag(F)` | set, clear, test |
| `setvar(V, n)`, `addvar(V, n)`, `var(V) == n` | |
| `settrainerflag(T)`, `defeated(T)` | trainer flags |
| `givebadge(B)`, `checkbadge(B, V)`, `countbadges(V)` | badges are profile bits, not flags ([gyms.md](gyms.md#badges)) |
| `removeobject(obj)`, `addobject(obj)` | remove or add an object now; pair with its hide flag so it stays that way |

In C: `Save_VarsFlags_CheckFlagInArray` and friends (`src/save_vars_flags.c`), and
named accessors for system flags in `src/sys_flags.c` (`CheckGameClearFlag`,
`CheckRocketHideoutCleared`, `CheckBattledSnorlax`, fly points, menu icons...).

### Finding things

- `tools/mapkit/mapkit.sh refs FLAG_X` lists every map, script and C file using a
  flag or var.
- [unknown-flags-vars.md](unknown-flags-vars.md) lists the `FLAG_UNK_*` / `VAR_UNK_*`
  in use and the free ones. Most story steps below are still `UNK`: rename them in
  `flags.h`/`vars.h` as you work them out.
- `FLAG_UNK_998` appears all through this document. It means "Juggler Irwin has a
  new progress call"; his phone script reads and clears it
  (`src/application/pokegear/phone/scripts/phone_scripts_juggler_irwin.c:41`).
  It is not a gate.

## Overview

```
New Bark ─ starter ─ Mr. Pokémon (egg, Pokédex) ─ rival 1 ─ egg back to Elm
  → Falkner ─ aide's egg (opens Route 32)
  → Slowpoke Well (opens Bugsy's door) ─ rival 2 ─ Bugsy ─ HM01 Cut (Ilex exit)
  → Whitney ─ SquirtBottle ─ Sudowoodo (opens Route 37)
  → rival 3, Burned Tower beasts (opens Morty's gym) ─ Morty ─ HM03 Surf
  → Chuck (HM02 Fly) / Jasmine (after Amphy + SecretPotion) / Lake of Rage → Rocket HQ → Pryce
  → 3 of those 4 badges: takeover armed; 4: Elm calls, Radio Tower takeover
  → rival 4 ─ Radio Tower cleared (opens Route 44 and Blackthorn Gym)
  → Clair ─ Dragon's Den quiz (Rising Badge) ─ Elm's Master Ball
  → Kimono Girls ─ Ho-Oh (HG) / Lugia (SS) (opens New Bark east exit)
  → Route 27 ─ Tohjo Falls (Waterfall) ─ Victory Road ─ rival 5 ─ Elite Four
  → Hall of Fame (FLAG_GAME_CLEAR) ─ S.S. Ticket ─ Kanto ─ 8 Kanto badges ─ Mt. Silver ─ Red
```

## Johto

### Prof. Elm (`VAR_SCENE_ELMS_LAB`)

`VAR_SCENE_ELMS_LAB` (0x4108) tracks the early game and two later visits to the lab.

| Value | Set at | Meaning |
|---:|---|---|
| 0 | start | lab entry trigger sets `FLAG_ELMS_LAB_PREVENT_PLAYER_ESCAPE`; the starter machine sets `FLAG_GOT_STARTER` |
| 1 | `NewBark_ElmsLab_1F:274` | starter chosen, errand given; `VAR_SCENE_NEW_BARK_TOWN_OW = 1`. The aide's trigger gives Potions |
| 2 | `NewBark_ElmsLab_1F:694` | Potions received |
| 3 | `Route30_MrPokemonHouse:350` | Mystery Egg and Pokédex received |
| 4 | `NewBark_ElmsLab_1F:1009` | egg handed over, officer told the rival's name. Also starts the Route 29 catching tutorial (`VAR_UNK_408B = 1`), Mom's call (`VAR_SCENE_ROUTE_30_PHONE_CALL = 1`), shows the Route 30 battlers and the Cherrygrove mart's Poké Ball clerk |
| 5 | `NewBark_ElmsLab_1F:745` | dialogue only |
| 6 | `Violet_Gym:90` | Zephyr Badge |
| 7 | `Violet_Pokemart:115` | aide's egg received (`FLAG_GOT_EGG_FROM_ELMS_ASSISTANT`) |
| 8 | `DragonsDen_Shrine:220` | Rising Badge; frame script runs Elm's second scene |
| 9 | `NewBark_ElmsLab_1F:1213` | Master Ball received; `VAR_UNK_4079 = 3`, `VAR_SCENE_NEW_BARK_EAST_EXIT = 2` |

### Story beats

| # | Event | Where | Gate → sets | Opens |
|---|---|---|---|---|
| 1 | Mom's intro | `NewBark_PlayerHouse_1F:15`, frame `VAR_SCENE_PLAYERS_HOUSE_1F == 0` | sets `FLAG_GOT_BAG`, `_TRAINER_CARD`, `_SAVE_BUTTON`, `_OPTIONS_BUTTON` (start menu entries) | |
| 2 | Starter | `NewBark_ElmsLab_1F` | `VAR_SCENE_ELMS_LAB` 0 → 1 → 2 | |
| 3 | Pokégear | `NewBark_PlayerHouse_1F:322-332` | needs `FLAG_GOT_STARTER`; sets `FLAG_GOT_POKEGEAR` | |
| 4 | **New Bark west exit** | trigger `VAR_SCENE_NEW_BARK_WEST_EXIT == 0`, `NewBark:227` | pushes you back without `FLAG_GOT_POKEGEAR`; with it, Elm registers his number and the var becomes 1 | Route 29 |
| 5 | Guide Gent, Map Card | trigger `VAR_SCENE_CHERRYGROVE_CITY_OW` 0 → 1 → 2, `Cherrygrove:465` | `registerpokegearcard(1)` | |
| 6 | Apricorn Box | trigger `VAR_SCENE_ROUTE_30_OW == 0`, `Route30:59` | `FLAG_GOT_APRICORN_BOX`, var = 1 | |
| 7 | Mr. Pokémon, Oak | `Route30_MrPokemonHouse:48, 304, 342-352` | Mystery Egg, `FLAG_GOT_POKEDEX`; `VAR_SCENE_MR_POKEMONS_HOUSE = 1`, `VAR_SCENE_ELMS_LAB = 3`, `VAR_SCENE_CHERRYGROVE_CITY_OW = 3`, shows the Cherrygrove rival, `VAR_SCENE_ROUTE_30_OW = 2` (Elm's panic call) | |
| 8 | **Rival 1** | trigger `VAR_SCENE_CHERRYGROVE_CITY_OW == 3`, `Cherrygrove:490` | losing is allowed; var = 4 | |
| 9 | Egg back to Elm | `NewBark_ElmsLab_1F:818` | `VAR_SCENE_ELMS_LAB = 4` | Route 31 and on (nothing hard-blocks before this; the triggers just run in order) |
| 10 | Catching tutorial | trigger `VAR_UNK_408B == 1`, `Route29:109` | 5 Poké Balls, `FLAG_WATCHED_CATCHING_TUTORIAL` | |
| 11 | VS Recorder | trigger `VAR_UNK_4132 == 0`, `Route31_VioletGatehouse:16` | var = 1 | |
| 12 | Sprout Tower (optional) | `SproutTower_3F:13, 153` | rival scene (`VAR_UNK_40A4`), TM70 (`FLAG_UNK_076`); only moves a guide in Violet Gym | |
| 13 | Falkner | [gyms.md](gyms.md#violet-falkner) | `VAR_SCENE_VIOLET_CITY_OW = 1` → Elm calls → 2 | |
| 14 | Aide's egg | `Violet_Pokemart:28` | `FLAG_GOT_EGG_FROM_ELMS_ASSISTANT`, `VAR_SCENE_ELMS_LAB = 7` | |
| 15 | **Route 32 south** | trigger `VAR_UNK_408D == 0`, `Route32:220` | pushes you back until you have the aide's egg; then gives the Miracle Seed, var = 1 | Union Cave, Azalea |
| 16 | Azalea Rockets | trigger `VAR_UNK_4080 == 0`, `Azalea:196`; Kurt `Azalea_KurtHouse:84` | `FLAG_UNK_077`; Kurt and the well grunt leave (`FLAG_UNK_19E`, `FLAG_UNK_19F`) | Slowpoke Well |
| 17 | **Proton, Slowpoke Well** | `SlowpokeWell_B1F:38` | `FLAG_UNK_1A9` (grunt at Bugsy's door leaves), `FLAG_BEAT_AZALEA_ROCKETS`, `VAR_UNK_4075 = 1`, `VAR_UNK_4080 = 2` (Kurt gives a Fast Ball, → 3) | Azalea Gym |
| 18 | **Rival 2** | trigger `VAR_UNK_4075 == 1`, `Azalea:63` | var = 2 | |
| 19 | Bugsy | [gyms.md](gyms.md#azalea-bugsy) | Hive Badge: Cut | |
| 20 | **Ilex Forest** | Farfetch'd (`FLAG_FOUND_FIRST/SECOND_FARFETCHD`), `IlexForest:1098` gives HM01 (`FLAG_GOT_HM01`) | a Cut tree blocks the exit | Route 34, Goldenrod |
| 21 | Goldenrod | Bike Shop (`FLAG_UNK_089`), Radio Card (`Goldenrod_RadioTower_1F:157`, `FLAG_GOT_RADIO_CARD`) | | |
| 22 | Whitney | [gyms.md](gyms.md#goldenrod-whitney) | Plain Badge | |
| 23 | **SquirtBottle, Sudowoodo** | `Goldenrod_FlowerShop:246` checks `BADGE_PLAIN`; `Route36:43` needs the SquirtBottle | wild Sudowoodo Lv. 20; `FLAG_HIDE_ROUTE_36_SUDOWOODO`, `FLAG_CAUGHT_SUDOWOODO` | Route 37, Ecruteak |
| 24 | **Morty's gym locked** | frame `VAR_UNK_4079 == 0`, `Ecruteak_Gym:46` | an old man warps you out | until 26 |
| 25 | **Rival 3** | trigger `VAR_UNK_40A6 == 0`, `BurnedTower_1F:12` | var = 1 | |
| 26 | **Legendary beasts** | trigger `VAR_UNK_40A1 == 0`, `BurnedTower_B1F:21`, sets at :125-136 | beasts flee (`createroamer(0)` Raikou, `(1)` Entei at :72), Suicune shown in Cianwood, `VAR_UNK_4076 = 1`, `VAR_UNK_4079 = 2`, `FLAG_UNK_247` | Ecruteak Gym |
| 27 | Morty | [gyms.md](gyms.md#ecruteak-morty) | Fog Badge: Surf, Lv. 50 obedience | |
| 28 | **HM03 Surf** | Dance Theater: frame `VAR_UNK_410C == 0` → 1; grunt `Ecruteak_DanceTheater:198` → 2; gentleman :339/372 | `FLAG_GOT_HM03`, `VAR_UNK_410C = 3` | water routes, Olivine → Cianwood |
| 29 | Olivine rival | trigger `VAR_UNK_4078 == 0`, `Olivine:66` | scene only | |
| 30 | **Amphy** | `Olivine_LighthouseLightRoom:25` sets `VAR_SCENE_LIGHTHOUSE_JASMINE = 1`; `Cianwood_Pharmacy:4` gives the SecretPotion only at 1 (`FLAG_GOT_SECRETPOTION`); back at the top: `= 2`, `FLAG_HIDE_JASMINE_IN_GYM` cleared | Olivine Gym |
| 31 | Chuck → Fly | `Cianwood_Gym:67-71`; frame `VAR_UNK_4116 == 1` in Cianwood | HM02 (`FLAG_GOT_HM02`), Storm Badge allows Fly | |
| 32 | **Red Gyarados** | `LakeOfRage:248` (shiny, Lv. 30), Lance :299 | `FLAG_GOT_RED_SCALE`, `FLAG_UNK_0C3`, `VAR_UNK_40A8 = 1`; frame in `Mahogany_SouvenirShop` → 2 | Rocket HQ |
| 33 | **Rocket HQ** | `TeamRocketHeadquarters_*`, progress `VAR_UNK_40AC` 0 → 10; rival scene `B3F:173` | `FLAG_ROCKET_HIDEOUT_CLEARED`, Route 43 gate Rockets leave, `FLAG_UNK_1F9` (man at Pryce's door leaves) `B2F:730-734` | Mahogany Gym; Route 43 toll ends |
| 34 | Jasmine, Pryce | [gyms.md](gyms.md#olivine-jasmine) | `VAR_MIDGAME_BADGES` | |
| 35 | **Radio Tower** | [below](#the-rocket-takeover) | | Route 44, Blackthorn Gym |
| 36 | **Route 44** | trigger `VAR_UNK_407A == 0`, `Mahogany:110` | pushes you back; `Goldenrod_RadioTowerObservationDeck:178` sets 1 | Ice Path, Blackthorn |
| 37 | Clair, Dragon's Den | [gyms.md](gyms.md#blackthorn-clair) | Rising Badge, `VAR_SCENE_NEW_BARK_EAST_EXIT = 1`, `VAR_SCENE_ELMS_LAB = 8` | Waterfall |
| 38 | Master Ball | `NewBark_ElmsLab_1F:1213` | `VAR_SCENE_NEW_BARK_EAST_EXIT = 2`, `VAR_UNK_4079 = 3` | |
| 39 | **Kimono Girls** | trigger `VAR_UNK_4079 == 3`, `Ecruteak:72` (rival scene, → 4, `VAR_UNK_410C = 4`); `Ecruteak_DanceTheater:715-877`, five battles | HG: Clear Bell, `FLAG_UNK_103`; SS: Tidal Bell, `FLAG_UNK_104`. `VAR_UNK_410C = 6`, `VAR_UNK_40FA = 1` | Bell Tower (HG) / Whirl Islands (SS) |
| 40 | **Ho-Oh (HG)** | `Ecruteak_BellTowerBarrierStation:36` checks `BADGE_FOG`; `BellTower_1F:51` needs the Rainbow Wing (`FLAG_UNK_093`); `BellTowerRoof:51` Ho-Oh Lv. 45 | `FLAG_UNK_108`, `VAR_SCENE_NEW_BARK_EAST_EXIT = 3` (`BellTowerRoof:76`) | New Bark east exit |
| 40 | **Lugia (SS)** | `WhirlIslands_B2F:29` needs the Silver Wing (`FLAG_UNK_094`); `WhirlIslands_B3F_LugiaCave:63` Lugia Lv. 45 | `FLAG_UNK_109`, `VAR_SCENE_NEW_BARK_EAST_EXIT = 3` (:88) | New Bark east exit |
| 41 | **New Bark east exit** | triggers at (700,398) for `VAR_SCENE_NEW_BARK_EAST_EXIT` 1 (Mom: Elm is waiting) and 2 (rival: go see the Kimono Girls); both push you back. No trigger at 0 or 3 | | Route 27 |
| 42 | Tohjo Falls | Waterfall needs the Rising Badge | | Route 26, Victory Road |
| 43 | League reception gate | trigger `VAR_UNK_4110 == 0`, `Route22_PokemonLeagueReceptionGate:70` | prints "the eight Badges of Johto!" **without checking any**, sets 1 | Victory Road |
| 44 | **Rival 5** | trigger `VAR_UNK_40C5 == 0`, `VictoryRoad_3F:4` | var = 1 | Indigo Plateau |

So the real gates to the League are the east exit of New Bark (Ho-Oh or Lugia
done) and Waterfall (Rising Badge). Value 0 has no trigger, so before Clair you can
Surf east to Route 27; Tohjo Falls still stops you.

### The Rocket takeover

`VAR_MIDGAME_BADGES` (0x4134) counts Morty, Chuck, Jasmine and Pryce. When Chuck,
Jasmine or Pryce brings it to 3, they set `VAR_SCENE_ROCKET_TAKEOVER = 1` (Morty
doesn't check, since Surf makes him come first). At 4, a frame script in Mahogany
(:17), Olivine (:21) or Cianwood (after Fly, :76) plays Elm's call, which sets
`VAR_SCENE_ROCKET_TAKEOVER = 2`, `FLAG_ROCKET_TAKEOVER_ACTIVE`, `FLAG_UNK_0C5`,
`VAR_UNK_40F8 = 2`, and `VAR_MIDGAME_BADGES = 5` so it doesn't fire again.

`VAR_SCENE_ROCKET_TAKEOVER` (0x4077):

| Value | Set at | State |
|---:|---|---|
| 0 | start | normal Goldenrod |
| 1 | gyms above | 3 badges: extra grunts in Goldenrod (`FLAG_HIDE_ROCKET_TAKEOVER_4`) |
| 2 | Elm's call | takeover armed; trigger in `Goldenrod_Tunnel_B1F:507` |
| 3 | `Goldenrod_Tunnel_B1F:580` | got the Rocket uniform; Goldenrod overrun (`Goldenrod:54`), rival unmasks you at `Goldenrod_RadioTower_1F:314` |
| 4 | `Goldenrod_RadioTower_1F:448` | tower occupied: Petrel (5F) gives the Basement Key, the Director (`Goldenrod_TunnelWarehouse:27`) the Card Key, Archer on the deck |
| 5 | `Goldenrod_RadioTowerObservationDeck:171` | cleared |

`src/sys_vars.c:252` treats 2-4 as "takeover active". **Rival 4** is in the
underground: trigger `VAR_UNK_40A0 == 0`, `Goldenrod_Tunnel_B2F:301`; reaching B2F
needs the Basement Key.

Beating Archer (`Goldenrod_RadioTowerObservationDeck:58-183`) clears
`FLAG_ROCKET_TAKEOVER_ACTIVE`, sets `FLAG_BEAT_RADIO_TOWER_ROCKETS`, gives the
Rainbow Wing (HG, `FLAG_UNK_093`) or Silver Wing (SS, `FLAG_UNK_094`), sets
`VAR_UNK_407A = 1` (Route 44), and moves the Blackthorn Gym guard aside.

### Rival battles

No single var tracks the rival: each meeting has its own trigger var. Every battle
picks the team with `getstarterchoice` (`VAR_PLAYER_STARTER`): the rival has the
starter strong against yours. Teams are in `files/poketool/trainer/trainers.json`.

| Battle | Script | You chose Chikorita | Cyndaquil | Totodile |
|---|---|---|---|---|
| Cherrygrove | `Cherrygrove:512` | `TRAINER_PASSERBY_BOY_2` | `_BOY_3` | `TRAINER_PASSERBY_BOY` |
| Azalea | `Azalea:104` | `TRAINER_RIVAL_SILVER_7` | `_10` | `TRAINER_RIVAL_SILVER` |
| Burned Tower | `BurnedTower_1F:33` | `_8` | `_11` | `_4` |
| Goldenrod Underground | `Goldenrod_Tunnel_B2F:328` | `_18` | `_12` | `_17` |
| Victory Road | `VictoryRoad_3F:46` | `_9` | `_13` | `_5` |
| Mt. Moon (post-game) | `MountMoon:29` | `_15` | `_16` | `_14` |
| Indigo Plateau (post-game, Mon/Wed) | `PokemonLeagueEntrance:110` | `_20` | `_21` | `_19` |
| Dragon's Den multi (post-game) | `DragonsDen:409` | `PARTNER_RIVAL_2` | `_3` | `_1` |

In Cherrygrove he has no name yet, so the class is Passerby. `TRAINER_RIVAL_SILVER_2`,
`_3` and `_6` aren't used by any map. Scenes without a battle: Sprout Tower,
Olivine, the Rocket HQ, the Radio Tower, Ecruteak before the Kimono Girls.
The post-game chain is `VAR_UNK_40FC`: 1 (Mt. Moon) → 2 (Dragon's Den) → 3 (Elm's lab).

## Elite Four and game clear

- **Entrance** (`PokemonLeagueEntrance:17-40`): every entry clears
  `FLAG_DEFEATED_WILL`, `_KOGA`, `_BRUNO`, `_KAREN` and resets the room doors
  (`FLAG_HIDE_*S_ROOM_RETREAT` set, `FLAG_HIDE_*_ROOM_EXIT` cleared). That is the
  whole re-challenge reset.
- **Each room** (e.g. `PokemonLeagueWillRoom:11-90`): a frame script walks you in
  and closes the door behind you. Winning sets `FLAG_DEFEATED_<NAME>` and removes
  the objects blocking the exit; losing whites out.
- **Rematch teams:** each room and Lance use the `_2` trainer if
  `VAR_UNK_4135 >= 8` (all Kanto badges). Beating Red isn't needed.
- **Lance** (`PokemonLeagueLanceRoom`): on the first win (`!FLAG_GAME_CLEAR`, :200)
  shows Oak at Olivine port (`FLAG_HIDE_OLIVINE_PORT_OAK`) and sets
  `VAR_UNK_411A = 1`.
- **Hall of Fame** (`PokemonLeagueHallOfFame:15-200`): sets
  `VAR_SCENE_PLAYERS_HOUSE_1F = 3` (Mom sends you to Elm for the S.S. Ticket),
  brings Red back (`FLAG_UNK_25F` cleared), brings back static legendaries you
  didn't catch (Ho-Oh, Lugia, Sudowoodo, Red Gyarados, Mewtwo, the birds, Snorlax if
  met, Suicune if `VAR_SCENE_ROUTE_25 == 3`, Groudon/Kyogre, Rayquaza), recreates
  knocked-out roamers (`VAR_ROAMER_*_STATUS == 2` → 0, `createroamer`), then
  `hofcredits(0)`.
- **`FLAG_GAME_CLEAR`** (0x964) is set only in C. `hofcredits` →
  `CallTask_GameClear` (`src/game_clear.c:263`) records the clear time (first
  time), moves the continue point to your room, sets `FLAG_GAME_CLEAR` and the
  profile copy, saves, rolls credits and resets. Red's battle uses `hofcredits(1)`,
  which does the same without counting a League win.

`FLAG_GAME_CLEAR` is what unlocks the post-game. Scripts that check it: the S.S.
Aqua sailor, Elm's S.S. Ticket, the Battle Frontier gate
(`Route40_BattleFrontierGatehouse:16`), the Johto leaders' rematch schedules, Bell
Tower, Lake of Rage, National Park, and more. C reads it for the Trainer Card,
phone calls (Elm, Irwin, Buena), mail, Easy Chat words and app launching (see
`grep -rn FLAG_GAME_CLEAR src`).

## Post-game

### To Kanto

| Event | Where | Gate → sets |
|---|---|---|
| S.S. Ticket | `NewBark_ElmsLab_1F:339` | needs `FLAG_GAME_CLEAR`; sets `FLAG_GOT_SS_TICKET_FROM_ELM` |
| National Dex | frame `VAR_UNK_411A == 1`, `SsAquaOlivinePortInterior:43` | Oak runs `natdexflagaction(1)` (sets the Pokédex and profile flags) |
| Board the S.S. Aqua | `SsAquaOlivinePortInterior:133-210` | needs `FLAG_GAME_CLEAR` and the ticket; `VAR_BOAT_DIRECTION`, `FLAG_BOAT_ARRIVED`. After the first trip, sails Monday and Friday from Olivine |
| First voyage | `VAR_SCENE_SS_AQUA` 0 → 7 across the `SsAqua*` maps | 7 = arrived |
| Vermilion | `SsAquaVermilionPortExterior:13-18` | `setpokegearmapunlocklevel(2)` (Kanto map), `FLAG_SYS_FLYPOINT_VERMILION` |
| West Kanto | first entry to Viridian sets `VAR_UNK_4121 = 1`, `FLAG_UNLOCKED_WEST_KANTO` (`Viridian:30`) | the Route 22 gate's east guard steps aside |

Kanto battle music plays once `FLAG_SYS_FLYPOINT_VERMILION` is set
(`src/battle_intro_config.c:200`).

### Kanto roadblocks

**Power Plant** (opens Saffron, the Magnet Train, Misty):

| Step | Where | Sets |
|---|---|---|
| 1 | Power Plant manager, `Route10_PowerPlantBroken:69` | `FLAG_GOT_POWER_PLANT_MANAGERS_STORY`, `VAR_SCENE_ROUTE_10_POWER_PLANT = 1` |
| 2 | policeman trigger, `:104-133` | shows the grunt in Cerulean Gym, `VAR_UNK_411C = 1` |
| 3 | Cerulean Gym frame script | grunt flees; `VAR_SCENE_ROUTE_24_ROCKET = 1`, `VAR_UNK_4088 = 1`, Misty on Route 25 |
| 4 | Route 25 trigger `VAR_UNK_4088 == 1` | Misty returns to her gym (`FLAG_HIDE_CERULEAN_GYM_POPULATION` cleared) |
| 5 | Route 24 grunt, `Route24:21-127` | `VAR_SCENE_ROUTE_24_ROCKET` 2 → 3, reveals the Machine Part |
| 6 | Machine Part in Cerulean Gym | `VAR_SCENE_ROUTE_24_ROCKET = 4` |
| 7 | back to the manager, `Route10_PowerPlantBroken:22-61` | **`FLAG_RESTORED_POWER`**, TM57, `VAR_UNK_40FF = 1` |

`FLAG_RESTORED_POWER` is read by both Magnet Train stations, the Saffron gatehouses, Lavender Radio Station, the Copycat's house and Route 10.

**Others:**

| Roadblock | Opened by |
|---|---|
| Magnet Train | `ITEM_PASS`: the Fan Club chairman gives the Lost Item (`Vermilion_PokemonFanClub:95`, `VAR_UNK_4130 = 1`); the Copycat trades it for the Pass (`Saffron_CopycatHouse_2F:101-170`) |
| Snorlax, Routes 11/12 | Poké Flute channel playing (`radiomusicisplaying(5)`), which needs the EXPN Card (`Lavender_RadioStation`, `FLAG_GOT_EXPN_CARD`, after power is restored). Sets `FLAG_SNORLAX_MEET` |
| Route 19 | beating Blaine ([gyms.md](gyms.md#cinnabar-blaine)) |
| Viridian Gym | Blue on Cinnabar with `VAR_UNK_4135 >= 7` |
| Route 9, Rock Tunnel | field moves only |
| Battle Frontier | `FLAG_GAME_CLEAR` (`Route40_BattleFrontierGatehouse`) |

### Mt. Silver and Red

1. Beating Blue sets `VAR_UNK_4096 = 1`; Viridian's frame script plays Oak's call (→ 2).
2. Oak's lab with `VAR_UNK_4096 == 2` (`Pallet_TownOaksLab:110-163`) gives HM08 Rock
   Climb, sets `FLAG_UNLOCKED_MT_SILVER`, `FLAG_GOT_HM08` and `VAR_UNK_4110 = 2`.
3. The Route 22 gate's west guard (trigger `VAR_UNK_4110 == 1`) stands aside.
   Rock Climb needs the Earth Badge.
4. Red (`MountSilver_CaveSummit:4-56`): win → `FLAG_UNK_25F` (hides him until the next
   Hall of Fame), `VAR_UNK_40FD = 1` (Blue's rematch schedule), first time
   `VAR_UNK_4131 = 1` (Kanto starters in Oak's lab), `RIBBON_LEGEND`, `hofcredits(1)`.

### Legendaries

| Pokémon | Chain |
|---|---|
| Raikou, Entei | roam from the Burned Tower scene (`createroamer(0/1)`); status in `VAR_ROAMER_RAIKOU_STATUS` / `_ENTEI_STATUS` (1 = caught, 2 = knocked out) |
| Suicune | `VAR_SCENE_ROUTE_25`: Route 14 sighting (`FLAG_UNK_14D`) or Misty's badge → 1, Eusine → 2, battle → 3 |
| Other version's bird | the Pewter old man (`Pewter:39-75`, no gate): HG gives the Silver Wing (`FLAG_UNK_094`, shows Lugia), SS the Rainbow Wing (`FLAG_UNK_093`, shows Ho-Oh). Lv. 70 |
| Latias (HG) / Latios (SS) | `VAR_UNK_4130 == 1` (Lost Item received): Steven in Vermilion (`Vermilion:39-114`) runs `createroamer(2/3)`, → 2 |
| Groudon (HG) / Kyogre (SS), Rayquaza | `VAR_SCENE_EMBEDDED_TOWER`: 1 Kanto starter from Oak, 2 orb from Mr. Pokémon, 3 Cliff Edge Gate, 4 after the battle, 5 Jade Orb from Oak, 6/7/9 Rayquaza room, 8 Oak afterwards |
| Arceus event, Sinjoh Ruins | `VAR_SCENE_SINJOH_MYSTRI_ROOM`; needs an event Arceus leading the party (`RuinsOfAlph:167`). Steps not traced |

## Engine-side progress

| What | Where |
|---|---|
| Start menu entries | `FLAG_GOT_BAG` 0x11B + n (Trainer Card, Save, Options); Pokédex `FLAG_GOT_POKEDEX`, Pokégear `FLAG_GOT_POKEGEAR`; `src/start_menu.c:290, 538` via `src/sys_flags.c` |
| Pokégear cards | `registerpokegearcard(n)`: 1 Map (Cherrygrove), 2 Radio (Goldenrod Radio Tower); Kanto map via `setpokegearmapunlocklevel` (Route 27 → 1, Vermilion → 2) |
| Running Shoes | `PlayerSaveData.hasRunningShoes` (not a flag), given by Mom in Cherrygrove (`Cherrygrove:164`) |
| National Dex | `natdexflagaction(1)` sets it; `natdexflagaction(2, V)` checks |
| Fly points | `FLAG_SYS_FLYPOINT_*` (0x9B0 + `FLYPOINT_*`) set automatically on entering a map listed as a fly point in `sSpawnPoints` (`src/spawn_warp.c:128`, called from `src/field_warp_state.c`). Vermilion, Victory Road and the Pokéathlon are set by script |
| Whiteout point | set on entering a Pokémon Center, your house or the League (`src/field_warp_tasks.c:262`), or by `setspawn` |
| New game | `NewGame_InitSaveData` (`src/overlay_36.c:251`): your room, ¥3000, `FLAG_UNK_960`; then the `init` script for hide flags. No vars are set |

## Changing progression

| I want to... | Do this |
|---|---|
| skip an event | set the flags and vars it would set, in the `init` script or in a script you run earlier; check its later readers with `mapkit refs` |
| remove a roadblock NPC | set its hide flag in `init` (or clear the `FLAG_HIDE_*` it waits for) |
| remove a trigger | change the trigger var's start value, or delete the `coord_events` entry |
| add a roadblock | an object with a new hide flag (set in `init`, cleared when the event is done), or a trigger on a free var that pushes the player back (copy `NewBark_EventScript_LyraTrigger`) |
| require badges for something | `checkbadge(BADGE_X, VAR)` for one badge, `countbadges(VAR)` for a number |
| change post-game unlocks | the `FLAG_GAME_CLEAR` checks listed above |
| make a new story flag or var | rename a free `FLAG_UNK_*` / `VAR_UNK_*` ([unknown-flags-vars.md](unknown-flags-vars.md#free-flags)); don't use maptemp, temp or daily ranges for story |

## Not verified

- Whether the Route 30 battlers fully block the route or one lane.
- Whether the Azalea well grunt (`FLAG_UNK_19F`) blocks the well entrance.
- What Ho-Oh/Lugia battle outcomes 2 and 3 mean (both white out).
- How the Cherrygrove mart is out of Poké Balls before step 4 (probably the
  clerk hidden by `FLAG_HIDE_CHERRYGROVE_MART_SPECIAL_CLERK`).
- The fly-point table in `src/spawn_warp.c`: the `FLYPOINT_GOLDENROD`,
  `_ECRUTEAK` and `_CIANWOOD` rows point at different cities than their names. The
  values match the ROM; the names may be wrong.
- The Sinjoh Ruins and the later Steven chain (`VAR_UNK_4130` 3-7).
