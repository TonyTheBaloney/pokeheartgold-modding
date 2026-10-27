<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Static and legendary encounters

> AI-generated; not affiliated with pret. See AI.md at the repository root.

Ho-Oh, Lugia, Suicune, Snorlax, Sudowoodo, the birds, Mewtwo and the rest are
**scripted wild battles**: an overworld object whose script calls `wildbattle`. This
guide covers what that command builds, what happens to the object after the battle, the
full list of them, and the usual changes: making one catchable again, changing its level
or moves, and adding a new one.

Roaming Raikou, Entei, Latios and Latias have their own guide, [roamers.md](roamers.md).
The Sinjoh Ruins Dialga, Palkia and Giratina are gifts (`givemon`), covered in
[gift-pokemon-and-trades.md](gift-pokemon-and-trades.md).

| pokeemerald | here |
|---|---|
| `setwildbattle SPECIES, level` + `dowildbattle` (or `special BattleSetup_StartLegendaryBattle`) | one command: `wildbattle(SPECIES_X, level, shiny)` (`ScrCmd_WildBattle`, `src/scrcmd_c.c:2583`) |
| `setflag FLAG_SYS_CTRL_OBJ_DELETE` around the battle | `setflag(FLAG_ENGAGING_STATIC_POKEMON)` around the battle; the map's **`OnLoad` script** hides the object ([§2](#2-after-the-battle-who-hides-the-pokémon)) |
| `specialvar VAR_RESULT, GetBattleOutcome` + `B_OUTCOME_*` | `getstaticencounteroutcome(VAR)` + `BATTLE_OUTCOME_*` (`include/constants/battle.h:112`), or `checkbattlewon(VAR)` |
| `FLAG_DEFEATED_*` / `FLAG_CAUGHT_*` per legendary | `FLAG_CAUGHT_*` (`include/constants/flags.h`), set only on a catch |
| legendaries don't come back once beaten | most come back each time you enter the Hall of Fame, unless caught ([§3](#3-the-static-encounters)) |
| `BATTLE_TYPE_LEGENDARY` (no running, special music) | nothing stops you running. Music and transition come from the species ([battle-music.md](battle-music.md#wild-battles)) |

## 1. The `wildbattle` command

```
wildbattle(species, level, shiny)
```

- `species` and `level` are each a number **or a variable** (`ScriptGetVar`). Ho-Oh and
  Lugia pass `VAR_TEMP_x400A` and `VAR_SPECIAL_x8004`, set just before by game version.
- `shiny` is a constant byte: 1 forces a shiny. Only the Lake of Rage Gyarados uses it.
  Shiny-locking one takes a code change ([shiny.md §6.4](shiny.md#64-shiny-locked-static-encounters)).
- The level is a `u8`. Nothing checks it against 100.

`SetupAndStartWildBattle` (`src/encounter.c:542`) builds the Pokémon with
`FieldSystem_GenerateSingleWildPokemon` (`src/field/encounter_check.c:992`), the same
code as an ordinary wild Pokémon:

| | How it's set |
|---|---|
| IVs | random (`USE_RANDOM_IVS`). No guaranteed perfect IVs |
| nature | random. A Synchronize lead copies its nature half the time (`getWildMonNature`) |
| gender | random. A Cute Charm lead forces the opposite gender 2 times in 3 |
| moves | the last four level-up moves it knows at that level (`CreateMon`); [§4.3](#43-give-it-other-moves) sets your own |
| held item | the species' wild held items, rolled as usual (`WildMonSetRandomHeldItem`); Compound Eyes raises the chance |
| shiny | the normal 1 in 8192, unless `shiny` is 1 (then `GenerateShinyPersonality`) |
| OT id | yours |

The fifth argument of `SetupAndStartWildBattle` is called `canFlee`, but it doesn't
control running. It sets `BATTLE_SPECIAL_LEGENDARY` (bit 3), and
`subscript_0000_StartEncounter.s` uses that bit only to print message 1246 instead of
965. In English both say "A wild {0} appeared!".

`fatefulwildbattle(species, level)` (command 686) does the same and also sets the
fateful-encounter flag. No retail script uses it.

## 2. After the battle: who hides the Pokémon

Every retail static follows the same pattern. Sudowoodo, slightly trimmed
(`data/maps/Route36/scripts.pory`):

```
script Route36_OnLoad {
    if (flag(FLAG_ENGAGING_STATIC_POKEMON)) {
        setflag(FLAG_HIDE_ROUTE_36_SUDOWOODO)   // gone from now on
        removeobject(obj_R36_usokky)            // and gone right now
        clearflag(FLAG_ENGAGING_STATIC_POKEMON)
        end
    }
    end
}

script Route36_EventScript_Usokky {
    ...
    setflag(FLAG_ENGAGING_STATIC_POKEMON)
    wildbattle(SPECIES_SUDOWOODO, 20, 0)
    clearflag(FLAG_ENGAGING_STATIC_POKEMON)
    checkbattlewon(VAR_SPECIAL_RESULT)
    if (var(VAR_SPECIAL_RESULT) == 0) { goto(_0255) }        // lost: whiteout
    getstaticencounteroutcome(VAR_TEMP_x4001)
    compare(VAR_TEMP_x4001, BATTLE_OUTCOME_MON_CAUGHT)
    callifeq(_023F)                                          // setflag(FLAG_CAUGHT_SUDOWOODO)
    ...
}
```

The object is not hidden by the event script but by the map's **`OnLoad`** script
(`INIT_SCRIPT_ON_LOAD`). Here is the order of events:

1. The script sets `FLAG_ENGAGING_STATIC_POKEMON` (0xA4) and calls `wildbattle`.
2. After the battle, `Task_StartEncounter` (`src/encounter.c:135`) stores the outcome in
   the script's result and in `VAR_BATTLE_RESULT` (0x4013), through
   `Encounter_GetResult`.
3. **If you won, caught it or ran away**, it rebuilds the overworld
   (`CallTask_RestoreOverworld`). That runs the map's `OnLoad` script, which sees the
   flag and hides the Pokémon.
4. **If you lost (or drew)**, it returns without rebuilding the overworld, so `OnLoad`
   doesn't run and the Pokémon stays. The event script must then `whiteout`, as every
   retail script does.
5. The event script resumes, clears the flag and checks the outcome.

So in the original game, knocking it out or **running away** removes the Pokémon just as
catching it does. Only a loss leaves it there.

### Outcomes

`BATTLE_OUTCOME_*` (`include/constants/battle.h:112`). These are the values
`getstaticencounteroutcome` gives and `VAR_BATTLE_RESULT` holds:

| Value | Name | When | Overworld rebuilt (OnLoad runs)? |
|---|---|---|---|
| 1 | `BATTLE_OUTCOME_WIN` | you knocked it out | yes |
| 2 | `BATTLE_OUTCOME_LOSE` | you whited out | **no** |
| 3 | `BATTLE_OUTCOME_DRAW` | both sides fainted at once (Explosion, Destiny Bond) | **no** (counts as a loss) |
| 4 | `BATTLE_OUTCOME_MON_CAUGHT` | caught | yes |
| 5 | `BATTLE_OUTCOME_PLAYER_FLED` | you ran, or it fled (Roar, Teleport, its own escape) | yes |

Running and the wild Pokémon fleeing both give 5 (`BATTLE_RESULT_PLAYER_FLED` in
`subscript_0003_RunAway.s` and `subscript_0230_RunAwayWildMon.s`).

### The result commands

Two of these have names that say the opposite of what they return:

| Command | Gives |
|---|---|
| `checkbattlewon(VAR)` | 0 after a loss or draw, otherwise 1 (`IsBattleResultWin`) |
| `getstaticencounteroutcome(VAR)` | the outcome number above |
| `staticwildwonorcaughtcheck(VAR, 0)` | **TRUE when you did *not* win or catch it** (ran or lost); `IsBattleResultStaticWildWin`, `src/battle/battle_setup.c:550`. With 1 instead of 0 it reads `VAR_BATTLE_RESULT`, which works in an `OnLoad` script |
| `laticaughtcheck(VAR)` | **TRUE when it was *not* caught** (`IsBattleResultLatiCaught`, `:560`) |

`VAR_BATTLE_RESULT` keeps the last outcome, so an `OnLoad` script can look at it
directly. The Team Rocket HQ Electrodes do exactly this: they are removed only if you
won or caught them (`TeamRocketHeadquarters_B2F_OnLoad`).

## 3. The static encounters

All 21 `wildbattle` calls in the game. "Back after Hall of Fame" means that, unless it was
caught, `PokemonLeagueHallOfFame_OnLoad` (`data/maps/PokemonLeagueHallOfFame/scripts.pory`,
around line 80) clears its hide flag each time you enter the Hall of Fame.

| Pokémon | Map (`data/maps/<map>/scripts.pory`) | Level | Hidden by | Caught flag | Back after Hall of Fame |
|---|---|---|---|---|---|
| Ho-Oh | `BellTowerRoof` | HG 45, SS 70 | `FLAG_HIDE_BELL_TOWER_HO_OH` | `FLAG_CAUGHT_HO_OH` | yes |
| Lugia | `WhirlIslands_B3F_LugiaCave` | HG 70, SS 45 | `FLAG_HIDE_WHIRL_ISLAND_LUGIA` (and five invisible `SPRITE_STOP` blockers) | `FLAG_CAUGHT_LUGIA` | yes |
| Suicune | `Route25` | 40 | `FLAG_HIDE_ROUTE_25_SUICUNE` | `FLAG_CAUGHT_SUICUNE` | no: the Burned Tower one comes back instead (if `VAR_SCENE_ROUTE_25` is 3) |
| Suicune | `BurnedTower_B1F` | 40 | `FLAG_HIDE_BURNED_TOWER_STATIC_SUICUNE` | `FLAG_CAUGHT_SUICUNE` | yes |
| Snorlax | `Route11` | 50 | `FLAG_HIDE_ROUTE_11_SNORLAX` | `FLAG_CAUGHT_SNORLAX` | no: the Route 12 one appears instead (if `FLAG_SNORLAX_MEET`) |
| Snorlax | `Route12` | 50 | `FLAG_HIDE_ROUTE_12_SNORLAX` (set at New Game) | `FLAG_CAUGHT_SNORLAX` | yes, once `FLAG_SNORLAX_MEET` is set |
| Sudowoodo | `Route36` (two calls) | 20 | `FLAG_HIDE_ROUTE_36_SUDOWOODO` | `FLAG_CAUGHT_SUDOWOODO` | yes |
| Red Gyarados | `LakeOfRage` | 30, shiny | `FLAG_HIDE_LAKE_OF_RAGE_RED_GYARADOS` | `FLAG_CAUGHT_RED_GYARADOS` | yes |
| Lapras | `Union_Cave_B2F` | 20 | `FLAG_HIDE_UNION_CAVE_LAPRAS` | `FLAG_DAILY_CAUGHT_LAPRAS` (a daily flag, set after any outcome but a loss) | no; it is there every Friday (`OnTransition`) |
| Electrode ×3 | `TeamRocketHeadquarters_B2F` | 23 | `FLAG_HIDE_ROCKET_HIDEOUT_B3F_ELECTRODE_*`, only if won or caught | none | no |
| Zapdos | `Route10` | 50 | `FLAG_HIDE_ROUTE_10_ZAPDOS` | `FLAG_CAUGHT_ZAPDOS` | yes, with the Earth Badge |
| Articuno | `SeafoamIslands_B4F` | 50 | `FLAG_HIDE_SEAFOAM_ISLAND_ARTICUNO` | `FLAG_CAUGHT_ARTICUNO` | yes |
| Moltres | `MountSilver_CaveMoltresChamber` | 50 | `FLAG_HIDE_MT_SILVER_CAVE_MOLTRES` | `FLAG_CAUGHT_MOLTRES` | yes |
| Mewtwo | `Cerulean_Cave_B1F` | 70 | `FLAG_HIDE_CERULEAN_CAVE_MEWTWO` | `FLAG_CAUGHT_MEWTWO` | yes |
| Latios (HG) / Latias (SS) | `Pewter` (needs the Enigma Stone) | 40 | `FLAG_HIDE_PEWTER_CITY_LATIOS` / `_LATIAS` | none (`laticaughtcheck`) | no |
| Groudon (SS) / Kyogre (HG) | `EmbeddedTowerGroudonRoom` / `EmbeddedTowerKyogreRoom` | 50 | `FLAG_HIDE_EMBEDDED_TOWER_GROUDON` / `_KYOGRE`; `OnTransition` keeps it hidden once `FLAG_BEAT_OR_ESCAPED_FROM_GROUDON_OR_KYOGRE` is set | `FLAG_CAUGHT_GROUDON` / `FLAG_CAUGHT_KYOGRE` | yes (the Hall of Fame clears `FLAG_BEAT_OR_ESCAPED_...`) |
| Rayquaza | `EmbeddedTowerRayquazaRoom` | 50 | `FLAG_HIDE_EMBEDDED_TOWER_RAYQUAZA` | `FLAG_CAUGHT_RAYQUAZA` | yes |

The Snorlax on Route 11 and Route 12 only fight while the Poké Flute channel is playing
(`radiomusicisplaying(5, ...)`); otherwise they are asleep. Sudowoodo needs the
Squirtbottle, Ho-Oh and Lugia need the Kimono Girls' dance. Those conditions are in each
script, before the battle.

To find every use yourself: `grep -rn 'wildbattle(' data/maps`, or
`tools/mapkit/mapkit.sh refs FLAG_ENGAGING_STATIC_POKEMON`.

## 4. Recipes

These recipes were built together with `make release` on HeartGold US, then reverted
(all 4 checksums OK afterwards). They were **not play-tested**; see
[Not verified](#not-verified).

### 4.1 Catchable again after a loss, a knockout or running away

**After a loss** it's already catchable: the overworld isn't rebuilt, so the Pokémon is
still there once you're back from the Pokémon Center (Ho-Oh and Lugia even clear their
hide flag again on that path, which isn't needed). Knocking it out and running away are
the cases that remove it. There are three ways to bring it back.

**a) It stays until it's caught** (built). Make `OnLoad` hide it only on a catch. Ho-Oh
(`data/maps/BellTowerRoof/scripts.pory`):

```
raw `
#include "constants/battle.h"
`

script BellTowerRoof_OnLoad {
    if (flag(FLAG_ENGAGING_STATIC_POKEMON)) {
        clearflag(FLAG_ENGAGING_STATIC_POKEMON)
        if (var(VAR_BATTLE_RESULT) == BATTLE_OUTCOME_MON_CAUGHT) {
            setflag(FLAG_HIDE_BELL_TOWER_HO_OH)
            removeobject(obj_D17R0110_hou_obj01)
        }
        end
    }
    end
}
```

The `raw` block makes `BATTLE_OUTCOME_*` visible to the script (map scripts don't
include `constants/battle.h` by default; `Route36` already has the same block). After a
knockout or an escape Ho-Oh is still standing there, and talking to it starts the battle
again. Two things to check on each map:

- **What the event script does after a knockout.** Ho-Oh's sets story flags (Kimono
  Girls, New Bark Town) each time; setting them again is harmless. Sudowoodo's opens the
  road and gives the Berry Pots: with this change the tree would still block the road
  after a knockout, so keep the original behavior there, or test for
  `BATTLE_OUTCOME_PLAYER_FLED` only.
- **Every object the original removes.** Lugia's `OnLoad` also removes five `SPRITE_STOP`
  blockers. Put them inside the same `if`.

**b) It comes back the next time you enter the map** (not built). Keep `OnLoad` as it
is, and in the event script, after the battle, clear the hide flag unless it was caught:

```
    getstaticencounteroutcome(VAR_TEMP_x4005)
    if (var(VAR_TEMP_x4005) != BATTLE_OUTCOME_MON_CAUGHT) {
        clearflag(FLAG_HIDE_BELL_TOWER_HO_OH)
    }
```

`OnLoad` has already removed the object for this visit, so it only reappears after a
warp. This is the same idea as the Hall of Fame list, but without waiting.

**c) It comes back after the Hall of Fame.** This is the retail behavior for most of them.
To add one, or one the list misses (Route 25 Suicune, the Electrodes, the Latis), add
three lines to `PokemonLeagueHallOfFame_OnLoad`, after the others:

```
    if (!flag(FLAG_CAUGHT_TYRANITAR)) {
        clearflag(FLAG_HIDE_ROUTE_45_TYRANITAR)
    }
```

A static without a caught flag of its own (the Electrodes, the Latis) needs one first:
set it in the event script when `getstaticencounteroutcome` gives 4.

### 4.2 Change its level

Change the number in `wildbattle`. For Ho-Oh and Lugia it is the
`setvar(VAR_SPECIAL_x8004, ...)` pair just before, one value per version
(`getgameversion` gives 7 for HeartGold and 8 for SoulSilver).

Since `level` can be a variable, a script can compute it. For example, to use the
level that a scaling rule from [level-scaling.md](level-scaling.md) puts in
`VAR_SPECIAL_x8004`:

```
    wildbattle(SPECIES_SUDOWOODO, VAR_SPECIAL_x8004, 0)
```

To scale **every** scripted wild battle in C instead, apply the rule in
`FieldSystem_GenerateSingleWildPokemon` (`src/field/encounter_check.c:992`). Only
`wildbattle`, `fatefulwildbattle`, the Rocket trap battles (`rockettrapbattle`) and
`startfirstbattle` (`SetupAndStartFirstBattle`) use it
([level-scaling.md](level-scaling.md#wild-pokémon)).

### 4.3 Give it other moves

No command sets moves, so this recipe adds one, `setwildmonmoves`. A script uses it on
the line before `wildbattle`:

```
    setwildmonmoves(MOVE_SACRED_FIRE, MOVE_BRAVE_BIRD, MOVE_EARTHQUAKE, MOVE_RECOVER)
    setflag(FLAG_ENGAGING_STATIC_POKEMON)
    wildbattle(VAR_TEMP_x400A, VAR_SPECIAL_x8004, 0)
```

The four moves replace the level-up moves for **the next** `wildbattle` only, and are
then forgotten. `MOVE_NONE` leaves a slot empty. If the first move is `MOVE_NONE`,
nothing changes. Each argument can also be a variable.

Five files, following [script-commands.md](script-commands.md#6-adding-a-command).

**1. `src/encounter.c`**, just above `SetupAndStartWildBattle`:

```c
// Moves for the next scripted wild Pokémon (setwildmonmoves); all MOVE_NONE = its level-up moves
static u16 sNextWildMonMoves[MAX_MON_MOVES];

void Encounter_SetNextWildMonMoves(u16 move1, u16 move2, u16 move3, u16 move4) {
    sNextWildMonMoves[0] = move1;
    sNextWildMonMoves[1] = move2;
    sNextWildMonMoves[2] = move3;
    sNextWildMonMoves[3] = move4;
}

static void ApplyNextWildMonMoves(BattleSetup *setup) {
    Pokemon *mon = Party_GetMonByIndex(setup->party[BATTLER_ENEMY], 0);
    if (sNextWildMonMoves[0] == MOVE_NONE) {
        return;
    }
    for (int i = 0; i < MAX_MON_MOVES; i++) {
        MonSetMoveInSlot(mon, sNextWildMonMoves[i], i);
        sNextWildMonMoves[i] = MOVE_NONE;
    }
}
```

and in `SetupAndStartWildBattle`, after the Pokémon is made:

```c
    FieldSystem_GenerateSingleWildPokemon(fieldSystem, species, level, shiny, setup);
    ApplyNextWildMonMoves(setup);
```

`MonSetMoveInSlot` (`src/pokemon.c:3131`) also sets each move's PP to its maximum. Add
the same call to `SetupAndStartFatefulWildBattle` if you use that command.

**2. `include/encounter.h`**, after `SetupAndStartWildBattle`:

```c
void Encounter_SetNextWildMonMoves(u16 move1, u16 move2, u16 move3, u16 move4);
```

**3. `src/scrcmd_c.c`**, next to `ScrCmd_WildBattle` (the file already includes
`encounter.h`):

```c
BOOL ScrCmd_SetWildMonMoves(ScriptContext *ctx) {
    u16 move1 = ScriptGetVar(ctx);
    u16 move2 = ScriptGetVar(ctx);
    u16 move3 = ScriptGetVar(ctx);
    u16 move4 = ScriptGetVar(ctx);
    Encounter_SetNextWildMonMoves(move1, move2, move3, move4);
    return FALSE;
}
```

**4.** Declare it at the end of `include/scrcmd.h`
(`BOOL ScrCmd_SetWildMonMoves(ScriptContext *ctx);`) and append `ScrCmd_SetWildMonMoves,`
to the end of `gScriptCmdTable` in `src/data/fieldmap/script_cmd_table.h`. That makes it
command 853, if no other recipe has taken that number.

**5. `asm/macros/script.inc`**, after `BufferDeptStoreFloorNo`:

```
	// Gives the next wildbattle Pokémon these four moves (MOVE_NONE for an empty slot)
	.macro SetWildMonMoves move1, move2, move3, move4
	.short 853
	.short \move1
	.short \move2
	.short \move3
	.short \move4
	.endm
```

Then regenerate the command list:
`python3 tools/scriptcmds/scriptcmds.py --markdown > docs/modding/script-commands-list.md`.

The same pattern works for IVs or a held item: store them next to the moves, and in
`ApplyNextWildMonMoves` set `MON_DATA_HP_IV + i` or `MON_DATA_HELD_ITEM` with
`SetMonData`. After changing IVs, call `CalcMonLevelAndStats(mon)` so the stats match.
`givecustommon` in [gift-pokemon-and-trades.md](gift-pokemon-and-trades.md#3-custom-gifts-givecustommon)
shows each field. All of this goes in the static ARM9 (`encounter.c` and `scrcmd_c.c`
are in `main.lsf`'s `Static main` block), where space is tight, so keep it small.

### 4.4 Add a new one

A Tyranitar, level 55, on Route 45, that hides when beaten and comes back after the Hall
of Fame unless caught. You need two flags, an overworld object with a sprite, an event
script and an `OnLoad` script.

**1. Two flags.** `0x31C` and `0x31D` are free, in the hide-flag block
([unknown-flags-vars.md](unknown-flags-vars.md#free-flags)). In
`include/constants/flags.h`, rename them:

```c
#define FLAG_HIDE_ROUTE_45_TYRANITAR                              0x31C
#define FLAG_CAUGHT_TYRANITAR                                     0x31D
```

A clear hide flag means the object is visible, so this Tyranitar is there from the start
of the game. To make it appear later, set the flag at New Game (in the `init` script,
[new-game.md §3](new-game.md#3-starting-flags-items-money-and-pokémon)) and clear it from
the story script that should reveal it.

**2. A sprite.** Statics use `SPRITE_FOLLOWER_MON_STATIC_<SPECIES>`: the follower texture
under a second sprite id, outside the follower range (994-1049), so it is drawn as an
ordinary object. Retail has 56 of them, for the species that appear as objects:

> Butterfree, Pidgey, Rattata, Spearow, Fearow, Pikachu, Nidoran♀, Nidoran♂, Nidorino,
> Clefairy, Jigglypuff, Zubat, Oddish, Diglett, Meowth, Persian, Psyduck, Poliwrath,
> Abra, Machop, Machoke, Slowpoke, Slowbro, Farfetch'd, Dodrio, Electrode, Rhydon,
> Chansey, Kangaskhan, Lapras, Articuno, Zapdos, Moltres, Dratini, Dragonite, Mewtwo,
> Bayleef, Ampharos, Marill, Aipom, Murkrow, Miltank, Blissey, Raikou, Entei, Suicune,
> Celebi, Latias, Latios, Kyogre, Groudon, Rayquaza, Spiky-eared Pichu, Meganium,
> Typhlosion, Feraligatr

Ho-Oh, Lugia, Snorlax and Sudowoodo have their own large sprites (`SPRITE_HOU_OBJ01`,
`SPRITE_LUG_OBJ01`, `SPRITE_KABIGON`, `SPRITE_USOKKY`).

Tyranitar has none, so add it. It needs no new texture, only two lines. In
`include/constants/sprites.h`, after `SPRITE_FOLLOWER_MON_STATIC_FERALIGATR`:

```c
#define SPRITE_FOLLOWER_MON_STATIC_TYRANITAR   1050
```

and in `gObjectEventGraphicsInfos` (`asm/overlay_01_sprite_data.s`), after the Feraligatr
row and before the `0xFFFF` end marker:

```
	.short SPRITE_FOLLOWER_MON_STATIC_TYRANITAR, MMODEL_FOLLOWER_MON_TYRANITAR, 0x227 | (19 << 10)
```

1050 is the first free id ([overworld-sprites.md](overworld-sprites.md#adding-a-new-sprite);
`mapkit sprite add` takes the same number, so use 1051 if you've added a sprite). The
packed value is the one every static row uses. A species with no follower model (one you
added) needs a texture first ([adding-a-species.md](adding-a-species.md#a-follower-model-of-its-own)).

**3. The object.**

```sh
tools/mapkit/mapkit.sh npc add Route45 tyranitar SPRITE_FOLLOWER_MON_STATIC_TYRANITAR 656 204 \
    --movement MOVEMENT_TYPE_FACE_DOWN --facing DIR_SOUTH \
    --script Route45_EventScript_Tyranitar --flag FLAG_HIDE_ROUTE_45_TYRANITAR
```

This adds the object to `map.json` and `#define obj_R45_tyranitar 15` to `ids.h`. Pick
a tile the player can walk up to, in the map editor or with
`tools/mapkit/mapkit.sh show Route45`. The coordinates above are only an example.

**4. The scripts**, in `data/maps/Route45/scripts.pory`. Append both labels to the end of
`scrdefs`. Appending matters, because the number of every existing script must stay the
same:

```
scrdefs {
    ...
    Route45_EventScript_TrainerTips
    Route45_EventScript_Tyranitar
    Route45_OnLoad
}

raw `
#include "constants/battle.h"
`

script Route45_OnLoad {
    if (flag(FLAG_ENGAGING_STATIC_POKEMON)) {
        setflag(FLAG_HIDE_ROUTE_45_TYRANITAR)
        removeobject(obj_R45_tyranitar)
        clearflag(FLAG_ENGAGING_STATIC_POKEMON)
        end
    }
    end
}

script Route45_EventScript_Tyranitar {
    playse(SEQ_SE_DP_SELECT)
    lockall
    faceplayer
    playcry(SPECIES_TYRANITAR, 0)
    npcmsg("TYRANITAR: Gyaoooh!\r")
    waitcry
    closemessage
    setflag(FLAG_ENGAGING_STATIC_POKEMON)
    wildbattle(SPECIES_TYRANITAR, 55, 0)
    clearflag(FLAG_ENGAGING_STATIC_POKEMON)
    checkbattlewon(VAR_SPECIAL_RESULT)
    if (var(VAR_SPECIAL_RESULT) == FALSE) {
        whiteout
        releaseall
        end
    }
    getstaticencounteroutcome(VAR_TEMP_x4002)
    if (var(VAR_TEMP_x4002) == BATTLE_OUTCOME_MON_CAUGHT) {
        setflag(FLAG_CAUGHT_TYRANITAR)
    }
    releaseall
    end
}
```

and register `OnLoad` in the map's `mapscripts` block (Route 45 only had
`OnTransition`):

```
mapscripts Route45_MapScripts {
    INIT_SCRIPT_ON_TRANSITION: Route45_OnTransition
    INIT_SCRIPT_ON_LOAD: Route45_OnLoad
}
```

If the map already has an `OnLoad`, put the `if (flag(FLAG_ENGAGING_STATIC_POKEMON))`
block at its top. Keep the `whiteout` on the loss path: after a loss the overworld hasn't
been rebuilt ([§2](#2-after-the-battle-who-hides-the-pokémon)).

**5. Optional.**

- Back after the Hall of Fame: [4.1 c](#41-catchable-again-after-a-loss-a-knockout-or-running-away).
- Catchable until caught: [4.1 a](#41-catchable-again-after-a-loss-a-knockout-or-running-away).
- Its own moves: [4.3](#43-give-it-other-moves).
- Legendary music and transition: a row in `sWildBattleIntroParams`
  ([battle-music.md §4.3](battle-music.md#43-a-species)). Without one it gets the normal
  wild theme.

Check with `tools/mapkit/mapkit.sh validate Route45 -w`, then `make release`.

## 5. Problems in the original game

None of these were changed.

- **Misleading names.** `staticwildwonorcaughtcheck` returns TRUE when you did *not* win
  or catch; `laticaughtcheck` returns TRUE when it was *not* caught. The `canFlee`
  argument of `SetupAndStartWildBattle` (and `canRun` of the fateful version) only picks
  the intro message.
- **The SoulSilver Groudon check looks at Kyogre's flag.** At the Hall of Fame, both
  version branches test `FLAG_CAUGHT_KYOGRE` before clearing
  `FLAG_BEAT_OR_ESCAPED_FROM_GROUDON_OR_KYOGRE`. In SoulSilver you catch Groudon, so the
  flag is cleared even after a catch. It does no harm: catching sets
  `VAR_SCENE_EMBEDDED_TOWER` to 4, and `EmbeddedTowerGroudonRoom_OnTransition` checks
  that first.
- **Dead checks.** Most scripts test `getstaticencounteroutcome` against 3 (draw) after
  `checkbattlewon`, which has already sent draws to `whiteout`.
- **Running counts as defeating it.** Running away hides most statics until the next
  Hall of Fame. Eusine even comments on it at Route 25 ("No one can pick on you just
  because you ran from SUICUNE").

## Not verified

- None of the recipes were play-tested; they were only built (HeartGold US). In particular,
  not tried in a game: that Ho-Oh stays after a knockout with [4.1 a](#41-catchable-again-after-a-loss-a-knockout-or-running-away),
  that `setwildmonmoves` gives the moves in battle, and that the Tyranitar sprite draws
  correctly at 656,204 on Route 45.
- Recipe [4.1 b](#41-catchable-again-after-a-loss-a-knockout-or-running-away) was not
  built.
- What happens if a script skips `whiteout` after a loss was not tried.
- That a draw (3) is possible in a single wild battle comes from the code
  (`battle_controller_opponent.c:1874`), not from a test.
