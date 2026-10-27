<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Move tutors and the Move Relearner

> AI-generated; not affiliated with pret. See AI.md at the repository root.

HeartGold has five NPCs that teach moves outside of level-up and TMs, plus the Move
Deleter. The Move Relearner and the one-move tutors open the same screen (overlay 68).
The Frontier tutors use a script menu and a per-species bit table instead.

| NPC | Where | Teaches | Price | Who can learn | Code |
|---|---|---|---|---|---|
| Move Maniac (Move Relearner) | Blackthorn City, move tutor house | level-up moves at or below the current level | 1 Heart Scale | everyone | `monhasrelearnablemoves`, `moverelearnerinit` |
| Grandma Wilma | same house | Draco Meteor | free | Dragon type, friendship 255 | script check, then `movetutorinit` |
| Old man ("ultimate moves") | same house | Blast Burn / Hydro Cannon / Frenzy Plant | free | 12 starters (species numbers in the script), friendship 255 | script check, then `movetutorinit` |
| Move Deleter | same house | forgets a move | free | not an egg, at least 2 moves | `openlearnforgetmove` |
| Three Frontier tutors | Frontier Access, move tutor house | 51 moves | 32-64 BP | `waza_oshie.json` | `std_frontier_move_tutor_1`-`_3` |
| Headbutt tutor | Ilex Forest | Headbutt | free | `waza_oshie.json` (`TUTOR_HEADBUTT`) | `moncanlearnheadbuttfromtutor` |

pokeemerald comparison: there, each tutor is a script that calls `ChooseMonForMoveTutor`
and the species list is `sTutorLearnsets`. Here the Frontier and Headbutt lists are one
bit table in `waza_oshie.json`, and the other tutors decide in their script.

## Where things are

| What | File |
|---|---|
| Blackthorn NPCs (relearner, deleter, Wilma, ultimate moves) | `data/maps/Blackthorn_MoveTutorHouse/scripts.pory` |
| Frontier tutor NPCs | `data/maps/FrontierAccessMoveTutorHouse/scripts.pory` (each does `callstd(std_frontier_move_tutor_N)`) |
| shared Frontier tutor script | `files/fielddata/script/scr_seq/scr_seq_0002.s` (std 10440-10442, `src/script_manager.c:36`) |
| Frontier tutor text, menu rows | `files/msgdata/msg/msg_0748.json` |
| Headbutt tutor | `IlexForest_EventScript_FatMan`, `data/maps/IlexForest/scripts.pory:875` |
| tutor move list, prices, which NPC | `sTutorMoves`, `src/field/scrcmd_move_tutor.c:38` |
| `TUTOR_*` bit numbers | `include/constants/moves.h:524-575` |
| `MOVE_TUTOR_NPC_*` | `include/constants/scrcmd.h:45-48` |
| who learns which tutor move | `files/fielddata/wazaoshie/waza_oshie.json` → `waza_oshie.bin` (template `waza_oshie.json.txt`) |
| relearner script commands | `src/scrcmd_move_relearner.c` |
| eligible level-up moves | `MoveRelearner_GetEligibleLevelUpMoves`, `src/move_relearner.c:17` |
| the relearner/tutor screen | `src/application/move_relearner/move_relearner_app.c` (overlay 68, launched by `MoveRelearner_LaunchApp`, `src/launch_application.c:1247`) |
| screen text | `files/msgdata/msg/msg_0747.json` (0-10 tutor wording, 11-21 relearner wording) |
| move names | `msg_0750.json` |

## 1. The Move Relearner

`Blackthorn_MoveTutorHouse_EventScript_FatMan`:

1. First talk: sets `FLAG_MET_MOVE_MANIAC` and ends. Nothing is taught that time.
2. `hasitem(ITEM_HEART_SCALE, 1, ...)`; without one he says to come back.
3. Party select, egg check, then `monhasrelearnablemoves(VAR_SPECIAL_RESULT, slot)`.
4. `moverelearnerinit(slot)` opens the screen; `moverelearnergetresult(var)` gives 0
   (a move was learned) or 255 (cancelled).
5. Only on 0: `takeitem(ITEM_HEART_SCALE, 1, ...)`. Cancelling costs nothing.

### Which moves are listed

`MoveRelearner_GetEligibleLevelUpMoves` (`src/move_relearner.c:17`) reads the
species' level-up learnset (`level_up_learnsets.json`, with the form's own learnset
for Deoxys, Wormadam, Giratina, Shaymin, Rotom) and keeps each move that

- has a level **at or below the Pokémon's current level**,
- isn't one of its four current moves,
- isn't already in the list (a move listed twice in the learnset shows once).

The list keeps learnset order and ends with `0xFFFF`. Egg moves, TM moves, tutor
moves and moves from a pre-evolution are **not** included. A Pokémon that evolved
before learning a move of its old form can't get it back here.

`monhasrelearnablemoves` builds the same list and returns TRUE if it isn't empty.

**Learnset size:** the buffers are `LEVEL_UP_LEARNSET_MAX` (21) halfwords
(`include/pokemon.h:18`). A learnset member is moves + `0xFFFF`, padded to 4 bytes, so

- up to 19 moves: fits;
- 20 moves (10 retail species: Arbok, Dewgong, Mr. Mime, Steelix, Forretress,
  Medicham, Exploud, Dusclops, Dusknoir, Yanmega): the file is 44 bytes, 2 more than
  the buffer. Retail lives with it;
- 21 moves: also 2 bytes over, and the loop stops at 21 entries before reaching the
  end marker, so the list given to the screen **is never terminated**. The screen
  then reads garbage after it.

The level-up code elsewhere allows 21 ([pokemon.md](pokemon.md#level-up-learnsets)).
If you give a species 20 or 21 moves, apply [§6.2](#62-relearner-learnsets-of-21-moves).

### The screen

`moverelearnerinit` fills a `MoveRelearnerArgs` (`include/move_relearner.h`) with
`type = MOVE_RELEARNER_RELEARN` (the C passes a literal 1) and launches overlay 68.
The screen shows the move list on the bottom screen, and for the selected move its
type (or contest category), PP, power, accuracy and description.

- Choosing a move with fewer than 4 known moves: "Should the move X be remembered?"
  → it goes into the first empty slot.
- With 4 moves: "...can't learn more than four moves. Delete an existing move?" →
  the summary screen opens on the moves page with the new move shown
  (`MoveRelearner_OpenSummary`). **HMs can't be picked** there, because
  `moveToLearn` is set (`src/pokemon_summary.c:940`). Saying no asks "Give up making
  the Pokémon remember X?".
- `MoveRelearner_TeachMove` (`:922`) writes the move, sets its PP Ups to 0 and PP to
  the move's base max PP.

### Retail quirk: the list is freed before the screen reads it

`StartMoveRelearner` (`src/scrcmd_move_relearner.c:43`) launches the app and then
immediately frees `eligibleMoves`. `FieldSystem_LaunchApplication` only creates the
overlay manager; the screen's `Init` runs on a later frame, reads
`args->eligibleMoves`, and reads it again every time it comes back from the summary
screen. It works in retail because nothing is allocated from `HEAP_ID_FIELD3` in
between. If you add code that allocates there (or change heaps), the list can be
overwritten. [§6.3](#63-keep-the-relearner-list-alive) fixes it.

## 2. One-move tutors (Draco Meteor, ultimate moves)

Both are pure scripts in `Blackthorn_MoveTutorHouse/scripts.pory`. The C side,
`movetutorinit(slot, move)` (`ScrCmd_MoveTutorInit`), **checks nothing**. It builds a
one-entry list `{ move, 0xFFFF }` and opens the same screen as the relearner with
`type = MOVE_RELEARNER_TUTOR`, so the text is the tutor wording (`msg_0747` 0-10:
"Teach which move to X?"). Result: `moverelearnergetresult(var)`, 0 or 255.

The scripts check everything before that:

| Check | Grandma Wilma (Draco Meteor) | Old man (ultimate moves) |
|---|---|---|
| species | `getmontypes`: either type is 16 (`TYPE_DRAGON`) | `_05F4`: species 6/157/257/392 → Blast Burn, 9/160/260/395 → Hydro Cannon, 3/154/254/389 → Frenzy Plant |
| party pre-check | loops the party; if no Dragon type without the move, "none of the Pokémon with you now can learn the move" | none |
| already knows it | `monhasmove` | `monhasmove` |
| friendship | `mongetfriendship` < 255 → refuses | same |
| first-talk flag | `FLAG_UNK_186` | `FLAG_UNK_187` |

Both are free and can be repeated. The species list for the old man is also on the
memo in the house (`Blackthorn_MoveTutorHouse_EventScript_LittleBoy`); change both.

## 3. The Frontier tutors

Three NPCs in `FrontierAccessMoveTutorHouse` each call one entry of
`scr_seq_0002.s`. The entry sets:

| Std | `VAR_SPECIAL_x8000` (tutor) | `VAR_TEMP_x400F` (text offset) | `VAR_SPECIAL_x8007` |
|---|---|---|---|
| `std_frontier_move_tutor_1` | `MOVE_TUTOR_NPC_FRONTIER_TOP_LEFT` (0), 14 moves | 0 | 0 |
| `std_frontier_move_tutor_2` | `MOVE_TUTOR_NPC_FRONTIER_TOP_RIGHT` (1), 21 moves | 12 | 1 |
| `std_frontier_move_tutor_3` | `MOVE_TUTOR_NPC_FRONTIER_BOTTOM_RIGHT` (2), 16 moves | 24 | 2 |

Messages 4-15 of `msg_0748` are the first tutor's lines, 16-27 the second's, 28-39
the third's; the script prints `4 + offset`, `7 + offset` and so on. 40 is the egg
line, 0-3 are the menu rows (below).

The flow: party select → egg check → `gettutormovelistpagecount(slot, tutor, var)`;
0 means "no move I can teach" → `movetutorchoosemove(slot, tutor, page, VAR_SPECIAL_RESULT)`
shows a menu of up to 6 moves with their BP cost (two columns from 4 rows up), plus
NEXT (`0xFFFD`) and QUIT (`0xFFFE`) → `tutormovegetprice(move, var)` →
`checkbattlepoints` → if 4 moves known, the summary screen to pick one
(`pokemonsummaryscreen` + `getmoveselection`) → `takebattlepoints` →
`tutormoveteachinslot(slot, moveSlot, move)`.

`tutormoveteachinslot` and `setmonmove` both call `MonSetMoveInSlot_ResetPpUp`
(`src/pokemon.c:3120`): PP Ups to 0, PP to max.

### Which moves a Pokémon is offered

`GetLearnableTutorMoves` (`src/field/scrcmd_move_tutor.c:197`) goes through
`sTutorMoves` in order. Move `j` is offered when

- bit `j` of the species' 8-byte entry in `waza_oshie.bin` is set,
- `sTutorMoves[j].tutorNpc` is the NPC asked about,
- the Pokémon doesn't know it already.

So the `TUTOR_*` constant of a move must equal its index in `sTutorMoves`.

### `waza_oshie.json`

```json
{ "mon": "SPECIES_BULBASAUR", "moves": [ "TUTOR_MUD_SLAP", "TUTOR_FURY_CUTTER", ... ] }
```

- One entry per species, **in species order, with no egg entries**: Bulbasaur is
  entry 0, Arceus 492, then the 12 alternate forms `SPECIES_DEOXYS_ATK` ...
  `SPECIES_ROTOM_MOW` (505 entries, `NUM_SPECIES - 2`). The `"mon"` key is only a
  label. The build doesn't check it; the position is what counts.
- `GetMoveTutorLearnset` asserts the file is exactly `(NUM_SPECIES - 2) * 8` bytes.
- The template turns each `TUTOR_*` into a bit; above 63 it stops with
  "Tutor move out of range".
- Forms: `GetMoveTutorLearnsetIndex` (`:150`) maps Deoxys, Wormadam, Giratina,
  Shaymin and Rotom forms to their entries. Other forms (Unown, Burmy, Castform,
  Arceus...) use the base species.

Adding a species: [adding-a-species.md](adding-a-species.md#3-base-stats-evolutions-moves).

**Retail quirk:** in `GetMoveTutorLearnsetIndex`, `index` is only set for the form
cases. For every other species it is returned uninitialized. It works because mwcc
keeps `index` in the same register as `species` (r0), so `index - 1` is
`species - 1`. A compiler that doesn't do that returns garbage. If you edit this
function, write `u16 index = species;` first.

### The menu

`ScrCmd_MoveTutorChooseMove` (`:249`) builds a `ScriptMenu` from the **calling
script's** message file: rows use entries 0/1 of it (move name + `BP`), 2 is NEXT,
3 is QUIT. That is `msg_0748` for the std script. Calling `movetutorchoosemove` from
a map script would use the map's first four messages instead.

Paging: up to 7 moves fit on one page. Above that it shows 6 per page, and the page
count is `n / 6 + 1`.

**Retail bug (read from the code, not seen in game):** with exactly 12 or 18 moves
offered, the page count is one too many. On the extra page `pageNum * 6 == n`, the
"never taken" branch at `:279` runs: it shows the first 6 moves again and
`showNextButton` is read uninitialized (a stack slot in the compiled code). The
second and third tutors have 21 and 16 moves, so 12 is reachable for a Pokémon that
learns many of them. Fix in [§6.4](#64-fix-the-frontier-tutor-page-count).

### Prices

`cost` in `sTutorMoves` is in BP, 0-255 (`u8`). `tutormovegetprice` asserts if the
move isn't in the table.

## 4. The Headbutt tutor

`IlexForest_EventScript_FatMan` uses `moncanlearnheadbuttfromtutor(slot, var)`.
That is `GetLearnableTutorMoves` with `MOVE_TUTOR_NPC_HEADBUTT`: TRUE when
`TUTOR_HEADBUTT` (bit 51) is set and the Pokémon doesn't know Headbutt. So who learns
Headbutt here is `waza_oshie.json`, not `personal.json`.

The script does the rest itself: `monhasmove`, `countmonmoves`, the summary screen
(`pokemonsummaryscreen(1, slot, 29)`; 29 is `MOVE_HEADBUTT`, which also blocks
forgetting HMs), then `setmonmove`. It's free and repeatable.

## 5. The Move Deleter

`Blackthorn_MoveTutorHouse_EventScript_PokefanM`: refuses eggs and Pokémon with one
move (`countmonmoves`), then `openlearnforgetmove(slot)` opens the summary screen on
the moves page with `moveToLearn = 0` (`LearnForgetMove_LaunchApp`,
`src/launch_application.c:382`). Because no move is being learned, **HMs can be
forgotten** here. `getlearnforgetmoveresult(var)` gives the slot, or 255 (the screen
returns 4 for cancel). `monforgetmove(slot, moveSlot)` removes it.

## 6. How-tos

### 6.1 Change the relearner's price or make it free

Script only, in `Blackthorn_MoveTutorHouse_EventScript_FatMan`:

- Another item: replace `ITEM_HEART_SCALE` in `hasitem` and `takeitem`, and the
  text.
- Free: remove the `hasitem` check and the `takeitem` + "handed over" message.
- Money: `hasenoughmoneyimmediate(VAR, amount)` and `submoneyimmediate(amount)`
  (macros in `asm/macros/script.inc`).

To let him teach from the first talk, move `setflag(FLAG_MET_MOVE_MANIAC)` to the top
and drop the `end` after the introduction.

### 6.2 Relearner: learnsets of 21 moves

In `src/move_relearner.c`, use the 22-entry size the rest of the game uses:

```c
    u16 *tableFromFile = Heap_Alloc(heapID, MAX_LEARNED_MOVES * 2);
    u16 *returnTable = Heap_Alloc(heapID, MAX_LEARNED_MOVES * 2);
    ...
    for (u8 i = 0, j, k = 0; i < MAX_LEARNED_MOVES; i++) {
```

`MAX_LEARNED_MOVES` (`include/constants/pokemon.h`) is already visible there. 21 moves + end marker = 44 bytes =
22 halfwords, so the file fits and the marker is always reached.

**Relearn moves above the current level** (Gen 9 style): in the same loop, remove

```c
        } else if (LEVEL_UP_LEARNSET_LVL(tableFromFile[i]) > level) {
            continue;
```

Egg moves aren't in the list. Adding them means loading `kowaza_list` the way
`LoadEggMoves` (`src/get_egg.c:364`, static) does, for the species' baby form, and
appending them before the end marker. The screen takes any length up to 256.

### 6.3 Keep the relearner list alive

In `src/scrcmd_move_relearner.c`, remove `Heap_Free(eligibleMoves);` from
`StartMoveRelearner`, and free it when the result is read:

```c
BOOL ScrCmd_MoveRelearnerGetResult(ScriptContext *ctx) {
    ...
    Heap_Free(moveRelearner->eligibleMoves);
    MoveRelearner_Delete(moveRelearner);
    return FALSE;
}
```

Every retail use of `moverelearnerinit`/`movetutorinit` is followed by
`moverelearnergetresult`, so nothing leaks. Any new script must do the same (it
already must, to free the args).

### 6.4 Fix the Frontier tutor page count

In `ScrCmd_GetTutorMoveListPageCount`:

```c
    } else {
        *result = (numLearnableMoves + 5) / 6;
    }
```

7 moves still make one page (the `<= 7` case above it); 12 now make 2, 13 make 3.

### 6.5 Add a move to the Frontier tutors

Example: Drain Punch for 48 BP at the first tutor.

1. `include/constants/moves.h`: `#define TUTOR_DRAIN_PUNCH 52` after
   `TUTOR_HEADBUTT`.
2. `sTutorMoves` in `src/field/scrcmd_move_tutor.c`: append at the **end**, after
   Headbutt, so its index is 52:
   ```c
       { MOVE_DRAIN_PUNCH,   48, MOVE_TUTOR_NPC_FRONTIER_TOP_LEFT     },
   ```
   The order of a tutor's menu is the order in this table.
3. `ScrCmd_MoveTutorChooseMove`: `u8 learnableMoves[52];` holds one entry per
   table row. Make it `u8 learnableMoves[NELEMS(sTutorMoves)];`, or the 53rd move
   overflows the stack.
4. `waza_oshie.json`: add `"TUTOR_DRAIN_PUNCH"` to each species that should learn
   it (`SPECIES_MACHOP`, `SPECIES_MACHOKE`, ...).

Up to 64 tutor moves (bits 0-63) fit. More needs a bigger `MoveTutorLearnset`
(`u8 moves[8]` → e.g. 16), the template's `oshie_*` macros, and the size check, and
the file grows to `(NUM_SPECIES - 2) * 16` bytes.

To **move** a move to another Frontier tutor, change its `tutorNpc`. To **remove**
one, don't delete the row (that shifts every later bit); remove it from
`waza_oshie.json` instead, or give it an unused `tutorNpc`.

### 6.6 A new one-move tutor that uses `waza_oshie.json`

The Headbutt trick works for any move: give the move its own NPC number, then
`gettutormovelistpagecount` with that number returns 0 or 1, which means "can't learn
or already knows" / "can learn".

1. `include/constants/scrcmd.h`: `#define MOVE_TUTOR_NPC_DRAIN_PUNCH 4`.
2. Add the move as in §6.5, with `MOVE_TUTOR_NPC_DRAIN_PUNCH` as its `tutorNpc` and
   cost 0. It then doesn't appear at any Frontier tutor.
3. The NPC script (this uses the relearner screen, which also handles the 4-move
   case):

```
script MyMap_EventScript_DrainPunchTutor {
    playse(SEQ_SE_DP_SELECT)
    lockall
    faceplayer
    npcmsg("I can teach Drain Punch.\n"
           "Which Pokémon should learn it?\r")
    closemessage
    fadescreen(6, 1, 0, RGB_BLACK)
    waitfade
    partyselectui
    getpartyselection(VAR_SPECIAL_x8000)
    restoreoverworld
    fadescreen(6, 1, 1, RGB_BLACK)
    waitfade
    if (var(VAR_SPECIAL_x8000) == 255) { goto(MyMap_DrainPunchTutor_End) }
    getpartymonspecies(VAR_SPECIAL_x8000, VAR_SPECIAL_RESULT)
    if (var(VAR_SPECIAL_RESULT) == 0) { goto(MyMap_DrainPunchTutor_End) }
    gettutormovelistpagecount(VAR_SPECIAL_x8000, MOVE_TUTOR_NPC_DRAIN_PUNCH, VAR_SPECIAL_RESULT)
    if (var(VAR_SPECIAL_RESULT) == 0) {
        npcmsg("That Pokémon can’t learn it,\n"
               "or it already knows it.")
        waitbuttonpress
        closemessage
        releaseall
        end
    }
    fadescreen(6, 1, 0, RGB_BLACK)
    waitfade
    movetutorinit(VAR_SPECIAL_x8000, MOVE_DRAIN_PUNCH)
    moverelearnergetresult(VAR_SPECIAL_RESULT)
    restoreoverworld
    fadescreen(6, 1, 1, RGB_BLACK)
    waitfade
MyMap_DrainPunchTutor_End:
    releaseall
    end
}
```

`moverelearnergetresult` gives 0 if it was learned. Charge for it after that, as the
relearner does. For a tutor without a species table (like Wilma), skip step 1-2 and
check types or species in the script.

### 6.7 Change who gets the ultimate moves or Draco Meteor

Edit the script checks in §2: `_05F4` (species → 1/2/3) and `_06B0` (which move) for
the old man; the `getmontypes` comparisons with 16 for Wilma (twice: the party loop
and `_042B`). The friendship requirement is the `mongetfriendship ... < 255` line in
each.

## 7. Problems in the original game

All four are in retail HeartGold and are kept as-is, so the ROM still matches. They were
found by reading the C and the compiled code; none was reproduced in game. A mod
that touches this code should apply the fixes.

| Problem | When it shows | Effect | Fix |
|---|---|---|---|
| The relearner's move list is freed right after the screen is launched, before the screen reads it (`StartMoveRelearner`, `src/scrcmd_move_relearner.c:43`) | every relearner or one-move tutor visit | none in retail, because nothing allocates from `HEAP_ID_FIELD3` in between; any new code that does can overwrite the list, and the screen shows wrong moves or teaches one | free it in `ScrCmd_MoveRelearnerGetResult` instead ([§6.3](#63-keep-the-relearner-list-alive)) |
| The relearner's buffers are 21 halfwords (`LEVEL_UP_LEARNSET_MAX`) but a learnset file can be 22 (`src/move_relearner.c:27-32`) | learnset of 20 moves (10 retail species): 2-byte overflow. 21 moves: overflow, and the list has no end marker | 20: probably harmless (heap rounding, not checked). 21: the screen counts moves past the end and lists garbage | use `MAX_LEARNED_MOVES` (22) for both buffers and the loop ([§6.2](#62-relearner-learnsets-of-21-moves)) |
| The Frontier tutor page count is `n / 6 + 1` (`ScrCmd_GetTutorMoveListPageCount`) | a Pokémon offered exactly 12 or 18 moves by one tutor | an extra page that repeats the first 6 moves; `showNextButton` is read uninitialized, so NEXT may or may not appear | `(n + 5) / 6` for more than 7 moves ([§6.4](#64-fix-the-frontier-tutor-page-count)) |
| `GetMoveTutorLearnsetIndex` leaves `index` unset for every species without a form case (`src/field/scrcmd_move_tutor.c:150`) | always, but it only breaks with another compiler or a change to the function | today mwcc keeps `index` in `species`'s register, so it's right. If that changes, every species reads a random entry of `waza_oshie.bin` | start the function with `u16 index = species;` (not built; it may change the code bytes) |

Builds that include the first three fixes are described in [Not verified](#not-verified).

## Checklist: adding a tutor move

- [ ] `TUTOR_X` = its index in `sTutorMoves`
- [ ] row appended to `sTutorMoves` (move, BP, NPC)
- [ ] `learnableMoves[]` sized from `NELEMS(sTutorMoves)`
- [ ] species in `waza_oshie.json`; 64 moves at most
- [ ] for a single-move NPC: new `MOVE_TUTOR_NPC_*`, script with
      `gettutormovelistpagecount` + `movetutorinit` + `moverelearnergetresult`
- [ ] `make release`

## Not verified

- §6.2 (both parts), §6.3, §6.4 and §6.6 were applied together and built into a
  HeartGold ROM with `make release`: Drain Punch at index 52 with its own NPC number
  and cost 0, given to the Machop line, and the §6.6 script added to the Blackthorn
  house. The built `waza_oshie.bin` was 4,040 bytes with bit 52 set for Machop,
  Machoke and Machamp only, and the script compiled. The changes were then reverted,
  and all four checksums matched. The Frontier variant of §6.5 (48 BP at the first
  tutor) differs only in the table row and wasn't built separately. Nothing was
  tried in game.
- The page-count bug (§3) and the freed relearner list (§1) are read from the C and
  the compiled code, not reproduced in game.
- The 20-move overflow being harmless in retail is assumed from the heap rounding
  allocations up; not checked.
