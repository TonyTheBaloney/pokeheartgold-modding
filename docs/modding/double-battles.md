<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Double, tag and multi battles

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The kinds of two-on-two battle, which battle-type flags each one gets, and how to
start each one: from a trainer who spots you, from a script, and with an AI partner
on your side like Lance in the Rocket Hideout.

| pokeemerald | here |
|---|---|
| `trainerbattle_double` | a trainer with `"double": 2` in `trainers.json`, started like any trainer |
| two trainers spotting you at once (`BATTLE_TYPE_TWO_OPPONENTS`) | the same: `BATTLE_TYPE_TAG`, from the sight check or `trainerbattle(T1, T2, 0, 0)` |
| `multi_2_vs_2` / `multi_2_vs_1` with Steven (`BATTLE_TYPE_INGAME_PARTNER`) | `multibattle(partner, T1, T2, 1)`: `BATTLE_TYPE_MULTI \| BATTLE_TYPE_AI` |
| `gPartnerTrainerId`, `FillPartnerParty` | `setup->trainerId[BATTLER_PLAYER2]`; the partner is an ordinary trainer from `trainers.json` |
| (none) | **escort mode**, left over from Diamond and Pearl (Cheryl, Riley...): a partner who joins every battle. Unused in HeartGold, but it still works in the code ([section 5](#5-escort-mode-a-partner-for-every-battle)) |

## 1. The kinds

| Kind | On your side | Against you | Battle type | Started by |
|---|---|---|---|---|
| single | you | one trainer | `TRAINER` | `trainerbattle(T, 0, 0, 0)` |
| **double** | you, 2 Pokémon out | one trainer with `"double": 2` (Twins, Double Team...) | `TRAINER \| DOUBLES` | the same, or both of its NPCs spotting you |
| **tag** | you, 2 Pokémon out | two trainers, one Pokémon each | `TRAINER \| DOUBLES \| TAG` | `trainerbattle(T1, T2, 0, 0)`, or two trainers spotting you at once |
| **multi** | you + an AI partner | two trainers | `TRAINER \| DOUBLES \| MULTI \| AI` | `multibattle(partner, T1, T2, 1)` |
| wild double | you + an AI partner | two wild Pokémon | `DOUBLES \| MULTI \| AI` | grass, only in escort mode |

The flags are `BATTLE_TYPE_*` in `include/constants/battle.h:133`. Link and Frontier
multi battles (another player, the Battle Tower partners) are separate and not
covered here.

The battler numbers ([battle-engine.md](battle-engine.md#7-glossary)): you are 0,
the opponents 1 and 3, and the second Pokémon on your side 2. In a double or tag
battle, 2 is your own second Pokémon. In a multi battle, 2 is the partner.

## 2. How the type is chosen

Every script trainer battle goes through `SetupAndStartTrainerBattle`
(`src/encounter.c:696`):

```c
    if (opponentTrainer2 != 0 && opponentTrainer1 != opponentTrainer2) {
        if (followerTrainerNum == 0) {
            battleType = (BATTLE_TYPE_TRAINER | BATTLE_TYPE_DOUBLES | BATTLE_TYPE_TAG);
        } else {
            battleType = (BATTLE_TYPE_TRAINER | BATTLE_TYPE_DOUBLES | BATTLE_TYPE_MULTI | BATTLE_TYPE_AI);
        }
    } else if (opponentTrainer1 == opponentTrainer2) {
        battleType = (BATTLE_TYPE_TRAINER | BATTLE_TYPE_DOUBLES);
    } else {
        battleType = BATTLE_TYPE_TRAINER;
        ...
```

Then `EnemyTrainerSet_Init` (`src/trainer_data.c:22`) loads every trainer whose id is
set (opponents, partner), builds their parties, and ORs in the `"double"` value of
the last one it loaded (`:45`). That is how a `"double": 2` trainer started with
`trainerbattle(T, 0, 0, 0)` becomes a double battle.

What follows from the code above:

| Call | Battle |
|---|---|
| `trainerbattle(T, 0, 0, 0)` | single; double if `T` has `"double": 2` |
| `trainerbattle(T, T, 0, 0)` | double against `T` (the sight script does this for Twins) |
| `trainerbattle(T1, T2, 0, 0)` | tag |
| `multibattle(P, T1, T2, x)` | multi with partner `P` |
| `multibattle(P, T, T, x)` or `multibattle(P, T, 0, x)` | **not** a multi: a double or a single, and the partner sits out. A multi needs two *different* opponents, so a two-on-two against one person needs two trainer entries (Lance and Clair, Ariana and a grunt) |
| `multibattle(0, T1, T2, x)` | tag (no partner) |

### The other arguments

`trainerbattle(T1, T2, a, b)` and `multibattle(P, T1, T2, b)`
(`ScrCmd_TrainerBattle`, `ScrCmd_MultiBattle`, `src/scrcmd_battle.c:99`, `:117`):

| Argument | Effect |
|---|---|
| `a` = 1 (single battles only) | adds `BATTLE_TYPE_11`: **losing doesn't black out.** The party is healed and the script goes on, with `checkbattlewon` giving 0 (`Task_StartEncounter`, `src/encounter.c:146`). Retail: the first rival battle in Cherrygrove, Giovanni at Tohjo Falls |
| `b` = 1 | the **first Pokémon of the partner** (multi) or of the opponent (single) comes out with the slide-in used for your walking Pokémon, not from a Poké Ball (`followMonSlot`, `src/encounter.c:727`; `Task_FollowMonSlideIn`, `src/battle/battle_controller_opponent.c:3264`). Retail passes 1 in all four multi battles: Lance's Dragonite stands next to him on the Hideout map. Ignored in double and tag battles |

## 3. Double and tag battles from trainers who spot you

`TryGetSeenByNpcTrainers` (`src/map_object_behavior.c:471`) runs each step. Whether
two-on-two is allowed (`doublesEligible`) is
`HasEnoughAlivePokemonForDoubleBattle`, checked in `FieldInput_Process`
(`src/field/field_control.c:199`).

| The first trainer that sees you | Result | Sight script path (`scr_seq_0953.s`) |
|---|---|---|
| single, and no other trainer sees you (or you have 1 healthy Pokémon) | single | type 0, `:1725` |
| single, and a second single trainer also sees you | **tag**: each walks up and talks in turn, then `TrainerBattle 8004, 8005` | type 2, `:1807` |
| `"double": 2` | **double**: its partner object is found, both walk up together and say lines 3 and 7, then `TrainerBattle 8004, 8005` with the same id | type 1, `:1759` |
| `"double": 2`, but you have 1 healthy Pokémon | it doesn't engage at all | |

Talking to a `"double": 2` trainer with one healthy Pokémon shows its
`TRMSG_DBL_1POKE_*` line instead (`PartyCheckForDouble`, `scr_seq_0953.s:1506`).

### A double-battle pair on a map

One trainer entry, two NPCs. From `data/maps/Azalea_Gym/map.json`:

```json
{ "local_id": "obj_T23GYM0102_gsbabygirl1_2", "x": 2, "y": 7, "trainer_type": "OBJECT_TYPE_TRAINER",
  "trainer_sight_or_param0": 1, "script": "std_trainer(TRAINER_TWINS_AMY_AND_MIMI)", ... },
{ "local_id": "obj_T23GYM0102_gsbabygirl1", "x": 3, "y": 7, "trainer_type": "OBJECT_TYPE_TRAINER",
  "trainer_sight_or_param0": 1, "script": "std_trainer_2(TRAINER_TWINS_AMY_AND_MIMI)", ... }
```

- The trainer has `"double": 2` and **at least two Pokémon**.
- One NPC uses `std_trainer(T)`, the other `std_trainer_2(T)`: that picks who says
  the `_1` and the `_2` lines ([trainer-text.md](trainer-text.md)).
- Both NPCs must have a trainer `trainer_type`. The second one is found by trainer
  number (`MapObjectManager_FindTrainerPartner`, `:670`); if it is missing, the game
  asserts.

### A tag pair

Two ordinary trainers, each with its own `std_trainer(T)`, placed so both can see
the same tile. Nothing links them: they team up only when both see you at once.
Otherwise each battles you alone.

## 4. A multi battle with an AI partner

What HeartGold does for Lance in the Rocket Hideout
(`data/maps/TeamRocketHeadquarters_B2F/scripts.pory:371`):

```
    multibattle(TRAINER_PKMN_TRAINER_LANCE_LANCE, TRAINER_EXECUTIVE_ARIANA_ARIANA_2, TRAINER_TEAM_ROCKET_GRUNT_25, 1)
    checkbattlewon(VAR_SPECIAL_RESULT)
    if (var(VAR_SPECIAL_RESULT) == 0) {
        whiteout
        ...
```

and for Silver against Lance and Clair (`DragonsDen/scripts.pory:409`, with one
partner entry per starter, `TRAINER_PARTNER_RIVAL_1`-`3`).

### What the partner is

An ordinary trainer in `files/poketool/trainer/trainers.json`
([trainers.md](trainers.md)). `TRAINER_PKMN_TRAINER_LANCE_LANCE` (675) is:

```json
{"type": "TRTYPE_MON", "class": "TRAINERCLASS_PKMN_TRAINER_LANCE", "name": "{TRNAME}Lance",
 "items": [], "ai_flags": 7, "double": 0, "party": [{"species": "SPECIES_DRAGONITE", "level": 40, ...}], ...}
```

| Field | For a partner |
|---|---|
| `class` | must have a **back sprite**, or it shows as Ethan or Lyra: Rival, Pokémon Trainer Lance, Cheryl, Riley, Buck, Mira, Marley, the player classes ([trainer-classes.md](trainer-classes.md#back-sprites)) |
| `ai_flags` | how it picks moves, like any trainer (`TrainerAI_Init`, `src/battle/trainer_ai.c:189`); `AI_DOUBLES` is added automatically. It never uses items ([trainers.md](trainers.md)) |
| `party` | any size up to 6. Lance has only Dragonite |
| `messages` | none needed: a partner says nothing in battle |
| `"double"` | 0 |

The opponents are ordinary trainers too, one Pokémon out each.

### Who controls what

With `BATTLE_TYPE_AI`, **every battler except you is AI-controlled**
(`OpponentData_SetInputTasks`, `src/battle/battle_controller_opponent.c:6352`). You
use your whole party; each of the four battlers has its own party
(`BattleSystem_GetParty`, `src/battle/battle_system.c:74`).

### Winning and losing

`BattleControllerPlayer_CheckBattleOver` (`src/battle/battle_controller_player.c:3499`):

- **You lose when your own party is out**, even if the partner still has Pokémon.
  When the partner runs out first, you fight on alone.
- You win when both opponents are out.

Losing blacks out as usual, so the script needs the `whiteout` branch shown above.
Nothing heals your party before or after unless the script does it (`healparty`).

### Recipe: a new multi battle

1. **The partner.** Add a trainer with a class that has a back sprite
   ([trainers.md](trainers.md#adding-a-trainer)). Or reuse
   `TRAINER_PKMN_TRAINER_LANCE_LANCE` / `TRAINER_PARTNER_RIVAL_*`.
2. **Two opponents**, two different trainer entries, each with `TRMSG_LOSE` text.
3. **The script**, on an NPC or a trigger:

   ```
       multibattle(TRAINER_MY_PARTNER, TRAINER_MY_FOE_1, TRAINER_MY_FOE_2, 0)
       checkbattlewon(VAR_SPECIAL_RESULT)
       if (var(VAR_SPECIAL_RESULT) == 0) {
           whiteout
           releaseall
           end
       }
       settrainerflag(TRAINER_MY_FOE_1)
       settrainerflag(TRAINER_MY_FOE_2)
   ```

   Pass `1` as the last argument only if the partner's first Pokémon is shown next to
   them on the map. Set the trainer flags if other scripts check `defeated(...)`.
4. Battle music for the battle comes from the class of `TRAINER_MY_FOE_1`; in a
   multi battle that is the normal trainer music unless it is a Rocket class, the
   Kimono Girls or Red ([battle-music.md](battle-music.md#trainer-battles)).

## 5. Escort mode: a partner for every battle

In Diamond and Pearl, Cheryl, Riley and others walked with you and joined every
battle. The code is still here, and HeartGold never turns it on:

```
    setvar(VAR_FOLLOWER_TRAINER_NUM, TRAINER_MY_PARTNER)
    setescortmode
    ...
    clearescortmode
    setvar(VAR_FOLLOWER_TRAINER_NUM, 0)
```

`setescortmode` sets `FLAG_HAVE_FOLLOWER` (`src/scrcmd_17.c:78`); the partner is
`VAR_FOLLOWER_TRAINER_NUM` (0x403F). While it is set:

| What | Effect | Where |
|---|---|---|
| `trainerbattle(T1, T2, 0, 0)` | multi with the partner | `ScrCmd_TrainerBattle`, `src/scrcmd_battle.c:109` |
| `trainerbattle(T, 0, 0, 0)`, a single trainer spotting you | still a single: the partner sits out ([section 2](#2-how-the-type-is-chosen)) | |
| grass encounters and Sweet Scent | always a double against two wild Pokémon, with the partner; roamers don't appear | `src/field/encounter_check.c:259`, `:284`, `:301`; Sweet Scent `:453` |
| trainers who need two Pokémon | engage even with one healthy Pokémon | `src/field/field_control.c:200` |
| after every battle | your party is healed | `src/encounter.c:154`, `:379` |
| Fly, Surf, Rock Climb, Teleport, Dig | can't be used | `src/field_move.c:227`, `:263`, `:403`, `:474`, `:517` |
| Bicycle, fishing rods, Escape Rope | can't be used | `src/field_use_item.c:327`, `:470`, `:580` |
| blacking out, entering the Hall of Fame | ends escort mode | `src/blackout.c:203`, `src/game_clear.c:105` |

`checkescortmode(VAR)` reads it. Escort mode doesn't put the partner on the map: an
NPC that walks with you is up to the map scripts. Note the gap above: alone, a
trainer that spots you still fights you one-on-one.

## Not verified

- The recipe in section 4 (`multibattle` with Lance as partner against two Route 30
  trainers), the escort-mode lines of section 5 and a `partycheckfordouble` check were
  added to `data/maps/Route30/scripts.pory` and built into a HeartGold ROM with
  `make release`, then reverted; all four checksums matched. Nothing was played in
  game.
- Escort mode is read from the code. HeartGold never sets `FLAG_HAVE_FOLLOWER`, so
  parts of it (the double wild encounter, the party screen with a partner) may have
  bugs that the retail game never shows.
- What the party screen shows in a multi battle (your Pokémon only, or the partner's
  too) wasn't traced.
- What happens in a scripted tag battle (`trainerbattle(T1, T2, 0, 0)`) when you have
  only one healthy Pokémon wasn't traced; Route 34 doesn't check. Use
  `partycheckfordouble(VAR)` first.
