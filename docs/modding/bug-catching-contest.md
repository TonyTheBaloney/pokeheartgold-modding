<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# The Bug-Catching Contest

> AI-generated; not affiliated with pret. See AI.md at the repository root.

On Tuesday, Thursday and Saturday the gate guards at National Park run the
Bug-Catching Contest. You enter with one Pokémon and get 20 Sport Balls and 20
minutes. You may keep one bug at a time. When the contest ends you are judged against
five NPCs, and you keep the bug you were holding.

The rules live in three places. The **C code** in `src/overlay_bug_contest.c` sets up the
contest, picks the wild Pokémon and the opponents, scores your catch and picks the prize.
The **standard script** `files/fielddata/script/scr_seq/scr_seq_0151.s` handles entry,
the end of the contest and the judging. Two **CSV tables** in `files/data/mushi/` hold the
wild Pokémon and the opponents' results. The rest is glue: the timer, the battle type and
the swap screen.

## Where things are

| What | File |
|---|---|
| contest state (`BugContest`, `BUGMON`, `BugContestant`) | `include/bug_contest_internal.h` |
| setup, encounters, opponents, scoring, prizes | `src/overlay_bug_contest.c` (overlay `bug_contest`) |
| wild Pokémon by day | `files/data/mushi/mushi_encount.csv` → `data/mushi/mushi_encount.bin` |
| NPC opponents' catches and scores | `files/data/mushi/mushi_trainer.csv` → `data/mushi/mushi_trainer.bin` |
| CSV layouts | `files/data/mushi/mushi_encount.txt`, `mushi_trainer.txt`; built by `files/data/mushi/meson.build` |
| entry, time up, retire, judging, NPC lines | `files/fielddata/script/scr_seq/scr_seq_0151.s` (standard scripts 10400-10428) |
| contest text | `files/msgdata/msg/msg_0246.json` |
| the gates | `data/maps/Route36_NationalParkGatehouse/scripts.pory`, `data/maps/Route35_NationalParkPokeathalonGatehouse/scripts.pory` |
| the contest area | `data/maps/NationalPark_BugCatchingContest/` (`MAP_NATIONAL_PARK_BUG_CATCHING_CONTEST`) |
| where judging happens | `data/maps/NationalPark/` (`scripts.pory`, `map.json`) |
| script commands | `ScrCmd_BugContestAction` ... `ScrCmd_IsBugContestantRegistered`, `src/field/scrcmd_pokemon_misc.c:1458-1554` |
| the timer | `FieldSystem_IncrementBugContestTimer`, `src/field_misc_events.c:384`; time-up check `src/field/field_control.c:837` |
| the battle (Sport Ball button, catch) | `BATTLE_TYPE_BUG_CONTEST`; `src/battle/battle_controller_player.c:408`, `:1868` |
| Sport Ball catch rate | `BattleSystem_CalculateBallShakes`, `src/battle/battle_command.c:7281` |
| the swap screen | `src/application/bug_contest_swap_mon.c`; text `files/msgdata/msg/msg_0029.json` |
| "contest is running" flag | `Save_VarsFlags_CheckBugContestFlag`, `src/sys_flags.c:216` (checks `FLAG_UNK_996`) |

## 1. Flags and variables

The contest uses these. All of them are saved, but you can't save while the contest is
running ([§11](#11-what-is-saved)).

| Name | Set | Cleared | Meaning |
|---|---|---|---|
| `FLAG_UNK_996` | end of entry (`scr_seq_0151.s:182`) | arriving at National Park to be judged (`data/maps/NationalPark/scripts.pory:77`) | **the contest is running.** This is the flag C checks (`src/sys_flags.c:216`) |
| `FLAG_BUG_CONTEST_ACTIVE` (0x993) | entry (`scr_seq_0151.s:174`) | after judging (`:366`) | only used to pick the contest music for National Park and both gates (`sMusicOverrideMap`, `src/sys_flags.c:14-18`) |
| `FLAG_UNK_24E` | entry (`:175`) | after judging (`:367`) | hides National Park's normal NPCs and trainers (`data/maps/NationalPark/map.json`) |
| `VAR_UNK_4118` | 1 at entry (`:176`); 2 if you finish early at the gate (`:258`) | 0 at judging (`:266`) | 1 makes the gate warp you into the contest area |
| `VAR_UNK_40F7` | 1 at entry (`:177`) | 0 at judging (`:267`) | 1 makes National Park start the judging |
| `FLAG_BUG_CONTEST_OTHER_POKES_HELD` | the guard kept your other Pokémon (`:164`) | after judging (`:368`) | "We'll return the Pokémon we kept" |
| `FLAG_WON_THIS_BUG_CONTEST` | you placed first (`:302`) | you didn't (`:307`) | the NPCs congratulate you afterwards |
| `FLAG_DAILY_DID_BUG_CONTEST` | after judging (`:365`) | each new day | one contest per day |
| `VAR_BUG_CONTEST_HELD_PRIZE` | Bag full at judging (`:329`) | prize collected (`:227`) | the item the guard is holding for you |
| `FLAG_HIDE_BUG_CONTESTANT_*` (0x273-0x27C) | entry, for the 5 NPCs not taking part | after judging | which contestants stand in the contest area |

Daily flags are cleared by `ClearDailyFlags` (`src/script_manager.c:410`) when the day
changes (`src/field_time_events.c:78`).

## 2. Which days, and how that is checked

There is no single list of days. Each piece checks the weekday itself, with
`getweekday` (`ScrCmd_GetWeekday`, `src/scrcmd_c.c:3555`, which returns `RTC_WEEK_*`:
0 Sunday ... 6 Saturday).

| Where | What it does on days 2, 4, 6 |
|---|---|
| guard script, `scr_seq_0151.s:100-120` | days 2/4/6 show "Today's Tuesday/Thursday/Saturday..." (`msg_0246_00004`-`00006`) and offer entry. Any other day shows `msg_0246_00007` ("held on Tuesday, Thursday, and Saturday") and stops. **This is the check that matters.** |
| both gates' `OnTransition` (`Route36_NationalParkGatehouse/scripts.pory:11-30`, `Route35_.../scripts.pory:74-91`) | on days 2/4/6, or while `VAR_UNK_4118` is 1, shows the attendant object flagged `FLAG_UNK_1C4` and hides the one flagged `FLAG_UNK_1C3`. Both attendants run the same guard script. |
| `BugContest_InitEncounters`, `src/overlay_bug_contest.c:305` | picks the wild set as `weekday / 2` ([§5](#5-the-wild-pokémon)) |
| `BugContest_InitOpponents`, `src/overlay_bug_contest.c:276` | keeps opponent rows whose `day` is today or 7 ([§7](#7-the-npc-opponents)) |
| phone, `PhoneScript_Generic_OnlyTuesThursSat`, `src/application/pokegear/phone/scripts/phone_scripts_generic.c:154` | the `BUGCONTESTDAYS` call rows ([phone.md](phone.md#4-what-route-trainers-say)) |

The guard's script reads the weekday into `VAR_TEMP_x4000` (`scr_seq_0151.s:100`) and
passes it to `BugContestAction 0, VAR_TEMP_x4000` (`:179`), which becomes
`BugContest.day_of_week` (`src/field/scrcmd_pokemon_misc.c:1465`,
`src/overlay_bug_contest.c:48`). The C side never checks that the day is a contest day.
There is no time-of-day check.

## 3. Entering

Talk to the attendant in either gate. Both run `std_bug_contest_guard_start`
(`scr_seq_0151_005`, `scr_seq_0151.s:91`). In order:

1. **A prize waiting?** If `VAR_BUG_CONTEST_HELD_PRIZE` is not 0, you get it first (`_02BC`, line 218).
2. **Already done today?** `FLAG_DAILY_DID_BUG_CONTEST` gives `msg_0246_00018` (line 99).
3. **Day check** and the yes/no ([§2](#2-which-days-and-how-that-is-checked)).
4. **Room for the catch.** If the PC has no free space **and** the party has 6 Pokémon, you're
   turned away with `msg_0246_00016` (lines 133-138).
5. **Only one Pokémon?** If exactly one is alive and the party has one Pokémon, skip to step 7
   (lines 140-145).
6. **Otherwise** the guard names your first healthy Pokémon (`GetPartyLeadAlive`) and asks if
   that's OK (`msg_0246_00010`). No: "Please reorder your Pokémon". Yes: "we'll hold your
   other Pokémon" and `FLAG_BUG_CONTEST_OTHER_POKES_HELD` is set (lines 147-164).
7. **Start.** Contest music; "received 20 Sport Balls" (`msg_0246_00014`, the 20 is in the
   text); the rules (`msg_0246_00015`). The flags and variables of §1 are set,
   `BugContestAction 0` builds the contest in C, `_0268` hides the NPCs not taking part,
   and `FLAG_UNK_996` is set last (lines 170-183).

The gate script then sees `VAR_UNK_4118 == 1` and warps you to
`MAP_NATIONAL_PARK_BUG_CATCHING_CONTEST` at (75, 39)
(`Route36_NationalParkGatehouse/scripts.pory:85-116`).

### What `BugContest_New` does

`src/overlay_bug_contest.c:38-54`:

| Step | Line | |
|---|---|---|
| allocate the `BugContest` on `HEAP_ID_3` and zero it | 41-43 | it lives only in RAM, in `fieldSystem->bugContest` |
| `sport_balls = 20` | 45 | |
| `national_dex = Pokedex_GetNatDexFlag(...)` | 47 | picks the wild set, the opponents' rows and the first prize |
| `day_of_week = weekday` | 48 | |
| `BugContest_BackUpParty` | 49 | [below](#the-party) |
| `BugContest_InitOpponents` | 50 | the NPCs' results are fixed **now** ([§7](#7-the-npc-opponents)) |
| `BugContest_InitEncounters` | 51 | copies today's 10 wild slots ([§5](#5-the-wild-pokémon)) |
| `FieldSystem_StartBugContestTimer` | 52 | [§6](#6-the-time-limit) |

### The party

`BugContest_BackUpParty` (`src/overlay_bug_contest.c:191-207`) copies the whole party to
`party_bak`, remembers the party size (`party_cur_num`) and the lead's slot
(`lead_mon_idx = Save_GetPartyLeadAlive`, the first Pokémon that isn't an egg and has HP,
`src/field_misc_util.c:199`). It then removes every Pokémon except the lead **from the save's
own party**. For the rest of the contest your party is one Pokémon.

At the end, `BugContest_RestoreParty_RetrieveCaughtPokemon` (`:209-232`) copies the lead
(with whatever EXP, HP and PP changes it got), puts the backup party back, and writes the lead
into its old slot, keeping its Aprijuice modifiers. Then the caught bug is added to the end of
the party. If the party had 6 Pokémon **before** the contest it goes to the first free box
slot instead (`party_cur_num >= PARTY_SIZE`, line 226).

In battle only party slot 0 is used: `BattleSetup_InitFromFieldSystem` gives the player a
party of size 1 for `BATTLE_TYPE_BUG_CONTEST` (`src/battle/battle_setup.c:230-232`).

## 4. Sport Balls and the battle

| | |
|---|---|
| Count | 20, `src/overlay_bug_contest.c:45`. Stored in `BugContest.sport_balls` |
| Into battle | `BattleSetup_New_BugContest` puts the count in `setup->safariBalls` and a copy of the bug you hold in `setup->bugContestMon` (`src/battle/battle_setup.c:95-100`, called from `src/field/encounter_check.c:1173-1177`) |
| The Bag button | becomes "throw a Sport Ball": `CONTROLLER_COMMAND_CATCHING_CONSTEST_THROW_BALL` (`src/battle/battle_controller_player.c:408-411`) |
| A throw | `BattleControllerPlayer_CatchingContestThrowBall` (`:1868-1881`): runs `BATTLE_SUBSCRIPT_THROW_POKEBALL` with `itemTemp = ITEM_SPORT_BALL` and takes one ball |
| Catch rate | **×1.5**: `ballMultiplier = 15` (`src/battle/battle_command.c:7281-7283`; multipliers are tenths, `:7166`). The rest of the formula is the normal one |
| After battle | the count is written back to `sport_balls` (`BattleSetup_CopyResultsToSaveData`, `src/battle/battle_setup.c:444-449`) |
| Battle menu | `BATTLE_MENU_19`/`20` instead of the normal menus (`src/battle/battle_controller_opponent.c:4305`, `:4320`); one party ball on the gauge (`src/battle/battle_input.c:1674-1675`) |

The Sport Ball is item 499 (`ITEM_SPORT_BALL`, `include/constants/items.h:961`). You never
have it in the Bag; the battle makes one up for each throw.

**Out of balls.** The throw subscript (`files/battledata/script/subscript/subscript_0011_ThrowBall.s:17-28`)
checks, in a contest battle with no catch, whether the count reached 0. If so it prints
"You're out of Sport Balls! Game over!" (`msg_0197_01269`) and ends the battle as if you fled.

**After the battle** (`Task_BugContestEncounter`, `src/encounter.c:477-540`):

| Result | What happens |
|---|---|
| lost or draw | `Task_BugContestWarpToJudging` (`src/game_clear.c:98`): heals the party and warps you to judging |
| caught | the swap screen ([§9](#9-the-swap-prompt)) |
| no catch and 0 balls left | `BugContest_WarpToJudging` (line 517-518), straight to judging |
| caught with the last ball | `std_bug_contest_balls_up` (line 533-534): "You've run out of Poké Balls" (`msg_0246_00001`), then the warp |

In battle a caught bug never joins the party. `CopyPokemonToPokemon(mon, BattleSystem_GetBugContestCaughtMon(...))`
stores it in the setup's `bugContestMon` (`src/battle/battle_command.c:6993-7004`). It is still
registered as caught in the Pokédex (`:6989`), and there is no nickname screen in battle (`:6880-6881`).

## 5. The wild Pokémon

[wild-encounters.md](wild-encounters.md#bug-catching-contest) lists the file. Here is
how it is used.

`mushi_encount.csv` has **4 sets of exactly 10 rows**. Columns: `species, lvlmin, lvlmax,
rate, score` (`BUGMON`, `include/bug_contest_internal.h:30-37`; the `.txt` adds 2 pad bytes).

**Which set** (`BugContest_InitEncounters`, `src/overlay_bug_contest.c:304-309`):

| | Set | Rows | Species |
|---|---|---|---|
| no National Dex, any day | 0 | 1-10 | Caterpie, Weedle, Metapod, Kakuna, Butterfree, Beedrill, Venonat, Paras, Scyther, Pinsir (levels 7-18) |
| National Dex, Tuesday (2/2) | 1 | 11-20 | the same species, levels 24-36 |
| National Dex, Thursday (4/2) | 2 | 21-30 | Wurmple, Silcoon, Nincada, Volbeat, Kricketot, Kricketune, Dustox, Combee, Scyther, Pinsir |
| National Dex, Saturday (6/2) | 3 | 31-40 | Wurmple, Cascoon, Nincada, Illumise, Kricketot, Kricketune, Beautifly, Combee, Scyther, Pinsir |

The set is `day_of_week / 2`, so other days would fall into these too: Sunday and Monday 0,
Wednesday 1, Friday 2. The file has no version columns; HeartGold and SoulSilver get the
same tables.

**`rate` is a threshold, not a weight.** `BugContest_GetEncounterSlot` (`:171-189`) rolls 0-99
and takes the **first** row whose `rate` is at most the roll. So a row's chance is the previous
row's `rate` minus its own (100 for the first row), and the last row must have `rate` 0 or the
loop runs past the table. Every set uses 80, 60, 50, 40, 30, 20, 15, 10, 5, 0:

| Row in set | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| `rate` | 80 | 60 | 50 | 40 | 30 | 20 | 15 | 10 | 5 | 0 |
| chance | 20% | 20% | 10% | 10% | 10% | 10% | 5% | 5% | 5% | 5% |

The level is random from `lvlmin` to `lvlmax` (line 185-186).

**When it applies.** While `FLAG_UNK_996` is set, every grass encounter, on any map, uses this
table instead of the map's (`FieldSystem_PerformLandOrSurfEncounterCheck`,
`src/field/encounter_check.c:279-280`, `:295-296`; Sweet Scent the same, `:448-449`, `:464-465`).
The map's own land table still decides **how often** you meet something: no land `rate`, no
encounters (`:233-235`). The contest area uses `ENCDATA_D22R0102` with land rate 25. Repel still
works, against the rolled level (`:982`). Despite the name of the function it uses
(`generateWildNonShinyAndAddToParty`, `:987`), the Pokémon can be shiny, 1 in 8192 as usual
([shiny.md](shiny.md#2-who-can-be-shiny-and-how)).

## 6. The time limit

`BugContest.elapsed_time` counts **minutes on the DS clock**. It starts at 0 (the struct is
zeroed).

1. While no field task runs, every frame calls `FieldSystem_StartBugContestTimer`
   (`src/field/fieldmap.c:416-418`). Despite the name, this is the general clock update
   (`src/field_time_events.c:29-39`): it compares the hardware clock with the time last
   stored in the save.
2. When at least a whole minute has passed, `FieldSystem_HandleMinutesPassed`
   (`:97-99`) calls `FieldSystem_IncrementBugContestTimer`, which adds the minutes if a contest
   exists and `FLAG_UNK_996` is set (`src/field_misc_events.c:384-389`). The stored time is only
   updated then (`src/field_time_events.c:66-73`), so leftover seconds carry over.
3. Each frame you can move, `FieldSystem_UpdateBugContest` (`src/field/field_control.c:837-847`,
   called at `:221`) starts `std_bug_contest_time_up` once `elapsed_time >= 20`.

Battles are field tasks, so the timer isn't updated during one. But the stored time isn't moved
either, so the battle's minutes are added when you return to the field. Time in battles counts.

`BugContest_New` calls the same update at the start (`src/overlay_bug_contest.c:52`). At that
point `fieldSystem->bugContest` isn't set yet and `FLAG_UNK_996` is off, so minutes already
waiting are thrown away rather than counted.

The guards show the time left with `BugContestGetTimeLeft`, which prints `20 - elapsed_time`,
or 1 once 20 or more have passed (`src/field/scrcmd_pokemon_misc.c:1526-1546`).

Setting the DS clock back makes `FieldSystem_CheckTimeAdvance` take the new time without adding
anything (`src/field_time_events.c:57-61`). See [day-night-and-rtc.md](day-night-and-rtc.md).

## 7. The NPC opponents

The opponents don't play. Their catches and scores are drawn at entry, in
`BugContest_InitOpponents` (`src/overlay_bug_contest.c:244-288`).

**The ten contestants** have ids 0-9. The id picks everything about them:

| id | Name (`msg_0246_00078` + id) | Class (`sBugContestOpponentClasses`, line 19) | CSV rows | Hide flag |
|---:|---|---|---|---|
| 0 | Don | Bug Catcher | 1-8 | `FLAG_HIDE_BUG_CONTESTANT_BUG_CATCHER_DON` (0x273) |
| 1 | Ed | Bug Catcher | 9-16 | 0x274 |
| 2 | Abby | Ace Trainer F | 17-24 | 0x275 |
| 3 | William | Pokéfan M | 25-32 | 0x276 |
| 4 | Benny | Bug Catcher | 33-40 | 0x277 |
| 5 | Barry | Camper | 41-48 | 0x278 |
| 6 | Cindy | Picnicker | 49-56 | 0x279 |
| 7 | Josh | Bug Catcher | 57-64 | 0x27A |
| 8 | Samuel | Youngster | 65-72 | 0x27B |
| 9 | Kipp | School Kid M | 73-80 | 0x27C |

Their standard scripts are `std_bug_contest_<name>_during` (in the contest area) and `_after`
(in National Park), 10408 + 2 × id and one more (`include/constants/std_script.h:682-701`).

**Choosing five.** For each of the 5 slots it rolls `LCRandom() % 10` until it gets an id not
already chosen (lines 265-269).

**Choosing the catch.** `mushi_trainer.csv` has 8 rows per contestant (`bin[8 * id]`, line 270).
Columns: `national, day, species, score, randmod` (`BugContestantData`,
`include/bug_contest_internal.h:41-47`). A row is skipped if (lines 272-280):

- `national` is 1 and you don't have the National Dex, or
- `day` is less than 7 (`RTC_WEEK_MAX`) and isn't today.

So `day` 7 means any day, and rows with `national` 0 stay in even with the National Dex. One of
the remaining rows is picked at random (line 281). With the National Dex on a Thursday, Abby's
choices are her two `0,7` rows (Paras, Venonat) and her two `1,4` rows (Combee, Volbeat): an NPC
can "catch" a Pokémon that isn't in today's wild table. Her score is unaffected, since it comes
from the row.

**The score** (lines 282-283):

```c
score = (LCRandom() % (2 * randmod)) - randmod;     // -randmod ... randmod-1
contestants[i].score = score + data.score;
```

| Rows | `score` | `randmod` | Final range |
|---|---:|---:|---|
| Scyther (Don, Ed) | 320 | 20 | 300-339 |
| Pinsir (Don, Ed) | 300 | 30 | 270-329 |
| Paras, Venonat, Combee, Volbeat, Kricketune, Illumise | 280 | 50 | 230-329 |
| Beedrill, Butterfree, Kricketune, Nincada, Combee | 260 | 50 | 210-309 |
| Kakuna, Metapod, Kricketot, Dustox, Beautifly | 240 | 90 | 150-329 |
| Weedle, Caterpie, Silcoon, Cascoon, Wurmple | 220 | 110 | 110-329 |

On National Dex Saturdays the two swap for Don and Ed: Pinsir has 320/20 and Scyther 300/30.

The NPCs' Pokémon don't exist; only the species and score are shown at judging. In the contest
area, the entry script hides the five who aren't taking part (`_0268`, `scr_seq_0151.s:193-206`,
`SetFlagVar` on 627 + id = 0x273 + id). During judging, National Park's `OnResume` moves the five
in a row in front of the judge (`data/maps/NationalPark/scripts.pory:35-56`, objects 10-19 of
`NationalPark/map.json`).

## 8. Scoring your catch

`BugContest_JudgePlayerMon` (`src/overlay_bug_contest.c:314-345`). With nothing caught the score is
0. Otherwise it looks the species up in **today's** 10 wild rows (the first match) and adds four
parts:

| Part | Code | Max |
|---|---|---:|
| rarity | the row's `score` column (60, 80 or 100) | 100 |
| level | `level * 100 / lvlmax` (`lvlmax` from the same row) | 100 |
| IVs | `(sum of the 6 IVs) * 100 / (31 * 6)` | 100 |
| HP | `currentHP * 100 / maxHP` | 100 |

Each part is a separate integer division, rounded down. The best possible score is 400.
Example: a level 14 Scyther from set 0 (`lvlmax` 14), IVs adding up to 93, full HP:
100 + 100 + 50 + 100 = **350**.

- HP is the bug's HP when caught. Nothing heals it before judging (the heal on a loss only
  touches the party, `src/game_clear.c:106`), so damage lowers the score.
- If the species isn't in the table, `GF_ASSERT` fires and the score is 0 (lines 332-335).
- A level above `lvlmax` would give more than 100 for level. That can't happen with the
  retail tables ([level-scaling.md](level-scaling.md)).

**Ranking** (`BugContest_Judge`, lines 62-102). You are contestant 5. The six are sorted by
score with a selection sort that takes the **last** of equal scores (`score2 >= score`,
line 86). You start last and only move when you're picked, so **you win every tie**. Top three
places 0-2, anything else 3. With no catch your score is 0, and the lowest NPC score is 110,
so you come fourth.

## 9. The swap prompt

After every catch, `BugContest_PromptSwapPokemon` (`src/field_misc_events.c:403-436`) opens the
swap screen (`BugContestSwapMon_LaunchApp`, `src/launch_application.c:658`):

- **First catch** (`caught_poke` is 0): the screen only shows "Caught {species}!"
  (`msg_0029_00000`; `BugContestSwapMon_GetInitialState`, `src/application/bug_contest_swap_mon.c:545-556`).
- **Later catches:** both Pokémon with their HP bars and "Swap the {new} for your {old}?"
  (`msg_0029_00001`). Yes keeps the new one ("Released {old} and caught {new}!"); No keeps the old
  ("Released {new} and kept {old}!") (`BugContestSwapMon_ChooseMon`, `:451-517`;
  `BugContestSwapMon_SetResult`, `:573-584`).

Back on the field (`src/field_misc_events.c:423-431`), if the kept Pokémon isn't the current one
(on a first catch `keptMon` is still NULL), the new catch is copied into `BugContest.mon`, and
`caught_poke` is set. The released Pokémon is simply dropped. You hold one bug at a time, and
the one you hold at the end is judged and kept.

## 10. Ending and judging

**Ways to end:**

| How | Script / code |
|---|---|
| 20 minutes | `std_bug_contest_time_up` (`scr_seq_0151_000`, line 46): "Time's up!", warp |
| last ball used on a catch | `std_bug_contest_balls_up` (`_001`, line 56) |
| last ball used without a catch | the battle says "Game over!", then `BugContest_WarpToJudging` ([§4](#4-sport-balls-and-the-battle)) |
| losing a battle | `Task_BugContestWarpToJudging`, heals the party (`src/game_clear.c:98-106`) |
| Start menu **Retire** | `std_bug_contest_retire` (`_004`, line 72) (`src/start_menu.c:1260-1261`): "You still have N minute(s) left. Finish now?" |
| walking into a gate | the gate's frame script runs `std_bug_contest_guard_ask_end` (`_006`, line 242): same question. No sends you back into the area; yes sets `VAR_UNK_4118` to 2 and warps |

Every path ends at `MAP_NATIONAL_PARK` (46, 50): `_0076` in the script (line 41) and
`BugContest_WarpToJudging` in C (`src/field_misc_events.c:391-401`). On arrival
`NationalPark_OnTransition` clears `FLAG_UNK_996` because `VAR_UNK_40F7` is 1
(`data/maps/NationalPark/scripts.pory:60`, `:74-77`), and the frame table starts
`std_bug_contest_judging` (`:529-533`).

**Judging** (`scr_seq_0151_007`, lines 263-374):

1. `JudgeBugContest VAR_TEMP_x4000, VAR_TEMP_x4001, VAR_TEMP_x4002` gives your place (0-3), the
   prize item and your species, or 0 for none (`ScrCmd_JudgeBugContest`,
   `src/field/scrcmd_pokemon_misc.c:1486-1509`).
2. Third, second and first are announced with `BufferBugContestWinner 2/1/0`, each followed by
   "The score was N points!" (3 digits, `src/overlay_bug_contest.c:144`). Your own place uses the
   message without a trainer class (`msg_0246_00030`/`33`/`35`), an NPC's the one with
   (`31`/`34`/`36`).
3. The prize line is `msg_0246_00037 + place` (line 315-317): first, second, third, or
   "Everyone else gets a ... as a consolation prize!" Then the item is given, or held if the Bag
   is full ([below](#prizes)).
4. Your other Pokémon are returned (`msg_0246_00047`, if they were held). Then the nickname offer
   for the bug (`NicknameInput 255` edits `BugContest.mon`, `src/scrcmd_c.c:2127-2131`).
   `BufferBugContestMonNick` returns whether your party was full, which gives "sent to your Box"
   (`msg_0246_00046`).
5. Clean-up: the contestants' hide flags are cleared (`_04FD`), `FLAG_DAILY_DID_BUG_CONTEST` is
   set, the §1 flags are cleared, and `BugContestAction 1` restores the party, adds the bug and
   frees the contest (`ScrCmd_BugContestAction`, `src/field/scrcmd_pokemon_misc.c:1466-1469`;
   it also checks for Bill's PC-full call).

### Prizes

`BugContest_Judge`, `src/overlay_bug_contest.c:105-127`:

| Place | Prize |
|---|---|
| 1st, no National Dex | Sun Stone |
| 1st, National Dex | one of 10, 10% each: Sun, Moon, Fire, Thunder, Water, Leaf (`ITEM_SUN_STONE + 0..5`), Shiny, Dusk, Dawn, Oval Stone (`ITEM_SHINY_STONE + 0..3`) |
| 2nd | Everstone |
| 3rd | Sitrus Berry |
| 4th or lower | Shed Shell |

The code relies on the item ids being in a row: 80-85 and 107-110 (`include/constants/items.h:394-426`).

If the Bag has no room, the item goes into `VAR_BUG_CONTEST_HELD_PRIZE` (`scr_seq_0151.s:326-329`).
You can collect it from a gate attendant (checked first in `guard_start`, line 92) or from the
clerk in National Park, object 20 in `NationalPark/map.json`, script 10428 = `scr_seq_0151_028`
(line 545). There is no `std_` name for 10428 in `std_script.h`.

## 11. What is saved

**Nothing about a running contest.** `BugContest` is allocated on the heap
(`src/overlay_bug_contest.c:41`) and held in `fieldSystem->bugContest` (`include/field_system.h:275`).
While `FLAG_UNK_996` is set the Start menu disables the Bag and Save
(`FieldSystem_GetStartMenuButtonInhibitFlags_BugContest`, `src/start_menu.c:313-315`, used at
`:220-221` and `:262-263`). The Y-button registered items do nothing either
(`src/field_use_item.c:772`). So the contest can't be saved: the balls, the timer, the opponents,
the held bug and your other Pokémon all exist only in RAM.

What persists afterwards is the §1 flags and variables, the prize, the bug in your party or box,
and the Pokédex entries for what you caught. Changing any table or rule in this guide doesn't
change the save layout.

Other systems that check the contest flag:

| | |
|---|---|
| phone | National Park contacts don't ring and don't nag about rematches or gifts during the contest (`src/field/gear_phone_calls.c:216`; `phone_scripts_generic.c:132`, `:144`; [phone.md](phone.md)) |
| music | `sMusicOverrideMap`, `src/sys_flags.c:14-18` (on `FLAG_BUG_CONTEST_ACTIVE`) |
| contest-area map | no cycling, `allow_escaping` false, no Fly, no incoming calls (`data/maps/NationalPark_BugCatchingContest/map.json:12-18`) |

## 12. How to...

All of these are in [Not verified](#not-verified): none was built or played.

### Change the days

To add **Sunday**:

1. **The guard.** In `scr_seq_0151.s`, before line 101:

   ```diff
    	GetWeekday VAR_TEMP_x4000
   +	Compare VAR_TEMP_x4000, 0
   +	GoToIfEq _sunday
    	Compare VAR_TEMP_x4000, 2
   ```

   and somewhere after an `End`:

   ```
   _sunday:
   	NPCMsg msg_0246_00088
   	GoTo _016E
   ```

   `msg_0246_00088` is a new message at the end of `msg_0246.json` (a copy of `00004` saying
   Sunday; [text-and-messages.md](text-and-messages.md)). Update `msg_0246_00007` ("held on
   Tuesday, Thursday, and Saturday") too.
2. **The gates.** Add `elif (var(VAR_TEMP_x4000) == 0) { clearflag(FLAG_UNK_1C4) setflag(FLAG_UNK_1C3) }`
   to both `OnTransition` scripts ([§2](#2-which-days-and-how-that-is-checked)). This only moves
   the attendant.
3. **The tables.** Sunday is set `0 / 2 = 0`: the Johto set, even with the National Dex.
   Opponents get only their `day` 7 rows. For a Sunday set of its own, see
   [Add a fifth wild set](#add-a-fifth-wild-set).
4. **The phone** (optional): add `RTC_WEEK_SUNDAY` to `PhoneScript_Generic_OnlyTuesThursSat`
   (`phone_scripts_generic.c:154`).

To **remove** a day, drop its `Compare` in step 1 and make the guard fall through to
`msg_0246_00007`.

### Change the time limit

The 20 is written out in three places, and twice in the text:

```diff
--- src/field/field_control.c:843
-    if (bugContest->elapsed_time >= 20) {
+    if (bugContest->elapsed_time >= 30) {
--- src/field/scrcmd_pokemon_misc.c:1539
-    if (bugContest != 0 && bugContest->elapsed_time < 20) {
-        timeLeft = 20 - bugContest->elapsed_time;
+    if (bugContest != 0 && bugContest->elapsed_time < 30) {
+        timeLeft = 30 - bugContest->elapsed_time;
```

Then edit "You have 20 minutes." in `msg_0246_00015`. The time-left number is printed with 2
digits (`scrcmd_pokemon_misc.c:1543`), so keep it under 100.

### Change the number of Sport Balls

`bugContest->sport_balls = 20;` (`src/overlay_bug_contest.c:45`), plus "received 20 Sport
Balls" in `msg_0246_00014` and nothing else. `sport_balls` is a `u16`. How many digits the
battle's balls-left counter can show wasn't checked (`src/battle/battle_hp_bar.c:227`).

### Change the Sport Ball catch rate

`ballMultiplier = 15;` (`src/battle/battle_command.c:7282`) is in tenths: 20 is ×2, 10 is ×1.
The Sport Ball only exists in this battle, so nothing else changes.

### Change the scoring

Edit `BugContest_JudgePlayerMon` (`src/overlay_bug_contest.c:314-345`). For example, count IVs
double and drop HP:

```diff
     score += stat_total * 100 / (31 * NUM_STATS);
-    score += GetMonData(mon, MON_DATA_HP, NULL) * 100 / GetMonData(mon, MON_DATA_MAX_HP, NULL);
+    score += stat_total * 100 / (31 * NUM_STATS);
```

The opponents don't use this function. Their scores are the `score` ± `randmod` columns of
`mushi_trainer.csv`, so if you change how high players can score, rescale those columns too, or
the contest gets much easier or harder. `score` is a `u16` and is printed with 3 digits.

To score species differently, change the `score` column of `mushi_encount.csv` (a `u8`).

### Change the prizes

Edit the `switch` in `BugContest_Judge` (`src/overlay_bug_contest.c:105-127`). The text shows the
item's name, so nothing else is needed. For example, a Master Ball for first and a Moon Stone for
second:

```diff
     case 0: // First Place
-        if (bugContest->national_dex) {
-            rand = LCRandom() % 10;
-        } else {
-            rand = 0;
-        }
-        if (rand < 6) {
-            bugContest->prize = ITEM_SUN_STONE + rand;
-        } else {
-            bugContest->prize = ITEM_SHINY_STONE + rand - 6;
-        }
+        bugContest->prize = ITEM_MASTER_BALL;
         break;
     case 1:
-        bugContest->prize = ITEM_EVERSTONE;
+        bugContest->prize = ITEM_MOON_STONE;
         break;
```

`rand` is then unused; remove its declaration if the compiler complains. Only one item is given
(`SetVar VAR_SPECIAL_x8005, 1`, `scr_seq_0151.s:319`).

### Add a contest Pokémon

Each set has exactly 10 rows, so to add a Pokémon, **replace** one. For example, Heracross
instead of Paras on National Dex Tuesdays (`mushi_encount.csv`, set 1, row 8):

```diff
-SPECIES_PARAS,27,34,10,80
+SPECIES_HERACROSS,27,34,10,100
```

Keep the `rate` column as it is unless you mean to change the odds ([§5](#5-the-wild-pokémon)):
each row's `rate` must be lower than the one above it, and the last row's must be 0.

For an NPC to show off the new Pokémon, change one of the rows for `1,2` in `mushi_trainer.csv`,
e.g. Abby's (rows 19-20, both Paras):

```diff
-1,2,SPECIES_PARAS,280,50
+1,2,SPECIES_HERACROSS,300,40
```

Each contestant must keep exactly 8 rows (`8 *` is hard-coded, `src/overlay_bug_contest.c:270-272`),
and on every possible day at least one row must pass the filter. The retail file always has
two `0,7` rows per contestant. With none, `LCRandom() % k` divides by zero (line 281). `randmod`
must not be 0 either (line 282).

**More than 10 per set:** raise `BUGMON_COUNT` (`include/bug_contest_internal.h:39`) and give
**every** set that many rows. The `BugContest` struct grows, but it isn't saved.

### Add a fifth wild set

The set index is `day_of_week / 2` (`src/overlay_bug_contest.c:305`). For a set of its own on a
new day, add 10 rows at the end of `mushi_encount.csv` (set 4) and choose it in code:

```diff
     if (bugContest->national_dex) {
-        set = bugContest->day_of_week / 2; // Tuesday -> 1, Thursday -> 2, Saturday -> 3
+        if (bugContest->day_of_week == RTC_WEEK_SUNDAY) {
+            set = 4;
+        } else {
+            set = bugContest->day_of_week / 2; // Tuesday -> 1, Thursday -> 2, Saturday -> 3
+        }
     } else {
```

Opponents for that day need rows with `day` 0 (or rely on their `day` 7 rows).

### Run the contest on another map

The C side doesn't care which map you're on: while `FLAG_UNK_996` is set, any grass uses the
contest table. These parts name National Park:

| Tied to National Park | Where |
|---|---|
| the warp to judging (from C) | `BugContest_WarpToJudging`: `MAP_NATIONAL_PARK`, 46, 50 (`src/field_misc_events.c:394-397`) |
| the warp to judging (from scripts) | `_0076`: `Warp MAP_NATIONAL_PARK, 0, 46, 50, DIR_NORTH` (`scr_seq_0151.s:41`) |
| the warp into the contest area | both gates: `warp(MAP_NATIONAL_PARK_BUG_CATCHING_CONTEST, 0, 75, 39, DIR_WEST)` |
| starting the judging | National Park's frame table `VAR_UNK_40F7, 1: std_bug_contest_judging` |
| clearing `FLAG_UNK_996` | `NationalPark_OnTransition` (`scripts.pory:60`, `:77`) |
| lining up the contestants | `NationalPark_OnResume`, moving objects 10-19; the judging script also uses objects 10-19 (`_04FD`) and moves the camera with object 241 |
| the contest area's NPCs | objects with the `FLAG_HIDE_BUG_CONTESTANT_*` flags and `_during` scripts in `NationalPark_BugCatchingContest/map.json` |
| phone and music | `MAP_NATIONAL_PARK` in `gear_phone_calls.c:216`, `phone_scripts_generic.c:132`, `:144`; `sys_flags.c:16-18` |

To move it:

1. A contest map with grass and a land encounter `rate` above 0 ([wild-encounters.md](wild-encounters.md)).
   Copy the flags of `NationalPark_BugCatchingContest/map.json` (`allow_escaping`, `allow_fly`,
   `allow_cycling` false) so the player can't leave without the guard.
2. Copy the ten contestant objects with their flags and `_during` scripts if you want them.
3. An entry NPC whose script does `callstd(std_bug_contest_guard_start)` and then, if
   `VAR_UNK_4118 == 1`, warps to your contest map, like
   `Route36_NationalParkGatehouse_EventScript_Attendant`. Any way out of the contest map should go
   through a script that calls `std_bug_contest_guard_ask_end`.
4. A judging map with a frame table `VAR_UNK_40F7, 1: std_bug_contest_judging` and an
   `OnTransition` that clears `FLAG_UNK_996` when `VAR_UNK_40F7` is 1. Give it objects 10-19 for
   the contestants (or edit `_04FD` and the `OnResume` loop) and a prize clerk with script 10428.
5. Change the two judging warps (C and `_0076`) to that map and position.
6. Optional: add the new maps to `sMusicOverrideMap` and to the phone checks.

[npcs-and-scripts.md](npcs-and-scripts.md) and [maps-and-warps.md](maps-and-warps.md) cover the
objects, frame tables and warps.

## Not verified

- Nothing in this guide was tried in game. Everything comes from reading the code and data at the
  cited lines.
- None of the §12 recipes were built. The diffs are untested, including the new message
  `msg_0246_00088`, the Heracross rows and the fifth set.
- The battle's balls-left display for counts of 100 or more.
- Whether the lead's ability (Synchronize, Cute Charm, Intimidate, Keen Eye...) affects contest
  encounters. `generateWildNonShinyAndAddToParty` gets the lead, but this wasn't traced.
- Surfing during a contest: the battle setup becomes a contest battle (`encounter_check.c:279`),
  but the surf branch doesn't use the contest table. The contest area may have no water anyway;
  not checked.
- Why `NationalPark_OnTransition` also clears `FLAG_UNK_996` on Tuesdays, Thursdays and
  **Fridays** (`scripts.pory:64-66`, not Saturdays). Judging clears it on every day through the
  `VAR_UNK_40F7` branch either way.
- What `ChangeObjectMovement VAR_SPECIAL_x8005, 2` in `_04FD` does to objects 10-19.
- `msg_0246_00002`, `00008`, `00009`, `00011`, `00012`, `00024` and `00025` are empty entries. No
  script was found using them.
