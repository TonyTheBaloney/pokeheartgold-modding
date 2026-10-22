<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Map scripts in `scripts.pory`

> AI-generated, local to this fork. Do not upstream.

Every map keeps its scripts in `data/maps/<MapName>/scripts.pory`, written in a
language modeled on [poryscript](https://github.com/huderlem/poryscript): structured
`if`/`while`/`switch` instead of `GoTo` labels, inline text and movement, a
`mapscripts` block, and `raw` for anything else. The compiler lives in
`tools/mapkit/mapkit/pory/`; the build runs it for every map. (A map folder with
`scripts.inc` / `map_scripts.inc` and no `scripts.pory` still builds from those.)

All 452 maps with their own scripts were converted by `mapkit pory init`, which
decompiles the original assembly into `if`/`elif`/`else` blocks and `movement`
blocks. HG and SS still match.

## Quick start

```sh
M=tools/mapkit/mapkit.sh
$M pory show Route30        # what scripts.pory compiles to
$M validate Route30         # checks the compiled output
make                        # still matching until you change behavior
```

## Example

```
script Cherrygrove_EventScript_MysticWaterMan {
    playse(SEQ_SE_DP_SELECT)
    lockall
    faceplayer
    if (!flag(FLAG_GOT_MYSTIC_WATER_FROM_CHERRYGROVE_CITY_MAN)) {
        npcmsg("A Pokémon I caught had an item.\n"
               "I think it’s Mystic Water.\r"
               "I don’t need it, so do you want it?\r")
        if (!itemspace(ITEM_MYSTIC_WATER, 1)) {
            npcmsg("You don’t have room for this.")
            waitbuttonpress
            closemessage
            releaseall
            end
        }
        callstd(std_give_item_verbose)
        setflag(FLAG_GOT_MYSTIC_WATER_FROM_CHERRYGROVE_CITY_MAN)
    }
    npcmsg("Back to fishing for me, then.")
    waitbuttonpress
    closemessage
    releaseall
    end
}
```

compiles to exactly the original commands (the three strings fill messages
`msg_0550_T21_00020`-`00022`, as `text.json` records):

```asm
Cherrygrove_EventScript_MysticWaterMan:
	PlaySE SEQ_SE_DP_SELECT
	LockAll
	FacePlayer
	GoToIfSet FLAG_GOT_MYSTIC_WATER_FROM_CHERRYGROVE_CITY_MAN, Cherrygrove_EventScript_MysticWaterMan_EndIf_1
	NPCMsg msg_0550_T21_00020
	GoToIfNoItemSpace ITEM_MYSTIC_WATER, 1, Cherrygrove_EventScript_MysticWaterMan_If_2
	CallStd std_give_item_verbose
	SetFlag FLAG_GOT_MYSTIC_WATER_FROM_CHERRYGROVE_CITY_MAN
Cherrygrove_EventScript_MysticWaterMan_EndIf_1:
	NPCMsg msg_0550_T21_00021
	WaitButton
	CloseMsg
	ReleaseAll
	End

Cherrygrove_EventScript_MysticWaterMan_If_2:
	NPCMsg msg_0550_T21_00022
	...
	End
```

## Language

### Top-level blocks

| Block | Meaning |
|---|---|
| `script Name { ... }` | a script with a number (`ScrDef` entry), usable from `map.json` and map scripts |
| `script(local) Name { ... }` | a label only, for `call`/`goto` from other scripts |
| `text Name { "..." "..." }` | a named message; adjacent strings join |
| `movement Name { walk_up * 2  face_left }` | movement data, placed where it is written (`EndMovement` added) |
| `mapscripts Name { ... }` | the map's init scripts (compiles to `map_scripts.inc`) |
| `scrdefs { A B C }` | script numbers: the listed scripts get 1, 2, 3, ... (optional) |
| ``raw `...` `` | copied as-is into `scripts.inc` |
| `const NAME = value` | replaced in arguments and conditions |

Comments: `//`, `#`, `/* */`. Semicolons are optional.

### Commands

Any script command, by its macro name (`LockAll`) or **lowercased** (`lockall`), as
in pokeemerald. A few pokeemerald names map to the HGSS command:

| pokeemerald name | HGSS command |
|---|---|
| `waitbuttonpress` | `WaitButton` |
| `closemessage` | `CloseMsg` |
| `message` | `NPCMsg` |
| `applymovement`, `waitmovement` | `ApplyMovement`, `WaitMovement` |
| `removeobject`, `addobject` | `HidePerson`, `ShowPerson` |

Arguments are any expression the assembler accepts. A string argument becomes a
new message (below); `moves(walk_up * 2, face_left)` becomes an inline movement.
The table lives in `tools/mapkit/script_config.json` (`command_aliases`).

### Control flow

`if (...) { } elif (...) { } else { }`, `while (...) { }`, `while { }` (forever),
`do { } while (...)`, `switch (var(V)) { case 1: case 2: ... default: ... }` (cases
don't fall through; stacked cases share a body), `break`, `continue`,
`goto(Label)`, `call(Label)`, `return`, `end`, and labels (`Name:`). A script that
doesn't end in `end`/`return`/`goto` gets `End`.

### Conditions

Combine with `!`, `&&`, `||` and parentheses.

| Condition | Compiles to |
|---|---|
| `flag(F)` (or `flag(F) == FALSE`) | `GoToIfSet` / `GoToIfUnset` |
| `var(V) == n` (`!=`, `<`, `<=`, `>`, `>=`; bare `var(V)` means `!= 0`) | `Compare V, n` + `GoToIfEq`/`Ne`/`Lt`/`Le`/`Gt`/`Ge` (`Compare` picks var-vs-var itself) |
| `defeated(TRAINER_X)` | `GoToIfDefeated` / `GoToIfNotDefeated` |
| `itemspace(ITEM, count)` | `GoToIfNoItemSpace` (the other polarity jumps around a `GoTo`) |
| `getmenuchoice(VAR) == n`, `checkbadge(B, VAR) == n`, `yesno(VAR) == n` | the command, then `Compare` on the result var |

New conditions and result-writing commands go in `script_config.json`
(`conditions`, `autovar`); the compiler has no Gen 3 or HGSS mnemonics built in.

`if (c) { goto(L) }` / `{ break }` / `{ continue }` compile to one conditional
jump. An `if` with no `else` whose body ends in `end`/`return`/`goto` is placed
after the script's end, the way the original scripts are laid out.

Generated labels are readable: `<Script>_If_1`, `_EndIf_`, `_Else_`, `_While_`,
`_Do_`, `_Case_`, `_Default_`, `_EndSwitch_`, `_Skip_`, `_Text_0`, `_Movement_0`.

### Text

Dialog lives in the scripts. A message used by one command is an inline string;
adjacent strings join, one per line of dialog:

```
npcmsg("What? This is a big battle!\f"
       "Leave me alone!\r")
```

A message used by several commands is a `text` block, named by its id, after the
first script that uses it; commands use the name:

```
text msg_0375_R30_00002 {
    "A Pokémon can use its moves as long\n"
    "as the moves still have PP.\r"
}
```

Message numbers are positions in the bank, so `text.json` still lists every
message in order. For dialog that lives in `scripts.pory` it holds only the slot:

```json
{ "id": "msg_0375_R30_00001", "from": "scr_seq_R30_000#1" }
{ "id": "msg_0375_R30_00002", "from": "text" }
```

`"<Script>#<n>"` is that script's `n`-th string (from 0, in source order);
`"text"` is the `text` block with that id. The build fills each slot and keeps the
`id`, so `msg_0375_R30.h` and every number stay the same.

- **Editing a string** changes the message in place.
- **New strings** (no slot) are added after the bank's last message as
  `<Script>_Text_<n>`; `text Name { ... }` blocks become `Name`. msgenc accepts any id.
- **Inserting a string** before others in a script shifts which slot each string
  fills. Every command still shows its own string; only message numbers move, and
  nothing else uses these numbers.
- **Renaming a script by hand** unlinks its slots: they build as empty messages and
  the strings are added as new ones. `mapkit validate -w` warns (`empty-text`);
  `mapkit script rename` updates the slots for you.
- Messages used from C/asm, by number, or by nothing stay in `text.json` with
  their text (about 2600 of 6722).
- `\n`, `\r`, `\f`, `\"`, `\\` and codes like `{STRVAR_1 3, 0, 0}` work as in `text.json`.
- Maps that share another map's text bank (`@Everywhere` in `maps.txt`) can't add text.
- Strings inside a `poryswitch` count only in the version that keeps them, so a
  slot can't point at one; use a `text` block there.

`mapkit pory inline-text <map>|--all` moved the dialog (3907 inline strings, 217
`text` blocks); each map was compiled before and after and had to give the same
commands and the same bank. `pory init` does this step too.

### Movement

Macro names (`WalkNormalNorth`), lowercase, or pokeemerald-style names derived from
them: `walk_up`, `walk_slow_left`, `walk_fast_down`, `walk_in_place_right`,
`walk_in_place_fast_up`, `jump_far_left`, `jump_in_place_slow_down`, `face_right`,
`delay_8`, `warp_out`, `set_invisible`, ... (`North/South/West/East` become
`up/down/left/right`, `Normal` is dropped, `OnSpot` becomes `in_place`).
`walk_up * 3` becomes `WalkNormalNorth 3` when the macro takes a count.

### mapscripts

```
mapscripts Route30_MapScripts {
    INIT_SCRIPT_ON_TRANSITION: Route30_OnTransition
    INIT_SCRIPT_ON_RESUME { setflag(FLAG_X) }          // inline: becomes Route30_MapScripts_Resume
    INIT_SCRIPT_ON_FRAME_TABLE [
        VAR_SCENE_X, 0: Route30_EventScript_Scene
        VAR_SCENE_X, 1 { setvar(VAR_SCENE_X, 2) }
    ]
}
```

Keys: `INIT_SCRIPT_ON_LOAD`, `_ON_TRANSITION`, `_ON_RESUME`, `_ON_FRAME_TABLE`
(pokeemerald's `MAP_SCRIPT_ON_*` also work). Entries keep their order. Targets are
script labels (compiled to their number) or any expression.

### Script numbers (`ScrDef`)

Events and map scripts refer to scripts by number, so order matters:

- Without a `scrdefs` block, numbers follow file order: top-level `script` blocks
  (and inline map scripts) get 1, 2, 3, ...
- A `scrdefs` block fixes the order, where the original game didn't number
  scripts in file order (209 maps):

  ```
  scrdefs {
      scr_seq_R30_000
      scr_seq_R30_001
  }
  ```

  Listed scripts take those numbers wherever their blocks are; scripts not in the
  list are numbered after it, in file order, so `mapkit script add` never
  renumbers anything. A name can also be a label inside a script (two numbers for
  one script). One block per map; each name once; every name must exist.
- Never reorder or insert into the list: it renumbers every later script.
- `ScrDef` lines in a `raw` block still count, as they did before `scrdefs`.
- `map.json` refers to scripts by label; the build turns labels into numbers.
- `mapkit pory sync <map>` rewrites the `_EV_` defines in `ids.h` to match (only
  needed for code that still uses `_EV_<label> + 1`); `mapkit script add` does it for you.

### Compile-time switch

```
poryswitch(GAME) {
    HEARTGOLD: setflag(FLAG_HG_ONLY)
    SOULSILVER { setflag(FLAG_SS_ONLY) }
    _: setflag(FLAG_OTHER)
}
```

`GAME` is the version being built.

## How the maps were converted

`mapkit pory init <map>` (or `--all`) turns `scripts.inc` + `map_scripts.inc` into
`scripts.pory` and deletes them. It is a decompiler for the patterns the original
script compiler wrote (`tools/mapkit/mapkit/pory/decompile.py`):

- `Compare` + `GoToIf*` / `GoToIfSet` / `GoToIfNoItemSpace` jumps around a block
  become `if`; a `GoTo` past the other branch becomes `else`, and chains become `elif`.
- A jump to a block that ends the script and sits after the script's `End`
  becomes an `if` with that block inside (the compiler places it back there).
- Movement data becomes `movement` blocks, renamed `<Map>_Movement_<offset>`.
- Commands are lowercased; `WaitButton`, `CloseMsg`, `ApplyMovement`,
  `WaitMovement`, `HidePerson` and `ShowPerson` use their pokeemerald names.

Each script is compiled back and compared with the original, command by command
with jump targets resolved to positions. If the structured form doesn't
reproduce it, a plainer one is used (`if (...) { goto(label) }` and labels), then
`raw`. The whole file is compared again at the end. Result for the 452 maps:
2403 scripts structured, 13 structured without the after-`End` blocks, 1 with
labels and gotos, none raw; 2496 movements.

What stays as written, because the bytes depend on it:

- **Dead code** the original compiler left, such as a `goto` right after another
  `goto`, or an `end` after movement data. Removing it changes the ROM.
- **Shared tails**: blocks several branches `goto` keep their label (`_0083:`).
- **Script order**, as a `scrdefs` block, when the scripts aren't in number
  order in the file (209 maps). Scripts keep their numbers; new `script` blocks
  are numbered after the list.
- Two `ScrDef` names for one script, or a script that runs on into the next:
  the second name becomes a label inside the first script.
- Extra `#include`/`#define` lines, in `raw`.

`--raw` keeps the old behavior: `scripts.inc` in one `raw` block, unchanged.
Maps that use another map's scripts (`@Everywhere` in `maps.txt`) share the
owner's `scripts.pory`.

To change a script, edit it and run `make`: same commands in the same order give
the same ROM, whatever the labels are called.

## Build

`data/maps/meson.build`: for each folder with `scripts.pory`, `mapkit pory build` writes
the map's `scr_seq_*.s`, `scr_seq_*_hdr.s` and text bank into the build directory
(under their original names), and the event generator takes script numbers from it.
Errors point at `scripts.pory:<line>`. The compiled file always ends with
`.balign 4, 0`, as every original bank did.

## Editor support

The syntax is poryscript's, so the poryscript VS Code extension
(`karathan.poryscript`) highlights `.pory` files. Its autocomplete reads commands from
macro files; pointing it at `asm/macros/script.inc` and `asm/macros/movement.inc`
(the `commandIncludes` setting) should list the HGSS commands. Not tested yet.

## Not done / differences from poryscript

- No optimizer (output order follows the source, which keeps matching predictable).
- No `format()` text wrapping (needs DS font widths).
- No `mart` (HGSS marts are C tables).
- `raw` can only target `scripts.inc`; `map_scripts.inc` always comes from `mapscripts`.
- Labels inside a script are emitted as written (no local/global distinction on DS).
- `scrdefs` is new: GBA scripts are referenced by address, DS scripts by number.

## Tests

`python3 tools/mapkit/tests/test_pory.py`: lowering of every construct, error
messages, decompiler cases, and an all-maps round trip (compile each
`scripts.pory`, decompile the output, compile again, compare).
