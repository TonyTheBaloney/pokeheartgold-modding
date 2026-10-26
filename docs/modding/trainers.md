<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-23 -->

# Trainers: parties, levels, battles and AI

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This page covers individual trainers: their Pokémon and levels, how a script starts
a battle against them, rematches, and the AI that picks their moves, switches and
items. Trainer classes (title, sprite, prize money, music) are in
[trainer-classes.md](trainer-classes.md); placing a trainer NPC on a map is in
[npcs-and-scripts.md](npcs-and-scripts.md#trainers).

| pokeemerald | here |
|---|---|
| `src/data/trainers.h` + `trainer_parties.h` | `files/poketool/trainer/trainers.json` (one file for both) |
| `TRAINER_*` in `include/constants/opponents.h` | `TRAINER_*` in `include/constants/trainers.h` |
| `.iv = 0..255` | `"difficulty": 0..255`, the same scale |
| `.aiFlags = AI_SCRIPT_CHECK_BAD_MOVE \| ...` | `"ai_flags": 7` (a number; bits below) |
| `.doubleBattle = TRUE` | `"double": 2` |
| `trainerbattle_single` / `_double` | `trainerbattle(...)` in `scripts.pory`, or `std_trainer(...)` on the NPC |
| `data/battle_ai_scripts.s` (macros) | `gTrainerAITable` in `asm/trainer_ai_data.s`: **raw bytes**, no macros yet |
| `gRematchTable` | `sTrainerRematchSets` (`src/trainer_rematch.c`) |

## Where things are

| What | Where |
|---|---|
| parties, class, name, items, AI flags, singles/doubles | `files/poketool/trainer/trainers.json` |
| trainer ids | `include/constants/trainers.h` (id = position in `trainers.json`) |
| how a party is built (levels, IVs, nature, moves) | `CreateNPCTrainerParty` (`src/trainer_data.c:274`) |
| battle start from a script | `ScrCmd_TrainerBattle` (`src/scrcmd_battle.c:99`) → `SetupAndStartTrainerBattle` (`src/encounter.c:696`) |
| "defeated" flags | `TRAINER_FLAG_BASE` + id (`include/constants/flags.h:1394`) |
| rematch teams | `sTrainerRematchSets` (`src/trainer_rematch.c:12`) |
| AI: move choice | `TrainerAI_SelectMove` (`src/battle/trainer_ai.c:230`) running the scripts in `asm/trainer_ai_data.s` |
| AI: switching, items | `TrainerAI_ShouldSwitch` (`trainer_ai.c:3729`), `TrainerAI_ShouldUseItem` (`trainer_ai.c:3888`) |
| AI: which Pokémon comes in next | `TrainerAI_PostKOSwitchIn` (`src/battle/battle_controller_opponent.c:1059`) |

The build turns `trainers.json` into `trdata.narc` (per trainer) and `trpoke.narc`
(per party) through the templates `trdata.json.txt` and `trpoke.json.txt` next to it,
and the names into `msg_0729`. See `files/poketool/trainer/meson.build`.

## A trainer in trainers.json

```json
{
  "type": "TRTYPE_MON_ITEM_MOVES",
  "class": "TRAINERCLASS_LEADER_FALKNER",
  "name": "{TRNAME}Falkner",
  "items": [],
  "ai_flags": 3,
  "double": 0,
  "party": [
    {
      "difficulty": 50,
      "genderOverride": "TRPOKE_GENDER_OVERRIDE_OFF",
      "abilityOverride": "TRPOKE_ABILITY_OVERRIDE_OFF",
      "level": 9,
      "species": "SPECIES_PIDGEY",
      "item": "ITEM_NONE",
      "moves": ["MOVE_TACKLE", "MOVE_SAND_ATTACK"],
      "capsule": 0
    }
  ],
  "messages": [ ... ]
}
```

| Field | Meaning |
|---|---|
| `type` | which per-Pokémon fields exist: `TRTYPE_MON`, `TRTYPE_MON_MOVES`, `TRTYPE_MON_ITEM`, `TRTYPE_MON_ITEM_MOVES`. **Every party member must match it**: the binary is a flat array whose entry size comes from the type. |
| `class` | `TRAINERCLASS_*` ([trainer-classes.md](trainer-classes.md)) |
| `name` | `{TRNAME}` + the name. The Rival's name is replaced by the player's chosen rival name (`src/trainer_data.c:33`). |
| `items` | up to 4 items the trainer uses from the bag in battle ([below](#items-in-battle)) |
| `ai_flags` | which AI scripts run ([below](#ai-flags)) |
| `double` | `0` single, `2` double battle (`BATTLE_TYPE_DOUBLES`, OR'd into the battle type at `src/trainer_data.c:45`) |
| `party` | 1 to 6 Pokémon |
| `messages` | battle text by type (`TRMSG_*`). The build reads the tables made from it, so run `python3 tools/trmsg/trmsg.py build` after editing ([trainer-text.md](trainer-text.md)) |

Per Pokémon:

| Field | Meaning |
|---|---|
| `level` | 1-100 |
| `species` | `SPECIES_*` |
| `form` | optional; form number (packed into the top 6 bits of the species, `trpoke.json.txt`). No retail trainer uses it. |
| `difficulty` | 0-255. Every IV is `difficulty × 31 / 255` (`src/trainer_data.c:336`): 0 → 0, 50 → 6, 100 → 12, 150 → 18, 200 → 24, 250 → 30, 255 → 31. EVs are always 0. |
| `moves` | only with a `*_MOVES` type; up to 4, the rest padded with `MOVE_NONE`. Without it the Pokémon gets the last four moves it learns by level. |
| `item` | only with a `*_ITEM` type; held item |
| `genderOverride` | `TRPOKE_GENDER_OVERRIDE_OFF` / `_MALE` / `_FEMALE` |
| `abilityOverride` | `TRPOKE_ABILITY_OVERRIDE_OFF` / `_FIRST` / `_SECOND`: forces ability slot 1 or 2 |
| `capsule` | Ball Capsule seal id, 0 for none |

**Nature, gender and ability are fixed per trainer, not random.** The personality
value is seeded from `difficulty + level + species + trainer id`, then the RNG is
rolled once per trainer class number (`src/trainer_data.c:327`). Changing a
Pokémon's level or difficulty therefore also changes its nature (and, without an
override, its ability). Use the overrides when the ability matters.

A Pokémon that knows Frustration gets friendship 0, every other one 255
(`TrMon_FrustrationCheckAndSetFriendship`).

## Changing a party

Edit the trainer's entry and build with `make release` (plain `make` also runs the
checksum tests, which fail on any data change: see [README.md](README.md#building-a-modified-rom)).

- **Raise levels**: change `level`. Expect the nature to change too (above).
- **Give custom moves to a trainer that has none**: change `type` to
  `TRTYPE_MON_MOVES` and add `moves` to **every** Pokémon in the party.
- **Give held items**: `TRTYPE_MON_ITEM` (or `_ITEM_MOVES`) and an `item` on every
  Pokémon; use `ITEM_NONE` for the ones without.
- **Stronger IVs**: raise `difficulty`. Retail uses 0 for early trainers, 50-100 for
  gym leaders, up to 250 for late and post-game teams.

Finding a trainer: the id is the `TRAINER_*` constant (e.g.
`TRAINER_LEADER_FALKNER_FALKNER` = 20 is the 21st entry, counting the empty entry 0).
`python3 -c "import json; t=json.load(open('files/poketool/trainer/trainers.json'))['trainers']; print(t[20]['name'])"`
checks you have the right one.

### Adding a trainer

1. Append an entry at the **end** of `trainers` in `trainers.json`. Its id is its
   position (738 for the first new one).
2. Add the constant after `TRAINER_PARTNER_RIVAL_3` in `include/constants/trainers.h`:

   ```c
   #define TRAINER_PARTNER_RIVAL_3             737
   #define TRAINER_HIKER_BOB                   738
   ```

3. Use it from a script or an NPC ([below](#starting-a-battle)).

**Ids 740 and up need one more step for `std_trainer`.** `std_trainer(T)` is script
number `3000 + T - 1` (`include/constants/std_script.h:82`), which runs entry `T - 1`
of `files/fielddata/script/scr_seq/scr_seq_0953.s`. That file has 740 entries: 0-738
are labels on the same trainer script, and entry 739 is the "trainer spotted you"
script, `std_trainer_approach = std_trainer(LAST_TRAINER_INDEX)` with
`LAST_TRAINER_INDEX 740` (`include/constants/trainers.h:744`). So trainers 738 and
739 work as they are. For more, raise `LAST_TRAINER_INDEX` to one past your last
trainer and, in `scr_seq_0953.s`, add `ScrDef scr_seq_0953_000` lines before
`ScrDef scr_seq_0953_739`, one per extra id, so that the approach script is at
entry `LAST_TRAINER_INDEX - 1` again. `trainerbattle(...)` from a script doesn't go
through this table and works for any id.

The defeated flag of trainer `N` is flag `0x550 + N`. Retail ends at `0x821`;
`0x822`-`0x82D` are unused, and from `0x82E` on the range overlaps `FLAG_UNK_*` flags
([unknown-flags-vars.md](unknown-flags-vars.md)), so check those before adding more
than 12 trainers. Give the new trainer intro, defeat and after-battle lines in its
`messages` and run `python3 tools/trmsg/trmsg.py build`, which also gives it the
offset entry the text lookup needs ([trainer-text.md](trainer-text.md#text-for-a-new-trainer)).

## Starting a battle

**An NPC that spots you.** Set the object's `trainer_type` and sight range and use
`std_trainer(TRAINER_X)` as its script (`std_trainer_2` for the second trainer of a
pair); details in [npcs-and-scripts.md](npcs-and-scripts.md#trainers). The standard
script plays the encounter music, the battle and the trainer's text, and sets the
defeated flag.

**From a script**, as gyms do (`data/maps/Violet_Gym/scripts.pory:77`):

```
trainerbattle(TRAINER_LEADER_FALKNER_FALKNER, 0, 0, 0)
checkbattlewon(VAR_SPECIAL_RESULT)
if (var(VAR_SPECIAL_RESULT) == 0) {
    whiteout
    releaseall
    end
}
settrainerflag(TRAINER_LEADER_FALKNER_FALKNER)   // only if you want defeated() to see it
```

`trainerbattle(first, second, a, b)` (`ScrCmd_TrainerBattle`, `src/scrcmd_battle.c:99`):

| Call | Battle (`SetupAndStartTrainerBattle`, `src/encounter.c:701`) |
|---|---|
| `trainerbattle(T, 0, 0, 0)` | single, or double if `T` has `"double": 2` (one trainer, two Pokémon out: Twins, Double Team) |
| `trainerbattle(T1, T2, 0, 0)` | two different trainers together, a tag double battle (`Route34/scripts.pory:571`) |
| with a follower set (e.g. the Rival as partner) | multi battle: you and the follower against `T1` and `T2`; the partner's party is built like any trainer's |
| third argument `1` | adds `BATTLE_TYPE_11`; retail uses it only for the Cherrygrove passerby and Giovanni. Effect not traced. |
| fourth argument | if non-zero, sets an entry of `setup->followMonSlot` to 0 (`encounter.c:727`); retail always passes 0. Effect not traced. |

The script writes nothing for you: after a script battle, set the defeated flag
yourself if other scripts check `defeated(TRAINER_X)`.

Prize money is the class's rate × 4 × the level of the trainer's last Pokémon
([trainer-classes.md](trainer-classes.md#what-a-class-is-made-of)), so raising the
last Pokémon's level also raises the payout.

## Rematches

Phone rematches pick a different trainer id, one per stage, from
`sTrainerRematchSets` (`src/trainer_rematch.c:12`):

```c
{ TRAINER_YOUNGSTER_JOEY, TRAINER_YOUNGSTER_JOEY, TRAINER_YOUNGSTER_JOEY_2, TRAINER_YOUNGSTER_JOEY_3, TRAINER_YOUNGSTER_JOEY_4, TRAINER_NONE },
```

Column 0 is the trainer as placed on the map; columns 1-5 are the stages. The game
uses the first stage whose defeated flag isn't set (`GetIndexOfFirstUnbeatenRematch`),
stepping back to an earlier stage if that stage's story flag
(`FLAG_UNK_97B + stage`, `src/sys_flags.c:116`) isn't set yet. So to make a rematch
harder, edit the party of `TRAINER_YOUNGSTER_JOEY_2` etc. in `trainers.json`; to add
a stage, add a trainer and put its id in the row. Gym leader rematches are separate
battles in scripts ([gyms.md](gyms.md)). When a trainer asks for a rematch (phone
calls, days and times) and how to give a trainer a phone number is in
[phone.md](phone.md#6-rematches).

## Level scaling

Levels are fixed in the data. [level-scaling.md](level-scaling.md) shows how to
raise them with the player in `CreateNPCTrainerParty` (by party level, badge count
or both), what else depends on the level (natures, prize money, moves), and how to
evolve scaled Pokémon.

## The AI

Three separate parts decide what an AI trainer does each turn
(`TrainerAI_SelectCommand`, `src/battle/trainer_ai.c:3823`):

1. **Switch?** `TrainerAI_ShouldSwitch`. C code, same for every trainer.
2. **Use an item?** `TrainerAI_ShouldUseItem`. C code, uses the trainer's `items`.
3. **Which move?** `TrainerAI_SelectMove`. Runs the AI scripts chosen by `ai_flags`.

### AI flags

`ai_flags` is a bit mask; each set bit runs one script that adds to or subtracts
from every move's score. Each move starts at 100; the highest total wins, ties are
random (`TrainerAI_MainSingles`, `trainer_ai.c:250`). The scripts run from bit 0
upward (`trainer_ai.c:259`).

Only bit 0 (`AI_FLAG_BASIC`), bit 7 (`AI_DOUBLES`) and bit 29 (`AI_ROAMING_POKEMON`)
have names in this repository (`include/constants/battle/trainer_ai.h:72`,
`include/constants/battle.h:560`). The other names below are the ones pret uses for
the same engine in Diamond/Pearl/Platinum; the "used by" column is from the retail data.

| Bit | Value | Name (pokeplatinum) | What it does | Used by |
|---|---|---|---|---|
| 0 | 1 | Basic | avoid useless moves: no effect, immune target, status on a statused target, ... | almost everyone |
| 1 | 2 | Evaluate attacks | prefer the move that does the most damage, KO moves | gym leaders, E4 |
| 2 | 4 | Expert | the big one: situational scoring for most move effects | gym leaders, E4, Red, later rivals |
| 3 | 8 | Setup first turn | stat-up and status moves on the first turn | Chad (13), Whitney/Sabrina rematch (15) |
| 4 | 16 | Risky | high-risk moves (OHKO, Explosion, ...) | no retail trainer |
| 5 | 32 | Prioritize damage | damaging moves over status moves | Hikers, Black Belts, Poké Maniacs, early Rival (33, 35) |
| 6 | 64 | Baton Pass | Baton Pass after setting up | Nate (69), Sherman (71) |
| 7 | 128 | Tag strategy | doubles: target choice and helping the partner. **Added automatically in every double battle** (`trainer_ai.c:226`) | |
| 8 | 256 | Check HP | prefer moves suited to its own HP | no retail trainer |
| 9 | 512 | Weather | weather moves and abilities | Pryce, Erika, Blaine, Quinn (519), Vic & Tara (513) |
| 10 | 1024 | Harassment | annoying status moves | no retail trainer |
| 11-28 | | | empty: each jumps straight to the end | |
| 29 | | Roaming Pokémon | flee; forced for roamers (`trainer_ai.c:219`) | not for trainers |
| 30, 31 | | Safari, catching tutorial | | not for trainers |

Retail combinations: `1` (382 trainers), `7` = basic + evaluate + expert (186: gym
leaders, Elite Four, Red), `5` (90), `33` (57), `519` = `7` + weather.

**Making a trainer smarter** is the cheapest AI change there is: set `"ai_flags": 7`
(or `519` for a weather team, `15` to also set up on turn one, `71` for a Baton Pass
team). Flags 16, 256 and 1024 are coded but unused in retail, so test them.

### Items in battle

`items` is the trainer's bag (up to 4). `TrainerAI_ShouldUseItem`
(`trainer_ai.c:3888`), each turn before choosing a move:

- Full Restore: when the active Pokémon is under 1/4 HP.
- Potions (any item with an HP restore value): under 1/4 HP, or when it is missing
  more HP than the item heals.
- Status heals (Awakening, Antidote, Burn Heal, Ice Heal, Parlyz Heal, and items that
  cure confusion): when the active Pokémon has that status.
- X items and Guard Spec.: only just after the Pokémon comes in. The check is
  `fakeOutCount - totalTurns >= 0`, and `fakeOutCount` is set to the switch-in turn
  + 1 (`src/battle/battle_util.c:1834`).
- Item 1 can be used any time; item `i` (0-based) only once the trainer has no more
  than `count - i` Pokémon left. With 4 Full Restores and 6 Pokémon, the 2nd needs
  ≤ 3 left, the 3rd ≤ 2, the 4th ≤ 1.
- Never under Embargo, and never by the player's AI partner.

### Switching

`TrainerAI_ShouldSwitch` (`trainer_ai.c:3729`) runs for every trainer, whatever the
flags. It does nothing if trapped, and otherwise switches when: Perish Song is about
to KO it; it can't hurt a Wonder Guard target; all its moves are ineffective; a party
member absorbs the type of the damaging move that last hit it (Volt Absorb, Water
Absorb, Flash Fire; half the time); it's asleep and has Natural Cure. It stays in if it has a super-effective
move or has +4 or more total stat stages, and otherwise switches with some chance to
a party member that resists the last move and hits back super-effectively.

Who comes in after a faint: `TrainerAI_PostKOSwitchIn`
(`battle_controller_opponent.c:1059`) first looks for the party member whose types
match up best against the player's Pokémon and that has a super-effective move
against it; failing that, the one whose best move does the most damage. Its score is
a `u8` and can overflow (noted in the code).

These are plain C and safe to edit: remove a check, change a chance, add a rule.
Changes apply to every trainer, since there is no flag check; wrap a new rule in
`if (battleSystem->trainers[battler].data.aiFlags & (1 << N))` to make it opt-in.

### The AI scripts

The move-scoring scripts are bytecode in `gTrainerAITable` (`asm/trainer_ai_data.s:122`),
loaded at `src/battle/battle_controller_player.c:3964`. They are **not
disassembled**: the file is 10,607 32-bit little-endian words written as `.byte`
lines.

- Words 0-31 are the entry point of each flag bit, as word indices into the table
  (bit 0 at word `0x20`, bit 2 at `0x9F2`, bits 11-28 all at `0x296E`, a lone
  "end").
- After that, each instruction is one word with the command number, then its
  operands, one word each. The command numbers are the positions in `sAICommandTable`
  (`asm/trainer_ai_data.s:2795`); the matching C functions are the `AICmd_*` in
  `trainer_ai.c` and show how many operands each reads. For example `4`
  (`AICmd_AddToMoveScore`) takes one operand, the amount to add; `77`
  (`AICmd_PopOrEnd`) ends the script for this move.
- Jumps are **relative**: the operand is added to the cursor after the operands
  were read (`AICmd_GoTo`, `trainer_ai.c:2411`).

What you can safely do now: **change an operand in place**, such as a score added
or a random threshold, by editing its bytes. Don't insert or remove words: every
jump across that point and every entry offset after it would need fixing by hand.
Real script editing needs a disassembler to macros (like pokeemerald's
`battle_ai_scripts.s`), which this repository doesn't have yet.

To find something, decode the table with a few lines of Python:

```python
import re
lines = open("asm/trainer_ai_data.s").read().split("\n")
start = lines.index("gTrainerAITable:") + 1
end = next(i for i, l in enumerate(lines) if l.startswith("\t.public sWeightToPower"))
data = bytes(int(h, 16) for l in lines[start:end] for h in re.findall(r"0x([0-9A-F]{2})", l))
words = [int.from_bytes(data[i:i + 4], "little", signed=True) for i in range(0, len(data), 4)]
cmds = [l.split()[-1] for l in lines[end:] if l.strip().startswith(".word AICmd_")]
print(cmds[words[0x20]], words[0x20:0x20 + 4])   # first instruction of the basic script
```

The byte for word `n` is at `.byte` index `4n` counted from the line after
`gTrainerAITable:`.

## Checklist

- [ ] party members all match the trainer's `type`
- [ ] new trainer: entry at the end of `trainers.json`, `TRAINER_*` constant, flag
      range checked, text in the script; from id 740, `LAST_TRAINER_INDEX` and
      `scr_seq_0953.s`
- [ ] script battles: `checkbattlewon` + `whiteout`, `settrainerflag` if needed
- [ ] rematch stages: the trainer ids in `sTrainerRematchSets`
- [ ] AI: `ai_flags`, and `items` for in-battle healing
- [ ] `make release`

## Not verified

- None of these changes were tried in game, only read in the code. An `ai_flags`
  change was built with `make release`.
- The flag names other than bits 0, 7 and 29, and what each script does, come from
  pret's Diamond/Pearl/Platinum work, not from tracing these scripts.
- What `BATTLE_TYPE_11` (the third `trainerbattle` argument) changes.
- Whether the AI handles `form` correctly for alternate-form species.
- The `scr_seq_0953.s` steps for trainer ids 740 and up; and whether anything else
  assumes 738 trainers (the phone code compares against `LAST_TRAINER_INDEX`,
  `src/scrcmd_c.c:4701`).
