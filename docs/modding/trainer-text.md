<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Trainer battle text

> AI-generated; not affiliated with pret. See AI.md at the repository root.

Each trainer can have up to 19 kinds of line: what they say when they spot you, when
they lose, when you talk to them afterwards, mid-battle remarks, rematch greetings, and
so on. This page covers what each kind is for, how to change them, and how the game
finds them.

**In short:** edit `"messages"` in `files/poketool/trainer/trainers.json`, then run

```sh
python3 tools/trmsg/trmsg.py build
```

and build the ROM. The tool regenerates the three files the game actually reads. On
unmodified data it rewrites them byte for byte, so `make` still matches.

| pokeemerald | here |
|---|---|
| `TRAINER_X_INTRO`, `_DEFEAT`, `_POSTBATTLE` texts named in the map script (`trainerbattle_single TRAINER_X, Intro, Defeat`) | lines stored per trainer and found by trainer number and type; the map script only names the trainer (`std_trainer(TRAINER_X)`) |
| text in `data/maps/<Map>/scripts.inc` | `messages` in `trainers.json` → `msg_0728.json` + two binary tables |
| defeat text shown by the battle engine from the script's argument | defeat text looked up by the battle script (`TRAINER_MESSAGE_LOSE`) |
| no mid-battle lines in vanilla | types 13-16: lines when the opponent's Pokémon is low or last ([§1](#1-the-message-types)) |

## Contents

1. [The message types](#1-the-message-types)
2. [Changing text](#2-changing-text)
3. [Recipes](#3-recipes)
4. [How the game finds a line](#4-how-the-game-finds-a-line)
5. [The tool](#5-the-tool)

## 1. The message types

The types are `TRMSG_*` in `include/constants/trainers.h`. "Asked for by" says who
prints it; "needs exists-check" means the game first calls
`TrainerMessageWithIdPairExists` and skips the line if it isn't there (see
[§4](#4-how-the-game-finds-a-line) for why that matters).

| # | Constant | When it shows | Asked for by | Exists-check |
|---|---|---|---|---|
| 0 | `TRMSG_INTRO` | the trainer spots you or you talk to them before the battle | `std_trainer` (`scr_seq_0953.s`) | no |
| 1 | `TRMSG_LOSE` | in battle, after "Player defeated X!" | battle subscript `BattleWin` | no |
| 2 | `TRMSG_AFTER` | talking to them after you've won | `std_trainer` | no |
| 3 | `TRMSG_DBL_INTRO_1` | double-battle pair, first speaker's intro | `std_trainer` | no |
| 4 | `TRMSG_DBL_LOSE_1` | double battle, first speaker loses | `BattleWin` | no |
| 5 | `TRMSG_DBL_AFTER_1` | after the double battle, first speaker | `std_trainer` | no |
| 6 | `TRMSG_DBL_1POKE_1` | you have only one usable Pokémon, so they refuse to battle | `std_trainer` | no |
| 7-10 | `TRMSG_DBL_INTRO_2`, `_LOSE_2`, `_AFTER_2`, `_1POKE_2` | the same for the second speaker | as above | no |
| 11-12 | | unused | | |
| 13 | `TRMSG_HIT_POKE_FIRST_TIME` | the first time their Pokémon is hit (no retail trainer has one) | `CheckTrainerMessage` | **yes** |
| 14 | `TRMSG_CURRENT_POKE_HALF` | their Pokémon drops to half HP | `CheckTrainerMessage` | **yes** |
| 15 | `TRMSG_LAST_POKE` | they send out their last Pokémon | `CheckTrainerMessage` | **yes** |
| 16 | `TRMSG_LAST_POKE_HALF` | their last Pokémon drops to half HP | `CheckTrainerMessage` | **yes** |
| 17 | `TRMSG_PHONE_REMATCH_INTRO` | intro for a phone rematch | `std_trainer` (`GetRematchMsgParams`) | no |
| 18-19 | `TRMSG_PHONE_REMATCH_DBL_INTRO_1`, `_2` | the same for a double pair | `std_trainer` | no |
| 20 | `TRMSG_WIN` | **you** lose: the trainer slides back in and gloats before you black out | battle subscript `BattleLose` | **yes** |

Things the table above doesn't show:

- **Two speakers, one trainer.** A double-battle pair such as `TRAINER_TWINS_AMY_AND_MIMI`
  is one trainer number with lines 3-10; both NPCs on the map use that number. The
  speaker's name is part of the text ("Amy: Oh, goodness!").
- **Rematch teams only have a lose line.** For a phone rematch, `std_trainer` shows
  the *original* trainer's type 17 line, then battles the rematch team
  (`TRAINER_YOUNGSTER_JOEY_2` etc.). The battle prints the rematch team's own type 1,
  so a new rematch team needs a `TRMSG_LOSE` line and nothing else.
- **Gym leaders and story battles** use `trainerbattle(...)` from a map script, and
  their speeches before and after the battle are ordinary `npcmsg` text in that map.
  From the table, gym leaders, the Elite Four and Lance use only 1 (lose) and the
  mid-battle lines 15-16; the Rival and Red also have 20.
- **Mid-battle lines** are checked once per turn, before you choose an action
  (`BattleControllerPlayer_TrainerMessage`). They only work in single battles against
  a normal trainer: `CheckTrainerMessage` returns early for double, link and Frontier
  battles. Type 13 shows once per battle (`BATTLE_STATUS2_FIRST_DAMAGE_MESSAGE`);
  14 once per Pokémon (its `msgFlag` is cleared when it is sent out); 15 and 16 once,
  for the last Pokémon.
- **The Battle Frontier** doesn't use this table: its trainers' lines come from other
  message banks (`BattleSystem_PrintTrainerMessage`, `src/battle/battle_system.c`).

## 2. Changing text

Every trainer in `trainers.json` has a `messages` list:

```json
"messages": [
  {"type": "TRMSG_INTRO", "message": "I just lost, so I’m trying to find\\nmore Pokémon.\\rWait! You look weak! Come on,\\nlet’s battle!\\r"},
  {"type": "TRMSG_LOSE", "message": "Oh...\\nI’m out of Pokémon that can fight.\\n"},
  {"type": "TRMSG_AFTER", "message": "I knew it--if you don’t have many\\nPokémon, battles are harder!\\fI need to catch more Pokémon!\\n"},
  {"type": "TRMSG_PHONE_REMATCH_INTRO", "message": "I’ve been waiting!\\nLet’s battle now!\\r"}
]
```

The build itself doesn't read this list. In retail data it is an exact copy of the
binary tables, and `python3 tools/trmsg/trmsg.py build` turns it back into them. So:
change it, run `build`, then `make release`.

| To... | Do |
|---|---|
| change a line | edit its `message` |
| add a line | add `{"type": "TRMSG_...", "message": "..."}`; order in the list doesn't matter |
| remove a line | delete the entry. A line the game asks for without an exists-check then prints an empty box, so keep 0, 1 and 2 for any trainer the player can fight through `std_trainer` |
| see what a trainer says | `python3 tools/trmsg/trmsg.py show TRAINER_X` |
| check nothing is out of step | `python3 tools/trmsg/trmsg.py check` |

### Text format

In `trainers.json` the breaks are written `\\n`, `\\r` and `\\f` (a backslash and a
letter); `msg_0728.json` holds the real characters. A text box has two lines.

| Code | Effect (`src/render_text.c`) |
|---|---|
| `\n` | new line |
| `\r` | wait for A/B, then **clear** the box and continue at the top |
| `\f` | wait for A/B, then **scroll** up one line |

Retail lines are at most about 40 characters (most under 38). The font is
proportional, so check long lines in game.

**No placeholders.** Both the field (`ScrCmd_TrainerMessage`) and the battle
(`BattleSystem_PrintTrainerMessage`) print the line as stored, without
`StringExpandPlaceholders`, so `{STRVAR_1 ...}` (the player's name, a species) is not
replaced. To use one, print the line from a map script with `npcmsg` instead.

## 3. Recipes

### Give a route trainer a mid-battle line

```json
{"type": "TRMSG_LAST_POKE", "message": "This is my last one!\\nDon’t let me down!"}
```

Add it to the trainer's `messages`, run `build`. It shows when they send out their last
Pokémon, in a single battle.

### Make a trainer gloat when they beat you

Add a `TRMSG_WIN` line. The `BattleLose` subscript checks for it before "Player
blacked out!"; without one the trainer doesn't reappear.

### Text for a new trainer

A trainer added at the end of `trainers.json` (see
[trainers.md](trainers.md#adding-a-trainer)) needs `TRMSG_INTRO`, `TRMSG_LOSE` and
`TRMSG_AFTER` (or 3-10 for a double pair). `build` gives every trainer past the retail
738 its own offset entry; without one the game would read past the end of
`trtblofs.narc` and start its search at a garbage offset.

### A phone rematch

The rematch greeting is type 17 on the original trainer; each rematch team needs a type
1. The rest of the setup is in [phone.md](phone.md#7-example-give-a-route-trainer-a-phone-number).

### Print a trainer's line from a script

```
trainermessage(TRAINER_YOUNGSTER_JOEY, 2)    // type 2, TRMSG_AFTER
```

`TrainerMessage` (script command 214) takes a trainer and a type, both numbers or vars,
and prints into the open message box. `std_trainer` uses it with
`GetTrainerMsgParams`, which picks 0/2/0 for a single trainer and 3/5/6 or 7/9/10 for
each half of a double pair.

## 4. How the game finds a line

You don't need this to edit text with the tool. It explains why hand-editing the
tables (or appending to them, as older notes in this repo did) breaks things.

| File | Contents |
|---|---|
| `files/poketool/trmsg/trtbl.narc` | one member: pairs of `u16 trainer, u16 type`, 4 bytes each |
| `files/poketool/trmsg/trtblofs.narc` | one member: a `u16` per trainer, the byte offset of its first pair in `trtbl` |
| `files/msgdata/msg/msg_0728.json` | message N is the text of pair N (`offset / 4`) |

Both NARCs are copied into the ROM as they are (`files/poketool/trmsg/meson.build`).
In retail, `trtbl` has 1,717 pairs for 636 trainers; each trainer's pairs are
together, but the trainers are not in number order. `trtblofs` has 735 entries
(trainers 0-734). The three partner trainers 735-737 have none, and nothing asks for
their lines. A trainer with no lines has offset 0.

There are two lookups (`src/trainer_data.c`):

- `GetTrainerMessageByIdPair` starts at the trainer's offset and scans **to the end
  of the table** for a matching pair. If it finds none, the box is empty.
- `TrainerMessageWithIdPairExists` starts at the same place but **stops at the first
  pair that belongs to another trainer.**

So a trainer's pairs must sit together, starting at its offset. A pair appended to the
end of the table, away from the trainer's others, is still found by the first lookup
(intro, lose, after, rematch intro) but never by the second. Mid-battle lines (13-16)
and the gloat (20) would silently never show. Inserting a pair in the middle shifts
every later pair, so every later offset and every later `msg_0728` message has to move
with it. `trmsg.py build` does all of this.

## 5. The tool

`tools/trmsg/trmsg.py` (no build needed, standard Python 3):

| Command | Does |
|---|---|
| `show TRAINER_X [...]` | prints each line with its type and `msg_0728` id; numbers work too |
| `check` | `trtbl`, `trtblofs` and `msg_0728.json` agree with each other and with `trainers.json`, each trainer's pairs are together, every trainer has an offset entry |
| `build` | rewrites the three files from `trainers.json` |

`build` keeps each trainer's place in the table (read from the current
`trtbl.narc`) and puts trainers that are new to the table at the end, so a small edit
makes a small diff. It refuses two lines of the same type for one trainer (the game
would only find the first) and a table over 64 KB (offsets are 16-bit; retail is
about 7 KB).

The build doesn't run it. If you edit `trainers.json` and forget, `check` reports
which trainers differ.
