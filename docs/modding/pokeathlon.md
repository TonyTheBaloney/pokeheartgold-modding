<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# The Pokéathlon

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The Pokéathlon is the minigame contest in the Pokéathlon Dome. You pick three
Pokémon. They play three events (solo) or four (the multi-course reception and
link play) against three other teams. Each event gives up to 200 points. Bonuses
are added at the closing ceremony. The total becomes **Athlete Points** (AP), which
you spend in the Athlete Shop. A win also gives your three Pokémon a **medal**.

Every Pokémon has five Performance stats: Power, Stamina, Skill, Jump and Speed.
Each is 1 to 5 stars. The stars come from a per-species table, moved up or down by
nature, the day of the month and Aprijuice.

This guide covers where all of that lives and how to change it. To give a **new
species** its Pokéathlon data, see
[adding-a-species.md](adding-a-species.md#11-pokéathlon) (and the note in
[§9](#9-how-to-change-a-species-stats) about a second table it doesn't mention).

## Where things are

| What | File |
|---|---|
| per-species stars (base, min, max) | `files/poketool/personal/performance.narc`, 20 bytes a member (binary) |
| species → member | `sPokeathlonPerformanceArcIdxs`, `src/pokemon.c:4447`; a second copy, `gPokeathlonPerformanceFileIds`, `asm/pokeathlon_course_data.s:350` |
| today's stars (nature, day, Aprijuice) | `CalcBoxMonPokeathlonPerformance` `src/pokemon.c:4972`, `CalcBoxmonPokeathlonStars` `src/pokemon.c:5017` |
| Aprijuice: what a juice does | `ApricornBox_FeedAprijuice`, `src/application/apricorn_box/apricorn_box_overlay.c:111` |
| Aprijuice: where it is kept | `PartyExtra.aprijuiceModifiers`, `include/pokemon_types_def.h:321` |
| courses → events | `gPokeathlonCourseEventIds`, `asm/pokeathlon_course_data.s:283`; Master Course sets at `:288` |
| event code (all ten, plus the course) | overlay `OVY_96`, `main.lsf:1267`; sources in `src/pokeathlon/` |
| event score → points | `src/pokeathlon/pokeathlon_event_points.c`; tables at `asm/pokeathlon_event_data.s:199-224` |
| ceremony bonuses, winner | `src/pokeathlon/pokeathlon_course_ceremony.c` |
| what is saved after a course | `PokeathlonCourse_SaveResults`, `src/pokeathlon/pokeathlon_course_flow.c:1100` |
| save layout | `PokeathlonSave`, `include/pokeathlon/pokeathlon_save.h:52` |
| NPC teams | NARC `files/a/2/5/8` (100 teams), picked by `PokeathlonCourse_ChooseNpcTeams`, `pokeathlon_course_flow.c:1788` |
| per-event tuning (stars → speed, jump height...) | NARC `a/1/7/0`, read by each event ([§6](#6-events-and-their-stats)) |
| reception scripts | `files/fielddata/script/scr_seq/scr_seq_0167.s` (std script `_std_pokeathlon`), `scr_seq_0166.s` |
| Athlete Shop stock | `src/scrcmd_mart.c:251` (daily items), `:459` (Data Cards) |
| course, medal, event names | `files/msgdata/msg/msg_0313.json` (0-10 courses, 15-19 medals, 20-29 events) |

## 1. Stat order: read this first

The code uses **two orders** for the five stats, and the constant names don't
match what the game shows.

| Index | in `performance.narc` and in the course (`stats[]`) | in memory: stars, Aprijuice, nature table |
|---:|---|---|
| 0 | Power | Power |
| 1 | Speed | Stamina |
| 2 | Jump | Skill |
| 3 | Stamina | Jump |
| 4 | Skill | Speed |

The memory order is what the game prints. The Aprijuice screen labels row `i` with
message `5 + i` of `msg_0022` ("Power", "Stamina", "Skill", "Jump", "Speed")
(`src/application/apricorn_box/aprijuice_screen.c:604`). The juice names follow the
same order (`msg_0021` 20-24: Power, Stam., Skill, Jump, Speed Juice). The archive
order follows from `CalcBoxMonPokeathlonPerformance`, which copies archive byte 3
into memory index 1, 4 into 2, 2 into 3 and 1 into 4 (`src/pokemon.c:4996-5010`).
Hurdle Dash takes top speed from `stats[1]` and jump from `stats[2]`
(`src/pokeathlon/pokeathlon_hurdle_dash_runner.c:91-98`), which fits the archive
column.

The constants `PERFORMANCE_SKILL 1`, `PERFORMANCE_SPEED 2`, `PERFORMANCE_STAMINA 4`
and `ARCPERF_STAMINA 1`, `ARCPERF_SKILL 3`, `ARCPERF_SPEED 4`
(`include/constants/pokemon.h:126-139`) say otherwise. So do the field names of
`PokeathlonBox_MonStats` (`include/pokeathlon/pokeathlon_box.h:24`) and the
comments on `PokeathlonCourseMon.stats` and `PokeathlonCoursePerformance.stats`
(`include/pokeathlon/pokeathlon_course_internal.h:27`, `:284`). Only Power and Jump
come out the same either way. The names are only labels: the conversions are each
other's inverse, so the game is consistent. This guide uses the table above.

## 2. Per-species data

`files/poketool/personal/performance.narc` has 554 members of 20 bytes. A
species' member is `sPokeathlonPerformanceArcIdxs[species] + form`
(`src/pokemon.c:4995`). The table has 494 entries (species 0-493); species 0 and 1
both map to member 0, so species *n* is member *n − 1* up to where the alternate
forms are put in (Pikachu, 25 → 24; Snorlax, 143 → 142).

| Bytes | Field | Meaning |
|---|---|---|
| 0-4 | base stars, archive order | 0-4 means 1-5 stars |
| 5 | `isTall` | course only: sprites over the Pokémon sit higher |
| 6 | `collisionSizeClass` | course only: hit box size |
| 7 | `heightClass` | course only: 1-3 |
| 8 | `spriteSizeType` | course only |
| 9-18 | min, max for each stat | 5 pairs (min, max), archive order, also 0-4 |
| 19 | | unused by the code I read |

The C views: `PokeathlonBasePerformance` (`include/pokemon_types_def.h:329`; it
calls bytes 5-8 `dummy`) and `PokeathlonCoursePerformance`
(`include/pokeathlon/pokeathlon_course_internal.h:283`; it names bytes 5-8 and
leaves 9-19 as `unk09`).

Snorlax, member 142: `03 00 01 04 00 | 00 01 02 01 | 01 04  00 01  01 01  02 04  00 02 | 00`.
That is Power 4★ (range 2-5), Speed 1★ (1-2), Jump 2★ (fixed), Stamina 5★
(3-5), Skill 1★ (1-3). In all 554 members, min ≤ base ≤ max holds for every stat.

## 3. Today's stars: nature, day, Aprijuice

The stars a Pokémon has today are worked out every time from three things
(`src/pokemon.c:4972-5043`):

1. **A daily score per stat**, `dailyMod` (`src/pokemon.c:4990`):
   `natureMod + 2 * d − 9`, where `d` is the last decimal digit of
   `pidDigit + (day + 7 − i) * (day + i + 3)`. `pidDigit` is decimal digit `i` of the
   personality value and `day` is the day of the month. So `2d − 9` is −9..+9 and
   changes every day.
2. **The nature**, `sPokeathlonPerformanceNatureMods` (`src/pokemon.c:4944`), one row
   per nature in memory order. Most natures give +35 to one stat and −35 to another;
   the five neutral natures give +10 / −10 (Hardy: Power +10, Speed −10).
3. **Aprijuice**: the party slot's five signed bytes are added to the score
   (`src/pokemon.c:5026`).

The score becomes a star change (`PokeathlonStatScoreToStars`, `src/pokemon.c:4425`):

| Score | ≤ −120 | −119..−80 | −79..−40 | −39..−15 | −14..14 | 15..39 | 40..79 | 80..119 | ≥ 120 |
|---|---|---|---|---|---|---|---|---|---|
| Stars | −4 | −3 | −2 | −1 | 0 | +1 | +2 | +3 | +4 |

That change is added to the base and clamped to the species' min and max
(`src/pokemon.c:5028-5033`). The color says whether the result is at, above or
below the base (`STARS_AT_BASE`, `_ABOVE_BASE`, `_BELOW_BASE`,
`include/constants/pokemon.h:141`). The five results are packed 3 bits each into
`PokeathlonPerformanceStars.stars` (`src/pokemon.c:5041`).

So a nature alone (±35) moves a stat one star, and the daily part (±9) only matters
together with nature or juice near a threshold.

The summary screen draws star `i` (0-4) filled when `i ≤ stars` and hides it when
`i > max` (`PokemonSummary_GetPokeathlonStarStates`, `src/pokemon_summary.c:2583`).
It shows the stars only once `FLAG_UNK_982` is set
(`PokemonSummary_IsPokeathlonUnlocked`, `src/pokemon_summary.c:378`), which
`data/maps/PokeathlonDome/scripts.pory:210` does. See
[summary-screen.md](summary-screen.md).

### Aprijuice

A juice has five flavor values, one per stat in memory order, plus a mildness
(`ApricornJuice`, `include/apricorn_box.h:10`). Making and aging juice is outside
this guide. Feeding it (`ApricornBox_FeedAprijuice`,
`src/application/apricorn_box/apricorn_box_overlay.c:111`):

| Step | Code |
|---|---|
| strongest flavor's stat: `1.5 × amount`, +10 if the amount isn't 0 | `:139-142` |
| second flavor's stat: `1.5 × amount` | `:144` |
| the weakest flavor's stat loses a penalty: `total × (1 − 0.1 × (mildness / 25))` below mildness 200, `0.2 × total` from 200 to 254, `0.1 × total` at 255 (`total` = the two amounts) | `:145-153` |
| each value clamped to −127..127 and stored | `:154-163` |
| the Pokémon's mood changes (`ApplyMonMoodModifier(mon, 7)`) | `:164` |

A new juice **replaces** the old modifiers; it does not add to them (the old ones
are read but every slot is overwritten). Which flavor counts as strongest comes
from `ApricornJuice_RankFlavors` (`src/apricorn_box.c:279`).

The modifiers are kept per **party slot**, not in the Pokémon: `PartyExtraSub`, 5
bytes per slot, in the party save (`include/pokemon_types_def.h:316-323`). They are
cleared when a Pokémon is put into a slot from the PC, an in-game trade or a link
trade (`Party_SafeCopyMonToSlot_ResetAprijuiceModifiers`, `src/party.c:97`; callers
in `src/application/pc_box/pc_box.c:386`, `src/npc_trade.c:157`,
`src/wireless_trade_select_mon.c:2201`). I found no daily reset. PC Pokémon entered
from the box get no juice (`PokeathlonBox_GetBoxMonStats` passes `NULL`,
`src/pokeathlon/pokeathlon_box.c:333`).

## 4. Courses and events

The event ids (names: `msg_0313` 20-29; code: `gPokeathlonCourseEvents`,
`asm/pokeathlon_course_data.s:465`):

| Id | Event | Score order (`gPokeathlonEventScoreOrders`, `:164`) | Target (`gPokeathlonEventTargetScores`, `:230`) |
|---:|---|---|---:|
| 0 | Hurdle Dash | lower is better (time in frames) | 3000 |
| 1 | Pennant Capture | higher | 35 |
| 2 | Circle Push | higher | 40 |
| 3 | Block Smash | higher | 80 |
| 4 | Disc Catch | higher | 40 |
| 5 | Lamp Jump | higher | 350 |
| 6 | Relay Run | higher | 12288 |
| 7 | Ring Drop | higher | 70 |
| 8 | Snow Throw | higher | 30 |
| 9 | Goal Roll | higher | 3 |

The targets only matter for one flag: when every solo record beats its target,
`FLAG_UNK_0F1` is set (`PokeathlonCourse_BeatsAllEventTargets`,
`pokeathlon_course_flow.c:1511`; see
[unknown-flags-vars.md](unknown-flags-vars.md)).

The courses (`gPokeathlonCourseEventIds`, four bytes each; `0x0A` = no event):

| Id | Course (`msg_0313`) | Events | Medal(s) on a win |
|---:|---|---|---|
| 0 | Speed | Hurdle Dash, Pennant Capture, Relay Run | Speed |
| 1 | Power | Block Smash, Circle Push, Goal Roll | Power |
| 2 | Skill | Snow Throw, Goal Roll, Pennant Capture | Skill |
| 3 | Stamina | Ring Drop, Relay Run, Block Smash | Stamina |
| 4 | Jump | Lamp Jump, Disc Catch, Hurdle Dash | Jump |
| 5 | Speed & Jump | Hurdle Dash, Lamp Jump, Disc Catch, Relay Run | Speed, Jump |
| 6 | Jump & Skill | Lamp Jump, Disc Catch, Pennant Capture, Snow Throw | Skill, Jump |
| 7 | Skill & Power | Goal Roll, Snow Throw, Pennant Capture, Block Smash | Power, Skill |
| 8 | Power & Stamina | Block Smash, Circle Push, Goal Roll, Ring Drop | Power, Stamina |
| 9 | Stamina & Speed | Relay Run, Ring Drop, Hurdle Dash, Circle Push | Speed, Stamina |
| 10 | Master | one of 10 random sets (`gPokeathlonCourse10EventSets`, `:288`) | none |

Medals: `PokeathlonCourse_SetCourseMedals` (`pokeathlon_course_flow.c:1436`).

**Solo or four rounds.** The `Pokeathlon` script command
(`ScrCmd_Pokeathlon`, `src/scrcmd_c.c:4587`) takes a mode, an `isSupreme` byte, the
course and four result variables. Mode 0 (`POKEATHLON_COURSE_MODE_SOLO`,
`include/pokeathlon/pokeathlon_course_types_def.h:81`) plays 3 rounds and allows
courses 0-4; mode 1 (`_LINK`) plays 4 rounds and allows 5-10
(`PokeathlonCourse_ChooseEvents`, `pokeathlon_course_flow.c:1529`; rounds:
`pokeathlon_course_ceremony.c:652-657`). In mode 1 the free places are filled with
NPC teams (`pokeathlon_course.c:54-61`, `PokeathlonCourse_SetupNpcParticipants`).

**Supreme Cup** is not a course. It is `isSupreme = 1` on courses 0-4: the same
events, but NPC teams are taken 50 entries later in `a/2/5/8` (harder teams), and
the script pays more for a win ([§7](#7-athlete-points-medals-records)).

In `scr_seq_0167.s`:

| Script | Sets | Runs |
|---|---|---|
| `scr_seq_0167_000` (`:12`) | `VAR_TEMP_x400A = 0` | `Pokeathlon 0, 0, ...` courses 0-4 (menu → course id at `:133-156`) |
| `scr_seq_0167_001` (`:21`) | `VAR_TEMP_x400A = 1` (Supreme Cup reception) | `Pokeathlon 0, 1, ...` |
| `scr_seq_0167_002` (`:650`) | `VAR_TEMP_x400A = 2` | `Pokeathlon 1, 0, ...` courses 5-9 (`:770-793`) |
| same, Master Course | `VAR_TEMP_x400A = 3` (`:795-797`) | `Pokeathlon 1, 1, ...` course 10, so with `isSupreme = 1` |

The calls are at `:480-500`. `scr_seq_0166.s:286` is a second `Pokeathlon 1, 0`
call; I didn't trace that script.

## 5. Scoring

### Event points

Each event ends by calling `PokeathlonEvent_CalcPoints(list, event)`
(`src/pokeathlon/pokeathlon_event_points.c:17`). Events 0-8 convert each team's raw
score with a function from `gPokeathlonEventScorePointsFuncs`
(`asm/pokeathlon_event_data.s:214`). Every result is cut to 200
(`PokeathlonEvent_ClampPoints`, `:47`).

| Event | Points from the score | Line |
|---|---|---|
| Hurdle Dash | `11500 / (frames / 30)` | `:56` |
| Pennant Capture | `score × 3` | `:61` |
| Circle Push | `score × 3` | `:66` |
| Block Smash | `score` | `:71` |
| Disc Catch | `150 − 120 / (1 + score × 0.08)` (30 at 0, toward 150) | `:76`, `:43` |
| Lamp Jump | `score / 3.5` | `:81` |
| Relay Run | `score / 1024 × 10` | `:85` |
| Ring Drop | `score × 1.5` | `:90` |
| Snow Throw | `score × 3` | `:96` |
| Goal Roll | by rank: 100, 80, 70, 60 (`gPokeathlonEventRankPoints`, `asm/pokeathlon_event_data.s:199`), +5 per goal; tied teams get the lower place's points | `src/pokeathlon/pokeathlon_event_rank_points.c:11` |

Which kind each event uses is `gPokeathlonEventPointsCalcFuncs`
(`asm/pokeathlon_event_data.s:202`): `PokeathlonEvent_CalcPointsFromScores` for 0-8,
`PokeathlonEvent_CalcPointsFromRanks` for 9.

### The closing ceremony

The course total is built up during the ceremony (`pokeathlon_course_ceremony.c:551-700`):

| Step | Points | Code |
|---|---|---|
| Challenge Bonus, per team | `75 − Σ (base + 1)` over the 15 base stars of the three Pokémon, clamped 0..75. Read from `performance.narc`, so weak species earn more. | `PokeathlonCourseCeremony_CalcChallengeBonus`, `:1782` |
| No-miss bonus, per Pokémon that never failed, fell or impeded itself | 10 | `_GetNoMissPoints`, `:1679` |
| Points leader, per Pokémon with the most event points | 20 | `_GetPointsLeaderPoints`, `:1683` |
| Effort prize, per Pokémon with the most jumps, hits, failures or dashes (one kind picked at random) | 10 | `_GetEffortPrizePoints`, `:1687`; kind: `_ChooseEffortPrizeKind`, `:1809` |
| the event points of each round | 0-200 each | `CLOSING_STATE_COUNT_EVENT_POINTS`, `:649` |

Awards are chosen in `PokeathlonCourseCeremony_ChooseAwards` (`:1845`). Teams are
ranked by total (`_RankTeams`, `:1236`); a tie for first is broken by random
"drawing lots" (`_BreakTie`, `:2205`).

## 6. Events and their stats

All ten events are in overlay `OVY_96` with the course itself (`main.lsf:1267-1335`).
Each has a table of callbacks, `PokeathlonCourseEvent`
(`include/pokeathlon/pokeathlon_course_internal.h:344`: `init`, `draw`,
`onResults`, `exit`, `sendsOwnResult`), and a list of state functions
(`gPokeathlonCourseEventSteps`, `asm/pokeathlon_course_data.s:453`). The course
switches to the round's event in `PokeathlonCourse_State_StartRound`
(`pokeathlon_course_flow.c:667`).

An event reads a Pokémon's stars with `PokeathlonCourse_GetMonStats`
(`pokeathlon_course_flow.c:112`), archive order. NPC Pokémon always play with their
**base** stars (`pokeathlon_course_flow.c:1772-1776`); yours play with today's
stars. Each event turns stars into speeds and sizes through a member of NARC
`a/1/7/0`:

| Member | Read by |
|---:|---|
| 0, 10 | Hurdle Dash (`pokeathlon_hurdle_dash.c:376-377`) |
| 1, 11 | Circle Push (`pokeathlon_circle_push.c:530`, `:593`) |
| 2, 12 | Relay Run (`pokeathlon_relay_run.c:350`, `:384`) |
| 3 | Snow Throw (`pokeathlon_snow_throw.c:462`) |
| 4, 14 | Pennant Capture (`pokeathlon_pennant_capture.c:179`, `:198`) |
| 5 | Block Smash (`pokeathlon_block_smash_teams.c:328`) |
| 6, 16 | Lamp Jump (`pokeathlon_lamp_jump.c:404`, `:436`) |
| 7, 17 | Disc Catch (`pokeathlon_disc_catch_field.c:55`, `:163`) |
| 8, 11 | Goal Roll (`pokeathlon_goal_roll.c:304`, `:343`) |

Ring Drop reads none of these. I didn't work out the layout of these members.

## 7. Athlete Points, medals, records

`PokeathlonCourse_SaveResults` (`pokeathlon_course_flow.c:1100`) runs after the
ceremony:

| What | Rule | Code |
|---|---|---|
| Athlete Points | + the course total; ×2 on course 10 | `:1114-1118` |
| medals | on a win, the course's medal(s) for each of the three species | `:1105`, `:1436` |
| course record | solo win: best total, round points and Pokémon of courses 0-4 | `_SaveCourseRecord`, `:1143` |
| event records | top 5 per event, solo and link (link with trainer names) | `:1175`, `:1213` |
| statistics | courses joined/won/lost, event wins, the Pokémon's counters (capped 9,999,999) | `_SaveStatistics`, `:1371` |
| Friendship Room statues | your three Pokémon, on a win | `_SaveFriendshipStatues`, `:1412` |
| flags | `FLAG_UNK_0EF` all five course records, `_0F0` a species with all medals, `_0F1` all targets | `:1107`, `:1127`, `:1134` |

Then the reception script adds more (`scr_seq_0167.s`):

| When | AP | Line |
|---|---:|---|
| 1st place, normal reception | +100 | `:366` |
| 1st place, Supreme Cup | +300 | `:370` |
| reception 3 (mode 1), 1st | +500 | `:1003` |
| reception 3, 2nd | +200 | `:1010` |

Fans go up 10 for 1st, 5 for 2nd and down 5 for 4th (`AdjustPokeathlonStat11`,
`scr_seq_0167.s:344-361`; `src/field/scrcmd_pokemon_misc.c:807`). Statistics also
unlock the five decorations of the Dome: dashes ≥ 5000, courses ≥ 50, switches
≥ 200, course wins ≥ 100, each event won ≥ 50 times (`scr_seq_0167.s:413-470`,
stat ids in `ScrCmd_GetPokeathlonStat`, `scrcmd_pokemon_misc.c:762`).

AP are capped at 99,999 (`PokeathlonSave_AddAthletePoints`,
`src/pokeathlon/pokeathlon_save.c:93`). Scripts use `GiveAthletePoints`,
`TakeAthletePoints`, `CheckAthletePoints` (`src/overlay_22.c:96-117`).

### What is saved

`PokeathlonSave` is save array `SAVE_POKEATHLON` (37), 0xB80 bytes
(`include/pokeathlon/pokeathlon_save.h:52`). See [save-data.md](save-data.md).

| Offset | Field | Holds |
|---|---|---|
| 0x000 | `prefix.legacy.bytesDC` | 5 × `PokeathlonCourseBestRecord` (0x2C each, `pokeathlon_course_internal.h:444`) |
| 0x0DC | `prefix.legacy.bytes1F0` | medals: one byte per species, at `species − 1`, bits 0-4 = Speed, Power, Skill, Stamina, Jump (`POKEATHLON_MEDAL_*`, `pokeathlon_course_internal.h:220`) |
| 0x2CC | `recordsSolo[10]` | top 5 + times played, per event id |
| 0x484 | `recordsLink[10]` | the same with trainer names |
| | `soloEventBestPoints` | points of the best solo result, per event (10 × u16) |
| | `statistics` | `PokeathlonStatistics` (`pokeathlon_save.h:6`) |
| 0xB74 | `athletePoints` | |
| | `dataCardsBought` | bits 0-26 |
| | `dailyItemsBought` | 16 bits, cleared each day (`src/field_time_events.c:93`) |

Separately: Aprijuice (party save, [§3](#aprijuice)) and the Friendship Room statues
(`SAVE_POKEATHLON_FRIENDSHIP_RECORDS`, `pokeathlon_save.h:70`).

## 8. The Athlete Shop and Data Cards

**Daily items** (`ScrCmd_PokeathlonDailyMart`, `src/scrcmd_mart.c:440`). The stock is
one list per weekday, `sPokeathlonPrizeExchangePriceOverrides_*`
(`src/scrcmd_mart.c:251-418`), picked by `date.week` (0 = Sunday), plus 7 once the
National Dex is obtained (table at `:420`). Despite the name, these are the whole
stock, not price overrides (comment at `:247-250`). Each entry is
`{ item, AP price }`, ended by `0xFFFF`. Each row can be bought once a day: the bit
is the row number (`src/overlay_03/shop_menu.c:957`). Apricorns go to the Apricorn
Box instead of the Bag (`MartData_Inventory_AddApricornOrItem`, `shop_menu.c:941`).

**Data Cards** (`ScrCmd_PokeathlonDataCardMart`, `src/scrcmd_mart.c:512`). 27 cards,
`ITEM_DATA_CARD_01`-`27` (items 505-531). The shop shows the group of six that holds
the first card not yet bought (`sPokeathlonDataCardPrices`, `:502`). Buying a card
sets bit `item − 505` (`shop_menu.c:959`); it is not put in the Bag. A card shows
one line of the records board: `sPokeathlonRecordFlags`
(`src/overlay_03/pokeathlon_records.c:109`) gives each line the card that unlocks
it, 0 for always shown. The board is opened with `ShowPokeathlonRecords`
(`src/field/scrcmd_pokemon_misc.c:940`).

The Dome's drink machine also takes AP: 50, 80, 100 for Fresh Water, Soda Pop,
Lemonade (`data/maps/PokeathlonDome_Interior_1F/scripts.pory:608-700`).

## 9. How to: change a species' stats

Edit its member of `performance.narc`. Unpack and repack with `nitroarc` as in
[adding-a-species.md](adding-a-species.md#0-before-you-start). Example: Snorlax
(member 142) gets Speed 3★, range 2-4★.

```sh
NARC=build/heartgold.us/tools/nitroarc/nitroarc
mkdir -p /tmp/narc && cp files/poketool/personal/performance.narc /tmp/narc/
$NARC -xf /tmp/narc/performance.narc
python3 - <<'EOF'
p = '/tmp/narc/performance.narc.d/00142.bin'
b = bytearray(open(p, 'rb').read())
b[1] = 2              # Speed (archive index 1) base: 3 stars
b[9 + 2*1] = 1        # Speed min: 2 stars
b[10 + 2*1] = 3       # Speed max: 4 stars
open(p, 'wb').write(b)
EOF
ls /tmp/narc/performance.narc.d | sort > /tmp/narc/order.txt
$NARC -cf files/poketool/personal/performance.narc -T /tmp/narc/order.txt /tmp/narc/performance.narc.d
```

Rules:

- Use the **archive order** ([§1](#1-stat-order-read-this-first)).
- Keep values 0-4 and min ≤ base ≤ max. The summary draws 5 star sprites
  (`src/pokemon_summary.c:2528`); the packed field has 3 bits.
- Base stars also set the Challenge Bonus ([§5](#the-closing-ceremony)) and the NPC
  teams' strength ([§6](#6-events-and-their-stats)).

**Forms and new species.** The game finds the member in two tables that must stay
the same: `sPokeathlonPerformanceArcIdxs` (`src/pokemon.c:4447`) for the stars, and
`gPokeathlonPerformanceFileIds` (`asm/pokeathlon_course_data.s:350`) for the course
(`PokeathlonCourse_GetPerformanceFileId`, `pokeathlon_course_flow.c:427`: Challenge
Bonus, NPC stats, sprite sizes). Both have 494 entries and are identical today.
[adding-a-species.md](adding-a-species.md#11-pokéathlon) only extends the first. A
new species entered in a course would read past the end of the second; add the same
entry there.

## 10. How to: change course composition

Edit `gPokeathlonCourseEventIds` (`asm/pokeathlon_course_data.s:283`). Rows are
four bytes, courses 0-9 in order. Example: Speed Course plays Lamp Jump instead of
Pennant Capture:

```diff
 gPokeathlonCourseEventIds:
-	.byte 0x00, 0x01, 0x06, 0x0A, 0x03, 0x02, 0x09, 0x0A, 0x08, 0x09, 0x01, 0x0A
+	.byte 0x00, 0x05, 0x06, 0x0A, 0x03, 0x02, 0x09, 0x0A, 0x08, 0x09, 0x01, 0x0A
```

Things that depend on this table:

- Solo courses use the first 3 bytes; keep the 4th at `0x0A`. Three rounds are built
  into the result code (`roundPoints[3]`, the loops of 3 in
  `pokeathlon_course_flow.c:1175`, `:1262`), so more rounds is a code change.
- `PokeathlonCourse_FindCourseId` (`src/pokeathlon/pokeathlon_course.c:384`) finds
  the course again by matching the events (3 for solo, 4 for mode 1) and returns the
  first matching row. The ceremony uses it for the medal names and graphics
  (`pokeathlon_course_ceremony.c:1496`). Keep every row's events distinct from the
  rows before it.
- Medals, NPC team pools and names are keyed by the course id, not the events.
- The Master Course picks one of ten rows of `gPokeathlonCourse10EventSets`.

**NPC teams.** `a/2/5/8` has 100 members of 8 bytes: three species (u16), a name id
in `msg_0310`, an intro message id (`PokeathlonCourseNpcTeam`,
`pokeathlon_course_internal.h:486`). Course *c* (0-9) draws from teams `5c+1`..`5c+5`,
course 10 from 26-50, and `isSupreme` adds 50. The
reception starts the Master Course with `isSupreme = 1` ([§4](#4-courses-and-events)), so it
uses teams 76-100
(`PokeathlonCourse_ChooseNpcTeams`, `pokeathlon_course_flow.c:1788`). Team 1 is
Pikachu, Teddiursa, Vulpix. Each team also has an overworld sprite,
`gPokeathlonNpcTeamSpriteIds` (`asm/pokeathlon_course_data.s:335`, 100 entries).

## 11. How to: change scoring and prizes

| To change | Edit |
|---|---|
| how an event's score becomes points | its function in `src/pokeathlon/pokeathlon_event_points.c` (e.g. Ring Drop's `1.5` at `:92`) |
| the 200-point cap | `PokeathlonEvent_ClampPoints` (`:47`) and `pokeathlon_event_rank_points.c:38` |
| Goal Roll's place points | `gPokeathlonEventRankPoints`, `asm/pokeathlon_event_data.s:199` |
| ceremony bonuses | `pokeathlon_course_ceremony.c:1679-1689` (10/20/10) and the 75 in `:1786` |
| AP from the course total | `pokeathlon_course_flow.c:1114-1118` |
| AP for winning | `SetVar VAR_TEMP_x4009, ...` in `scr_seq_0167.s:366`, `:370`, `:1003`, `:1010` |
| event targets | `gPokeathlonEventTargetScores`, `asm/pokeathlon_course_data.s:230` |
| medals per course | `PokeathlonCourse_SetCourseMedals` (`pokeathlon_course_flow.c:1436`) and, for the ceremony text, `PokeathlonCourseCeremony_GetCourseMedal` (`pokeathlon_course_ceremony.c:1915`) |
| daily shop | the weekday lists in `src/scrcmd_mart.c:251-418` |
| Data Card prices | `src/scrcmd_mart.c:459-508` |

Example, a cheaper Rare Candy on Mondays:

```diff
 const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Monday[] = {
     ...
-    { ITEM_RARE_CANDY,   2000 },
+    { ITEM_RARE_CANDY,   1000 },
     { 0xFFFF,            0    },
 };
```

Limits for the daily lists: at most 12 items. `ScrCmd_CheckPokeathlonDailyMartHasStock`
counts 12 (`src/scrcmd_mart.c:548-557`) and the bought flags are 16 bits. Don't
reorder rows during a day: the bought bit is the row number. Data Cards must keep
item ids 505-531 in order, since the bit is `item − 505`.

## 12. What adding an event would involve

There is no data-only way: an event is a mini-game in C. Everything that counts
events assumes ten:

| Place | Sized for 10 |
|---|---|
| `gPokeathlonCourseEvents`, `gPokeathlonCourseEventSteps` | `asm/pokeathlon_course_data.s:453`, `:465` |
| score order, target | `:164`, `:230` (`PokeathlonCourse_BeatsAllEventTargets` loops 10) |
| points functions | `asm/pokeathlon_event_data.s:202`, `:214` |
| save: `recordsSolo[10]`, `recordsLink[10]`, `soloEventBestPoints`, `eventFirstPlaces[10]` | `include/pokeathlon/pokeathlon_save.h` (changes the save layout) |
| event name | `BufferPokeathlonEventName` asserts `< 10` (`src/message_format.c:574`); names at `msg_0313` 20-29, and entry 30 does not exist (the file has 30) |
| event intro | graphics members `event + 32/42/52` of `a/2/1/9`, text `msg_0309` 177/198/209 + event, `sPokeathlonEventIntroMascotAnims[10]` (`src/pokeathlon/pokeathlon_event_intro.c:218`, `:591-672`) |
| event records app | `src/pokeathlon/pokeathlon_event_record.c` (asserts `< 10`, loops 10) |
| trophies | `src/pokeathlon/pokeathlon_trophies.c:511`, `:617` |
| script stat ids 0-9 = events | `ScrCmd_GetPokeathlonStat`, `scrcmd_pokemon_misc.c:762` |

The new event needs its own `PokeathlonCourseEvent` (init/draw/results/exit), its
state functions, code that calls `PokeathlonEvent_CalcPoints`, and the link
messages the others use. It also has to fit in `OVY_96` with the rest. Swapping an
existing event for a new one keeps all the counts at ten and is the smaller job.

## Not verified

Nothing here was tried in game or built. In particular:

- The stat order in [§1](#1-stat-order-read-this-first) comes from screen labels,
  juice names and how Hurdle Dash, Relay Run and Lamp Jump use the stats; the
  Snorlax and Shuckle data fit it. It was not checked against the game's screens.
- The `performance.narc` layout and the Snorlax bytes were read with a small script;
  the meanings of bytes 5-8 come from the field names in
  `PokeathlonCoursePerformance`, not from tests. Byte 19 was not traced.
- The recipes in §9-§11 (narc edit, course diff, shop diff) were not built. The
  `nitroarc` commands are copied from adding-a-species.md.
- That a second table (`gPokeathlonPerformanceFileIds`) must be extended for a new
  species is read from the code; reading past its end was not reproduced.
- `scr_seq_0166.s` and the third reception's conditions were not traced; how mode 1
  behaves without a link partner was not checked.
- The Aprijuice formula was read, not tested; the flavor ranking (`ApricornJuice_RankFlavors`) was only skimmed.
- The layout of the `a/1/7/0` tuning members and of the event score units (frames,
  Relay Run's /1024) was not worked out.
- The drink-machine item mapping (30, 31, 32 → Fresh Water, Soda Pop, Lemonade) is from
  `include/constants/items.h`; the machine was not used.
