<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# Gyms and badges

> AI-generated; not affiliated with pret. See AI.md at the repository root.

Covers what a badge does, how each of the 16 gyms gives one, what keeps you out of
each gym, and how the gym puzzles work. The story around them, and how flags and
vars work in general, are in [story-progression.md](story-progression.md).

Map scripts are `data/maps/<Map>/scripts.pory`, written below as `Map:line`.
`init` is the new-game script `files/fielddata/script/scr_seq/scr_seq_0149.s`,
which sets the hide flags that NPCs start with.

## Badges

Badge ids are in `include/constants/badge.h`:

| Johto | id | Kanto | id |
|---|---:|---|---:|
| `BADGE_ZEPHYR` | 0 | `BADGE_BOULDER` | 8 |
| `BADGE_HIVE` | 1 | `BADGE_CASCADE` | 9 |
| `BADGE_PLAIN` | 2 | `BADGE_THUNDER` | 10 |
| `BADGE_FOG` | 3 | `BADGE_RAINBOW` | 11 |
| `BADGE_STORM` | 4 | `BADGE_SOUL` | 12 |
| `BADGE_MINERAL` | 5 | `BADGE_MARSH` | 13 |
| `BADGE_GLACIER` | 6 | `BADGE_VOLCANO` | 14 |
| `BADGE_RISING` | 7 | `BADGE_EARTH` | 15 |

They are bits in the player profile, not flags: `u8 johtoBadges` (ids 0-7) and
`u8 kantoBadges` (ids 8-15, stored as bit `id - 8`) in `include/player_data.h`.
`PlayerProfile_TestBadgeFlag`, `PlayerProfile_SetBadgeFlag` and
`PlayerProfile_CountBadges` (a popcount of both bytes, 0-16) are in `src/player_data.c`.

| Script command | Does |
|---|---|
| `givebadge(BADGE_X)` | sets the bit |
| `checkbadge(BADGE_X, VAR)` | VAR = 1 if owned |
| `countbadges(VAR)` | VAR = total, Johto and Kanto. No map script uses it |

### What badges do

**Field moves.** Two places check the same badges: the party menu
(`src/field_move.c`) and the std scripts that run when you press A on an obstacle
(`scr_seq_0146.s`, `std_field_*`). Surfing from the shore is checked in C,
`src/field/field_control.c:610`.

| Move | Badge | `field_move.c` |
|---|---|---|
| Rock Smash | Zephyr | :330 |
| Cut | Hive | :189 |
| Strength | Plain | :295 |
| Surf | Fog | :254 |
| Fly | Storm | :221 |
| Whirlpool | Glacier | :608 |
| Waterfall | Rising | :365 |
| Rock Climb | Earth | :397 |

Flash, Teleport, Dig, Sweet Scent, Headbutt and Chatter need no badge.

**Obedience** (`TryDisobedience`, `src/battle/battle_controller_player.c:1915`).
Traded Pokémon obey up to a level that depends on the badges you own. Johto and
Kanto badges both count:

| Badges | Obeys up to |
|---|---|
| none | Lv. 10 |
| 1+ | Lv. 20 |
| 2+ | Lv. 30 |
| Fog | Lv. 50 |
| Mineral | Lv. 70 |
| 8+ | any level |

The Fog and Mineral steps check those two badges, not a count. A hack that lets
you take gyms in any order should change these lines to count badges.

**Other effects of the badge count:**
- Which items marts sell (`src/scrcmd_mart.c`, tiers by total badges): see
  [items.md](items.md#marts).
- Money lost on whiteout scales with the count (`src/battle/battle_system.c:1316`).
- Vermilion Gym's gates start open if you have the Thunder Badge (`src/gymmick_init.c:61`).
- Phone calls and radio shows pass the count or single badges to their scripts
  (Juggler Irwin, Prof. Elm, the Pokémon Search Party show).

**Two badge counters kept by hand.** Scripts also count some badges in vars:

- `VAR_MIDGAME_BADGES` (0x4134): +1 from Morty, Chuck, Jasmine and Pryce. At 3,
  Chuck, Jasmine or Pryce sets `VAR_SCENE_ROCKET_TAKEOVER = 1`. At 4, Prof. Elm calls
  and starts the Radio Tower takeover, and the var is set to 5. See
  [story-progression.md](story-progression.md#the-rocket-takeover).
- `VAR_UNK_4135`: Kanto badges, +1 from each Kanto leader. 7 makes Blue let you into
  the Viridian Gym (`CinnabarIsland:99`). 8 gives the Elite Four and Lance their
  rematch teams (`PokemonLeagueWillRoom:70` and the other rooms).

If you add a badge or move one, update these counters by hand: they are not
derived from the badge bits.

## How a leader script works

Every leader script follows the same pattern (Falkner, `Violet_Gym:47`):

```
checkbadge(BADGE_ZEPHYR, VAR_SPECIAL_RESULT)      // already beaten: talk, or retry the TM
trainerbattle(TRAINER_LEADER_FALKNER_FALKNER, 0, 0, 0)
checkbattlewon(VAR_SPECIAL_RESULT)                // lost: whiteout
givebadge(BADGE_ZEPHYR)
addspecialgamestat(SCORE_EVENT_BADGE_GET)
settrainerflag(TRAINER_BIRD_KEEPER_GS_ROD)        // gym trainers count as beaten
...                                                // story flags and vars: see each gym
if (!itemspace(ITEM_TM51, 1)) { ... std_bag_is_full }
callstd(std_give_item_verbose)
setflag(FLAG_GOT_TM51_FROM_FALKNER)
```

If the bag is full, the leader keeps the TM. Talking to them again retries it,
because the script checks the badge and then the TM flag.

**Rematches.** Each gym's `OnTransition` hides the leader at some hours or weekdays,
so they can be met elsewhere. If a phone rematch is arranged
(`getphonebookrematch(PHONE_CONTACT_X)` is non-zero), the leader is hidden and
fought at `Saffron_FightingDojo` with their `_2` team (`include/constants/trainers.h`).
Otherwise the hours depend on `checkregisteredphonenumber`. Weekdays are RTC
values, 0 = Sunday. Most Johto leaders only start doing this after
`FLAG_GAME_CLEAR`.

## Summary

| # | Gym | Leader (`TRAINER_LEADER_…`) | Badge | TM | What blocks the gym | Puzzle |
|---|---|---|---|---|---|---|
| 1 | Violet | `FALKNER_FALKNER` | Zephyr | TM51 Roost | nothing (Sprout Tower is optional) | elevator |
| 2 | Azalea | `BUGSY_BUGSY` | Hive | TM89 U-turn | grunt at the door until Slowpoke Well | Spinarak carts |
| 3 | Goldenrod | `WHITNEY` | Plain | TM45 Attract | nothing | none (maze) |
| 4 | Ecruteak | `MORTY_MORTY` | Fog | TM30 Shadow Ball | old man throws you out until Burned Tower | invisible path |
| 5 | Cianwood | `CHUCK_CHUCK` | Storm | TM01 Focus Punch | nothing (Surf to get there) | waterfall winch |
| 6 | Olivine | `JASMINE_JASMINE` | Mineral | TM23 Iron Tail | Jasmine at the Lighthouse until Amphy is cured | none |
| 7 | Mahogany | `PRYCE_PRYCE` | Glacier | TM07 Hail | man at the door until Rocket HQ | ice floor |
| 8 | Blackthorn | `CLAIR_CLAIR` | Rising | TM59 Dragon Pulse | guard at the door until the Radio Tower | moving platforms |
| 9 | Pewter | `BROCK_BROCK` | Boulder | TM80 Rock Slide | nothing | none |
| 10 | Cerulean | `MISTY_MISTY` | Cascade | TM03 Water Pulse | Misty away until the Power Plant chain | none |
| 11 | Vermilion | `LT_SURGE_LT__SURGE` | Thunder | TM34 Shock Wave | nothing | trash cans |
| 12 | Celadon | `ERIKA_ERIKA` | Rainbow | TM19 Giga Drain | nothing (Cut trees inside) | Cut |
| 13 | Fuchsia | `JANINE_JANINE` | Soul | TM84 Poison Jab | nothing | invisible walls, disguised trainers |
| 14 | Saffron | `SABRINA_SABRINA` | Marsh | TM48 Skill Swap | nothing (Saffron needs power restored) | teleport pads |
| 15 | Cinnabar (in Seafoam) | `BLAINE_BLAINE` | Volcano | TM50 Overheat | nothing | trainers block the path |
| 16 | Viridian | `BLUE_BLUE` | Earth | TM92 Trick Room | old man at the door until 7 Kanto badges | spin tiles |

The TM flag is always `FLAG_GOT_TMxx_FROM_<LEADER>`.

Johto order: the story forces Falkner → Bugsy → Whitney → Morty (Surf). Chuck,
Jasmine and Pryce can be done in any order. Clair needs the Radio Tower, which needs
all four middle badges. Kanto is open in any order except Misty and Blue; the
eight Johto badges are only needed indirectly, because you reach Kanto after the
League.

## Puzzle code

The `*gyminit` script commands (`src/data/fieldmap/script_cmd_table.h:320-337`)
reset one shared save slot, `Gymmick` (`include/gymmick.h`), in
`src/gymmick_init.c`. `src/gymmick_collision.c:45-77` picks per-gym init, free and
collision code in `src/field/gymmick/<gym>.c`. Only one gym's state is kept at a
time, so it is reset each time you enter.

Goldenrod, Olivine, Pewter, Cerulean, Celadon, Saffron, Cinnabar and Mahogany have
no gymmick code. Mahogany's ice is presumably tile behavior in its layouts (not
verified).

## Johto gyms

### Violet: Falkner

- **On win** (`Violet_Gym:84-92`):
  - `VAR_SCENE_VIOLET_CITY_OW = 1`: Elm calls when you leave (Violet's frame script
    sets it to 2), then his aide waits in the Violet Mart.
  - `VAR_SCENE_ELMS_LAB = 6` (see [the Elm's Lab table](story-progression.md#prof-elm-var_scene_elms_lab)).
  - `FLAG_HIDE_WIFI_CLUB_CLOSED_LADY` set: the lady saying the Wi-Fi Club is closed
    leaves the Pokémon Centers.
  - `FLAG_UNK_192`, `FLAG_UNK_0F4`: set here, read nowhere.
  - With the TM: clears `FLAG_HIDE_NEW_BARK_FRIENDS_ROOM_FRIEND`.
- **Gate:** none. A gym guide stands on the elevator until Sprout Tower is done.
  `SproutTower_3F:154` sets `FLAG_HIDE_VIOLET_GYM_GYM_GUY_AFTER_SPROUT` and clears
  `…_BEFORE_SPROUT`. The two names are the wrong way round.
- **Puzzle:** `violetgyminit`; a coord event at (15,20) runs `violetgymelevator`
  (`src/field/gymmick/violet.c`).
- **Rematch:** hidden on Wednesday if his number is registered, on Monday if not
  and you have the Soul Badge.

### Azalea: Bugsy

- **On win:** only `settrainerflag` on the four gym trainers.
- **Gate:** a Rocket grunt in Azalea at (405,472), right below the door, has
  `FLAG_UNK_1A9`. Beating Proton in Slowpoke Well sets it (`SlowpokeWell_B1F:70`).
  The gym is reached through `Azalea_Gym_Entrance`, which only has a guide and a sign.
- **Puzzle:** `azaleagyminit` places the Spinarak carts. Twelve coord events call
  `azaleagymspinarak(0..11)`; the two switches call `azaleagymswitch(0/1)`
  (`src/field/gymmick/azalea.c`).
- **Rematch:** after `FLAG_GAME_CLEAR`. Hidden on Thursday (not registered) or
  Monday, Wednesday and Friday (registered).

### Goldenrod: Whitney

The badge takes two steps, because Whitney cries after the battle.

1. **Battle won** (`Goldenrod_Gym:77-102`): trainers set as beaten, Lass Cathy
   moves to (13,15), `VAR_UNK_410A = 1`, `FLAG_UNK_084` set, `VAR_UNK_40DA = 1`
   (Goldenrod NPC lines and the Route 35 Pokéathlon gate), and the Pokéathlon gate
   NPCs swap (`FLAG_HIDE_PARK_SOUTH_GATE_POKEATHLON_ENTHUSIASTS_UNLOCKED` / `_LOCKED`).
2. **Cathy:** a coord event at (13,11) with `VAR_UNK_410A == 1` sets `FLAG_UNK_0B7`.
3. **Badge:** talking to Whitney with `FLAG_UNK_0B7` set gives the badge,
   `VAR_UNK_410A = 2`, clears `FLAG_UNK_084`, sets `FLAG_UNK_998` (`:104-117`).

The Plain Badge opens the SquirtBottle at the Flower Shop, which is needed to get
past Sudowoodo on Route 36.

- **Rematch:** after game clear. Hidden 12:00-15:59 (not registered) or 18:00-20:59.

### Ecruteak: Morty

- **On win** (`Ecruteak_Gym:136-139`): `addvar(VAR_MIDGAME_BADGES, 1)`,
  `FLAG_UNK_998`. No `settrainerflag`; the gym trainers are fought normally.
- **Gate:** `VAR_UNK_4079`. While it is 0 the gym's frame script runs `OldManScene`:
  an old man (`FLAG_UNK_247`) walks over, sets the var to 1 and you are warped
  outside; Ecruteak's frame script sets it back to 0. `BurnedTower_B1F:134`, after
  the legendary beasts flee, sets it to 2 and sets `FLAG_UNK_247`. Later values are
  story, not the gym: 3 (Elm's lab after the Rising Badge), 4 (Ecruteak rival scene).
- **Puzzle:** an invisible path in the dark. `ecruteakgyminit` resets the four candles;
  `src/field/gymmick/ecruteak.c` sets up fog and candles. Fifteen coord events
  (`VAR_UNK_4109 == 0`) run `WarpToEcruteakGym`, which spins you back to the start.
  Each Medium's candle goes out when she is beaten; the hooks are in the generic
  trainer script (`scr_seq_0953.s:1530, 1730-1746`).
- **Rematch:** after game clear. Hidden Monday-Tuesday (not registered) or Friday.

### Cianwood: Chuck

- **On win** (`Cianwood_Gym:57-71`): trainers beaten, `addvar(VAR_MIDGAME_BADGES, 1)`,
  `VAR_UNK_4116 = 1` (Chuck's wife gives HM02 Fly outside, which sets it to 2), and
  `VAR_SCENE_ROCKET_TAKEOVER = 1` if `VAR_MIDGAME_BADGES == 3`.
- **Gate:** none in the gym.
- **Puzzle:** `OnTransition` runs `cianwoodgyminit` and clears
  `FLAG_SYS_CIANWOOD_WATERFALL_DISABLE`. Chuck ignores you while `VAR_TEMP_x4000 == 0`.
  The winch sign sets `FLAG_SYS_CIANWOOD_WATERFALL_DISABLE` (which silences the
  waterfall, `src/field/field_control.c:1070`) and runs `cianwoodgymturnwinch`.
  The winch resets on every visit, even after the badge.
- **Rematch:** no hide logic; `FLAG_HIDE_CIANWOOD_GYM_CHUCK` is never set.

### Olivine: Jasmine

- **On win** (`Olivine_Gym:216-221`): `addvar(VAR_MIDGAME_BADGES, 1)`, and
  `VAR_SCENE_ROCKET_TAKEOVER = 1` if it is 3. No gym trainers.
- **Gate:** `init` sets `FLAG_HIDE_JASMINE_IN_GYM`, `FLAG_HIDE_OLIVINE_GYM_GENTLEMAN`
  and `FLAG_HIDE_OLIVINE_GYM_GIRL`. Giving the SecretPotion to Amphy
  (`Olivine_LighthouseLightRoom:92-100`) clears all three and sets
  `VAR_SCENE_LIGHTHOUSE_JASMINE = 2`, `VAR_UNK_410E = 1` and `FLAG_UNK_998`.
- **Puzzle:** none. `VAR_UNK_410E` (1 → 2 → 3) only drives dialogue triggers.
- **Rematch:** after game clear. Hidden at 13:00 (not registered) or 12:00, and
  also 14:00-16:59 on weekends if Erika isn't registered and you have the Earth
  Badge. Registered, she trades a Steelix (`FLAG_TRADE_JASMINE_STEELIX`).

### Mahogany: Pryce

Three maps: `Mahogany_GymRoom1` (guide), `Mahogany_GymRoom2` (no scripts),
`Mahogany_GymLeaderRoom` (Pryce).

- **On win** (`Mahogany_GymLeaderRoom:116-152`): trainers beaten,
  `addvar(VAR_MIDGAME_BADGES, 1)`, `VAR_SCENE_ROCKET_TAKEOVER = 1` if it is 3.
- **Gate:** a man at Mahogany (523,184), below the door, has `FLAG_UNK_1F9`. Clearing
  the Rocket Hideout sets it (`TeamRocketHeadquarters_B2F:733`).
- **Puzzle:** ice floor; no script or gymmick code found.
- **Rematch:** after game clear, not registered: hidden 06:00-09:59. Skipped while
  `FLAG_UNK_189` is set, which guards Cameron's photo (Pryce sets it, runs
  `cameronphoto(40)`, clears it).

### Blackthorn: Clair

The badge is not given in the gym.

1. **Battle won** (`Blackthorn_Gym:114-122`): trainers beaten, `FLAG_UNK_0D1`
   ("beaten, go to the Den"), and the Dragon's Den guard steps aside
   (`FLAG_HIDE_BLACKTHORN_DEN_GUARD_INFRONT` set, `FLAG_HIDE_BLACKTHRON_DEN_GUARD_ASIDE`
   cleared; the constant really is spelled `BLACKTHRON`).
2. **Dragon's Den shrine quiz** (`DragonsDen_Shrine:168-224`): `givebadge(BADGE_RISING)`,
   `FLAG_UNK_998`, `FLAG_UNK_0EA`, `VAR_UNK_40C3/40C4/407B = 1`,
   `VAR_SCENE_ELMS_LAB = 8`, `VAR_SCENE_NEW_BARK_EAST_EXIT = 1`, and clears
   `FLAG_HIDE_VICTORY_ROAD_CLAIR`.
3. **TM:** with `FLAG_UNK_0EA` set, Clair gives TM59 (`Blackthorn_Gym:58-70`).

- **Gate:** a guard in front of the door (`FLAG_HIDE_BLACKTHORN_GYM_GUARD_INFRONT`).
  Beating Archer on the Radio Tower deck (`Goldenrod_RadioTowerObservationDeck:180`)
  hides him and shows the guard standing aside. Getting to Blackthorn also needs
  Route 44, which opens at the same time (`VAR_UNK_407A`).
- **Puzzle:** `blackthorngyminit` places three platforms (`gymmick_init.c:104`);
  switches move and turn them (`src/field/gymmick/blackthorn.c`, called from
  `field_control.c:633`). Three coord events (`VAR_UNK_4111 == 0`) catch falls and
  warp you back. The guide trigger (`VAR_UNK_4120`, once via `FLAG_UNK_138`)
  recalls your following Pokémon.
- **Rematch:** only once `VAR_UNK_40FC >= 2` (post-game Dragon's Den). Hidden
  06:00-09:59 (not registered) or 16:00-18:59.

## Kanto gyms

Every Kanto leader runs `addvar(VAR_UNK_4135, 1)` in addition to the badge.

### Pewter: Brock

- **On win:** `VAR_UNK_4135 + 1`, two trainers beaten.
- **Gate, puzzle:** none.
- **Rematch:** hidden 12:00-14:59 (not registered, with the Earth Badge) or 17:00-19:59.

### Cerulean: Misty

- **On win** (`Cerulean_Gym:215-232`): `VAR_UNK_4135 + 1`, trainers beaten. If
  `FLAG_UNK_14D` is set (Suicune already seen on Route 14), shows Suicune on
  Route 25 (`FLAG_HIDE_ROUTE_25_SUICUNE` cleared, `VAR_SCENE_ROUTE_25 = 1`).
- **Gate:** Misty and every gym NPC have `FLAG_HIDE_CERULEAN_GYM_POPULATION`, set
  by `init`. It is cleared by the Power Plant chain:
  1. The Power Plant manager's story, then the policeman
     (`Route10_PowerPlantBroken:104-133`): shows the Rocket in the gym,
     `VAR_UNK_411C = 1`.
  2. The gym's frame script (`VAR_UNK_411C == 1`, `Cerulean_Gym:54-98`): the grunt
     flees. `VAR_UNK_411C = 2`, `VAR_SCENE_ROUTE_24_ROCKET = 1`, `VAR_UNK_4088 = 1`,
     Misty and her date appear on Route 25.
  3. Route 25 (`VAR_UNK_4088 == 1`, `Route25:72-135`): Misty goes back; clears
     `FLAG_HIDE_CERULEAN_GYM_POPULATION`, `VAR_UNK_4088 = 2`.
- **Puzzle:** none. The Machine Part is hidden in the gym
  (`FLAG_HIDE_CERULEAN_GYM_MACHINE_PART`, revealed by the Route 24 grunt).
- **Rematch:** with the Earth Badge and `VAR_SCENE_ROUTE_25` not 1 or 2: everyone is
  hidden 16:00-17:59 (not registered) or 14:00-15:59.

### Vermilion: Lt. Surge

- **On win** (`Vermilion_Gym:310-322`): `VAR_UNK_4135 + 1`, sets
  `FLAG_HIDE_VERMILION_GYM_STOPS` (removes the six invisible barriers), trainers beaten.
- **Gate:** none.
- **Puzzle:** trash cans. `OnTransition` clears `FLAG_SYS_SOLVED_LT_SURGE_GYM` unless
  the barriers are gone, then runs `vermiliongyminit` (`gymmick_init.c:56-82`): with
  the Thunder Badge both gates open; otherwise it picks a random first can and a
  random neighbor of it from `sTrashCans` (15 cans). Each can calls
  `vermiliongymcancheck(n)` (`src/field/gymmick/vermilion.c:63`):

  | Result | Meaning | Script then |
  |---:|---|---|
  | 0 | nothing | |
  | 1 | first switch | `vermiliongymlockaction(0, 0)` |
  | 2 | second switch | `vermiliongymlockaction(1, 0)`, `setflag(FLAG_SYS_SOLVED_LT_SURGE_GYM)` |
  | 3 | wrong second can | `vermiliongymlockaction(0, 1)`, `resamplevermiliongymcans` |
  | 4 | already solved | |

  `FLAG_SYS_SOLVED_LT_SURGE_GYM` also silences the barrier hum
  (`field_control.c:1070`).
- **Rematch:** always there until `FLAG_CAUGHT_ZAPDOS`. Then hidden 09:00-11:59 (not
  registered), or when registered hidden unless `FLAG_TRADE_LT_SURGE_PIKACHU` is
  set, and also on Friday and Saturday.

### Celadon: Erika

- **On win:** `VAR_UNK_4135 + 1`, trainers beaten.
- **Gate:** none. Three Cut trees inside (`std_field_cut`, `FLAG_MAPTEMP_010-012`,
  so they grow back when you leave).
- **Rematch:** hidden 14:00-16:59 on weekends (not registered, with the Earth Badge),
  or Monday.

### Fuchsia: Janine

- **On win** (`Fuchsia_Gym:394-409`): `VAR_UNK_4135 + 1`, trainers beaten.
- **Gate:** none.
- **Puzzle:**
  - Invisible walls: `fuchsiagyminit`; bumping one calls
    `FuchsiaGymmick_CheckCollision` (`src/player_avatar_movement.c:686`,
    `src/field/gymmick/fuchsia.c`).
  - Four trainers dressed as Janine have paired flags
    `FLAG_HIDE_FUCHSIA_GYM_<T>_DISGUISED` / `_REVEALED` (`init` sets the `_REVEALED`
    ones). Talking to one swaps them; losing swaps them back.
  - `VAR_TEMP_x400B` is 111 during Janine's battle; `OnLoad` uses it to reveal the
    trainers you haven't beaten when the map reloads.
- **Rematch:** hidden 16:00-17:59 (not registered, with the Soul Badge) or 18:00-19:59.

### Saffron: Sabrina

- **On win:** `VAR_UNK_4135 + 1`, `FLAG_UNK_998`, trainers beaten.
- **Gate:** none in the gym; Saffron itself needs power restored (the gatehouses
  check `FLAG_RESTORED_POWER`).
- **Puzzle:** teleport pads are plain warps: 30 of the 31 `warp_events` in
  `Saffron_Gym/map.json` lead back into the gym. One coord event at (12,17) runs
  `WarpToSaffronGym`. No gymmick code.
- **Rematch:** hidden Friday (not registered, with the Marsh Badge) or Monday.

### Cinnabar: Blaine

The gym is a room in Seafoam Islands (`SeafoamIslandsCinnabarGym`, one warp to
`MAP_SEAFOAM_ISLANDS_1F`).

- **On win** (`SeafoamIslandsCinnabarGym:96-104`): `VAR_UNK_4135 + 1`,
  `FLAG_UNK_265` (hides four objects on Route 19), Route 19 reopens
  (`FLAG_HIDE_ROUTE_19_WORKMEN_CLOSED` set, `…_OPEN` cleared), and `FLAG_UNK_13C`,
  `13F`, `140` (three gym trainers' "beaten" flags).
- **Gate:** none.
- **Puzzle:** six trainers stand in the way; each has its own flag (Cary `FLAG_UNK_13B`,
  Waldo `13C`, Merle `13D`, Lowell `13E`, Linden `13F`, Daniel `140`). `OnResume`
  moves Cary, Merle and Lowell aside once theirs is set.
- **Rematch:** hidden Tuesday (not registered, with the Earth Badge) or Thursday.

### Viridian: Blue

- **On win** (`Viridian_Gym:71-82`): `VAR_UNK_4135 + 1`, `FLAG_UNK_998`, trainers
  beaten, `FLAG_UNK_97F` (read nowhere), Zapdos appears (`FLAG_HIDE_ROUTE_10_ZAPDOS`
  cleared), the man blocking Cerulean Cave leaves
  (`FLAG_HIDE_CERULEAN_CITY_MAN_OUTSIDE_CAVE` set), and `VAR_UNK_4096 = 1` (Oak
  calls, then gives HM08 Rock Climb and opens Mt. Silver).
- **Gate:** an old man below the door (`FLAG_HIDE_VIRIDIAN_CITY_OLD_MAN_OUTSIDE_GYM_LOCKED`).
  Talking to Blue on Cinnabar Island with `VAR_UNK_4135 >= 7` (`CinnabarIsland:99-136`)
  hides him and shows `…_UNLOCKED`.
- **Puzzle:** spin tiles. `viridiangyminit`; `ViridianGymmick_HandleTileAction` is
  called from `src/field/spin_slide.c:104` and `field_control.c:636`. The guide
  trigger (`VAR_UNK_4127`, once via `FLAG_UNK_13A`) recalls your following Pokémon.
- **Rematch:** only after Red is beaten (`VAR_UNK_40FD != 0`); then hidden Friday.
  Ace Trainer Arabella also uses `FLAG_HIDE_VIRIDIAN_GYM_BLUE`.

## Changing gyms

| I want to... | Do this |
|---|---|
| change a leader's team | the `TRAINER_LEADER_*` entry in `files/poketool/trainer/trainers.json`; rematch teams are the `_2` entries |
| change the TM | the `itemspace`/`std_give_item_verbose` lines and the text in the leader script; keep the `FLAG_GOT_TM…` flag |
| change which badge an HM needs | `src/field_move.c` **and** the matching `std_field_*` script in `scr_seq_0146.s`; Surf also in `field_control.c:610` |
| let gyms be done in any order | remove the door blockers listed above (or their hide flags in `init`), make obedience count badges, and check `VAR_MIDGAME_BADGES` still reaches 4 for the Radio Tower |
| block the League until 8 badges | the Route 22 gate's `PolicemanTrigger1` only prints "the eight Badges of Johto"; add `countbadges(VAR_TEMP_x4000)` and push the player back if it is under 8 |
| add a gym puzzle | a `*gyminit` command, a case in `src/gymmick_init.c` and `src/gymmick_collision.c`, and code in `src/field/gymmick/` |

## Not verified

- `FLAG_UNK_192`, `FLAG_UNK_0F4` (Falkner), `FLAG_UNK_084` (Whitney) and
  `FLAG_UNK_97F` (Blue) are set but read nowhere found.
- How Mahogany's ice floor is implemented.
- What exactly `FLAG_UNK_265` hides on Route 19, and why Blaine marks only three of
  his trainers beaten.
- Where leaders stand for phone rematches, beyond the `Saffron_FightingDojo` battles.
