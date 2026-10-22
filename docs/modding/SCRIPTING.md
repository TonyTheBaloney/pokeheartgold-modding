<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Map scripts in `scripts.pory`

> AI-generated, local to this fork. Do not upstream.

A map can keep its scripts in `data/maps/<MapName>/scripts.pory`, written in a
language modeled on [poryscript](https://github.com/huderlem/poryscript): structured
`if`/`while`/`switch` instead of `GoTo` labels, inline text and movement, a
`mapscripts` block, and `raw` for anything else. The compiler lives in
`tools/mapkit/mapkit/pory/`; the build runs it for every map that has a
`scripts.pory`, and uses `scripts.inc` / `map_scripts.inc` for the rest (the same
opt-in pokeemerald uses).

Today **Cherrygrove** uses `scripts.pory`; its Mystic Water script is written in
the structured form and the ROM still matches.

## Quick start

```sh
M=tools/mapkit/mapkit.sh
$M pory init Route30        # scripts.inc + map_scripts.inc -> scripts.pory (ROM unchanged)
$M pory show Route30        # what it compiles to
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
        npcmsg(msg_0550_T21_00020)
        if (!itemspace(ITEM_MYSTIC_WATER, 1)) {
            npcmsg(msg_0550_T21_00022)
            waitbuttonpress
            closemessage
            releaseall
            end
        }
        callstd(std_give_item_verbose)
        setflag(FLAG_GOT_MYSTIC_WATER_FROM_CHERRYGROVE_CITY_MAN)
    }
    npcmsg(msg_0550_T21_00021)
    waitbuttonpress
    closemessage
    releaseall
}
```

compiles to exactly the original commands:

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
| `movement Name { walk_up * 2  face_left }` | movement data (`EndMovement` added) |
| `mapscripts Name { ... }` | the map's init scripts (compiles to `map_scripts.inc`) |
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

- Inline strings (`npcmsg("Hello!\nNice day.")`) become `<Script>_Text_<n>`;
  `text Name { ... }` blocks become `Name`.
- They're appended to the map's bank after the messages in `text.json`, so existing
  message numbers never move. msgenc accepts any id, so names are real names.
- `\n`, `\r`, `\f` and codes like `{STRVAR_1 3, 0, 0}` work as in `text.json`.
- Maps that share another map's text bank (`@Everywhere` in `maps.txt`) can't add text.

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

- Numbers follow file order: `ScrDef` lines inside `raw` blocks and top-level
  `script` blocks (and inline map scripts).
- A `script` block whose name already has a `ScrDef` line in a `raw` block keeps
  that line's number. That's how a script converted out of `raw` keeps its number.
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

## Converting a map

1. `mapkit pory init <map>`: the old `scripts.inc` goes into a `raw` block and
   `map_scripts.inc` becomes a `mapscripts` block. Builds byte-identical; the test
   suite checks this for all 451 maps with their own scripts.
2. Rewrite scripts one at a time: cut a script out of the `raw` block (keep its
   `ScrDef` line), put a `script` block in the same place, and check that `make`
   still matches. Same commands in the same order = same ROM; labels don't matter.
3. Leave the rest in `raw` as long as you like.

Maps that use `Everywhere`'s scripts can't use `scripts.pory`.

## Build

`data/maps/meson.build`: if a folder has `scripts.pory`, `mapkit pory build` writes
the map's `scr_seq_*.s`, `scr_seq_*_hdr.s` and text bank into the build directory
(under their original names), and the event generator takes script numbers from it.
Errors point at `scripts.pory:<line>`.

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

## Tests

`python3 tools/mapkit/tests/test_pory.py`: lowering of every construct, error
messages, and the all-maps `pory init` round trip.
