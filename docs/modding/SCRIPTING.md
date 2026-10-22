<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Design: a poryscript-style language for HGSS map scripts

> AI-generated, local to this fork. Do not upstream. Proposal; nothing here is built yet.

## Goal

Write map scripts the way pokeemerald modders write
[poryscript](https://github.com/huderlem/poryscript): structured `if`/`while`/`switch`
instead of `GoTo` labels, inline text, `movement` blocks, `mapscripts`, and
`raw` for anything else. The compiler turns a map's `scripts.pory` into the
`scripts.inc`, `map_scripts.inc` and text this repo already builds.

Matching stays safe: existing maps keep their `.inc` files. A map uses the new
language only when it has a `scripts.pory` (the same opt-in pokeemerald uses).

## Where poryscript fits and where it doesn't

Sources: poryscript README, CHANGELOG (3.6.1), emitter source.

| poryscript | HGSS | Plan |
|---|---|---|
| `if`/`elif`/`else`, `while`, `do-while`, `switch`, `break`/`continue`, `&&` `\|\|` `!` | `GoTo`/`Call` labels | Same syntax, same lowering |
| `flag(F)` -> `goto_if_set` | `GoToIfSet` / `GoToIfUnset` | 1:1 |
| `var(V) == n` -> `compare` + `goto_if_eq` | `Compare V, n` (picks var-to-var or var-to-value itself) + `GoToIfEq/Ne/Lt/Le/Gt/Ge` | 1:1 |
| `defeated(T)` -> `checktrainerflag` | `GoToIfDefeated` / `GoToIfNotDefeated` | 1:1, one instruction |
| Branch mnemonics hard-coded in Go | HGSS also has commands with a built-in branch (`GoToIfNoItemSpace ITEM, n, label`) | **Data-driven condition table** (below) |
| AutoVar commands (`if (checkitem(X))`) via `command_config.json` | Many commands write a var (`GetMenuChoice VAR`, `CheckBadge B, VAR`) | Same idea, same config |
| Inline text -> `.string` in the `.inc` | Text is a separate msgenc JSON bank, referenced by id | **Compiler writes text entries** (below) |
| Every `script` is a global label | Event data refers to scripts by **number** (the `ScrDef` table) | **Top-level scripts become `ScrDef` entries** in order (below) |
| `mapscripts` -> `map_script` tables | Separate `map_scripts.inc` with `InitScriptEntry_*`, frame table `InitScriptGoToIfEqual` | **Second output file** |
| `movement M { walk_up * 5 }` | `WalkNormalNorth 5` (macros take a count) | `* n` becomes the count argument |
| `mart` | Marts are C tables (`src/scrcmd_mart.c`), not script data | Dropped |
| `poryswitch(GAME) { ... }` | HG vs SS differences | Keep; key `GAME` = `HEARTGOLD`/`SOULSILVER` |
| `raw` | | Keep (escape hatch) |
| `format("...")` text wrapping by font width | DS font, box width, `{STRVAR_1 ...}` codes | Later; needs DS font widths |
| Optimizer reorders blocks | Matching wants predictable output | Off by default; deterministic when on |
| Generated labels `_1`, `_7` | Diff noise | Named: `<Script>_If_1`, `<Script>_Else_1`, ... |

## Example

`data/maps/Cherrygrove/scripts.pory`, rewriting the real Mystic Water script
(`Cherrygrove_EventScript_MysticWaterMan`, text from `msg_0550_T21_00020`-`00022`):

```
const FLAG_MYSTIC_WATER = FLAG_GOT_MYSTIC_WATER_FROM_CHERRYGROVE_CITY_MAN

script Cherrygrove_EventScript_MysticWaterMan {
    PlaySE(SEQ_SE_DP_SELECT)
    LockAll
    FacePlayer
    if (!flag(FLAG_MYSTIC_WATER)) {
        NPCMsg("A Pokémon I caught had an item.\n"
               "I think it’s Mystic Water.\r"
               "I don’t need it, so do you want it?\r")
        if (!itemspace(ITEM_MYSTIC_WATER, 1)) {
            NPCMsg(Cherrygrove_Text_NoRoom)
            WaitButton
            CloseMsg
            ReleaseAll
            end
        }
        CallStd(std_give_item_verbose)
        SetFlag(FLAG_MYSTIC_WATER)
    }
    NPCMsg(Cherrygrove_Text_BackToFishing)
    WaitButton
    CloseMsg
    ReleaseAll
}

text Cherrygrove_Text_BackToFishing { "Back to fishing for me, then." }
text Cherrygrove_Text_NoRoom { "You don’t have room for this." }

movement Cherrygrove_Movement_GuideGentWalk {
    WalkNormalNorth * 2
    FaceEast
}

mapscripts Cherrygrove_MapScripts {
    INIT_SCRIPT_ON_TRANSITION: Cherrygrove_OnTransition
    INIT_SCRIPT_ON_FRAME_TABLE [
        VAR_SCENE_CHERRYGROVE_CITY_OW, 0: Cherrygrove_EventScript_GuideGentTour
    ]
}
```

Generated `scripts.inc` (script part):

```asm
	ScrDef Cherrygrove_EventScript_MysticWaterMan
	...
	ScrDefEnd

Cherrygrove_EventScript_MysticWaterMan:
	PlaySE SEQ_SE_DP_SELECT
	LockAll
	FacePlayer
	GoToIfSet FLAG_GOT_MYSTIC_WATER_FROM_CHERRYGROVE_CITY_MAN, Cherrygrove_EventScript_MysticWaterMan_EndIf_1
	NPCMsg Cherrygrove_EventScript_MysticWaterMan_Text_0
	GoToIfNoItemSpace ITEM_MYSTIC_WATER, 1, Cherrygrove_EventScript_MysticWaterMan_If_2
	CallStd std_give_item_verbose
	SetFlag FLAG_GOT_MYSTIC_WATER_FROM_CHERRYGROVE_CITY_MAN
Cherrygrove_EventScript_MysticWaterMan_EndIf_1:
	NPCMsg Cherrygrove_Text_BackToFishing
	WaitButton
	CloseMsg
	ReleaseAll
	End

Cherrygrove_EventScript_MysticWaterMan_If_2:
	NPCMsg Cherrygrove_Text_NoRoom
	...
	End
```

`map_scripts.inc`:

```asm
	InitScriptEntry_OnTransition _EV_Cherrygrove_OnTransition + 1
	InitScriptEntry_OnFrameTable Cherrygrove_MapScripts_FrameTable
	InitScriptEntryEnd

Cherrygrove_MapScripts_FrameTable:
	InitScriptGoToIfEqual VAR_SCENE_CHERRYGROVE_CITY_OW, 0, _EV_Cherrygrove_EventScript_GuideGentTour + 1
	InitScriptFrameTableEnd

	InitScriptEnd
```

Plus text entries `Cherrygrove_EventScript_MysticWaterMan_Text_0`,
`Cherrygrove_Text_BackToFishing`, `Cherrygrove_Text_NoRoom`, and the `_EV_*`
block of `ids.h`.

## The four HGSS-specific parts

### 1. Script numbers (`ScrDef`)

- Every top-level `script` gets a `ScrDef` entry, **in file order**, and an
  `_EV_<label>` define in the generated part of `ids.h`. `map.json` already
  accepts `"script": "<label>"` and turns it into `_EV_<label> + 1`.
- `script(local) Helper { ... }` is a label only (for `Call`/`GoTo`), with no number.
- Reordering scripts renumbers them; `map.json` uses labels, so that's safe
  unless something outside the map uses a number (the compiler warns when a
  number changes).
- Init scripts are numbered the same way, because init entries refer to
  script numbers, not labels.

### 2. Text

- msgenc accepts any id (`#define <id> <index>`), so messages can have real names.
- Inline strings get `<Script>_Text_<n>`; `text Name { ... }` blocks get `Name`.
- The map's `text.json` stays the source for existing messages. The compiler
  writes a generated bank: `text.json` entries first (unchanged order, so their
  numbers don't move), then the `.pory` text in file order. msgenc builds that.
- String rules follow poryscript: adjacent literals join; DS control codes
  (`\n`, `\r`, `\f`, `{STRVAR_1 3, 0, 0}`) pass through.
- Later: `format()` with DS font widths.

### 3. Conditions and commands from data, not code

poryscript hard-codes Gen 3 mnemonics. Here a config file
(`tools/mapkit/script_config.json`) lists:

```json
{
  "conditions": {
    "flag":      { "true": "GoToIfSet {0}, {label}",  "false": "GoToIfUnset {0}, {label}" },
    "defeated":  { "true": "GoToIfDefeated {0}, {label}", "false": "GoToIfNotDefeated {0}, {label}" },
    "itemspace": { "false": "GoToIfNoItemSpace {0}, {1}, {label}" },
    "var":       { "compare": "Compare {0}, {1}",
                   "==": "GoToIfEq {label}", "!=": "GoToIfNe {label}", "<": "GoToIfLt {label}",
                   "<=": "GoToIfLe {label}", ">": "GoToIfGt {label}", ">=": "GoToIfGe {label}" }
  },
  "autovar": {
    "GetMenuChoice": { "var_arg": 0 },
    "CheckBadge":    { "var_arg": 1 }
  },
  "jumps": { "goto": "GoTo", "call": "Call", "return": "Return", "end": "End" }
}
```

A condition with only one branch form (`itemspace` has no "has space" jump) is
lowered by inverting the surrounding branch. Command signatures (arguments,
which arguments are labels) come from `asm/macros/script.inc`, which mapkit
already parses.

### 4. Two outputs per map

`scripts.pory` -> `scripts.inc` + `map_scripts.inc` + generated text bank + the
`_EV_` block of `ids.h`. `ids.h` gets marked sections:

```c
// BEGIN generated by mapkit from scripts.pory; do not edit
#define _EV_Cherrygrove_EventScript_GuideGent 0
...
// END generated
#define obj_T21_gsoldman1 0
```

## Build integration

As in pokeemerald (`scripts.pory` next to `scripts.inc`):

- `data/maps/meson.build`: if a map folder has `scripts.pory`, add a
  `custom_target` running `mapkit pory` that outputs the `.s` files, the text
  JSON and `ids.h` into the build directory, and use those instead of the copies.
- cpp line markers (`# 12 "scripts.pory"`) so assembler errors point at the
  `.pory` line, as poryscript's `-lm` does.
- `mapkit validate` keeps working, because it reads the generated output.

## Converting existing maps

1. `mapkit pory init <map>` wraps the current `scripts.inc` and `map_scripts.inc`
   in `raw` blocks: builds identically on day one (what pokeemerald's migration
   recipe did).
2. Scripts are converted one at a time, by hand or by a decompiler that recognizes
   the `GoToIfSet`/`Compare`+`GoToIfXx` patterns. A script counts as converted
   when the ROM still matches (optimizer off, labels in the original order).
3. Maps nobody edits can stay `.inc` forever.

## Editor support

Keeping poryscript's syntax means the existing
[VS Code extension](https://marketplace.visualstudio.com/items?itemName=karathan.poryscript)
(language server: poryscript-pls) gives highlighting, and its autocomplete can be
pointed at this repo:

```json
"poryscript.commandIncludes": ["asm/macros/script.inc", "asm/macros/movement.inc"],
"poryscript.symbolIncludes": [
  { "expression": "^\\s*#define\\s+(FLAG_\\w+)", "type": "constant", "file": "include/constants/flags.h" },
  { "expression": "^\\s*#define\\s+(VAR_\\w+)", "type": "constant", "file": "include/constants/vars.h" }
]
```

HGSS command names are PascalCase (`NPCMsg`, `LockAll`); the language server reads
them from the macro file, so that works as is. Diagnostics for HGSS-only syntax
(`script(local)` already exists; `mapscripts` keys differ) may need small changes.

## Implementation choice

| Option | For | Against |
|---|---|---|
| **A. Python, inside mapkit** (recommended) | Same toolchain as the rest of the build (stdlib Python); reuses mapkit's macro table, `ids.h`/`map.json`/text handling and validator; config-driven from the start | New parser (~1–1.5k lines); poryscript features arrive as we add them |
| B. Fork poryscript (Go) | Parser, optimizer and tests exist | Emitter is Gen 3-specific (mnemonics, text, mapscripts, no ScrDef); Go toolchain in the build; long-lived fork |

Either way the `.pory` syntax stays poryscript-compatible, so editor support and
modder familiarity carry over.

## Order of work

1. Parser for `script`, `text`, `movement`, `mapscripts`, `raw`, `const`; `if`/`while`/`switch`
   with `flag`/`var`/`defeated` conditions; no optimizer.
2. Generated outputs + meson wiring; `mapkit pory init` (raw wrap). Check: a
   raw-wrapped map still matches.
3. Text naming and the generated bank; `ids.h` generated section.
4. Config-driven conditions/autovars; `poryswitch` for HG/SS.
5. Optional: decompiler for converting existing scripts; optimizer; `format()`.

## Open questions

- Generated label style: `<Script>_If_1` (readable) vs poryscript's `<Script>_1`.
- Should `text.json` eventually be generated entirely from `.pory` for converted maps?
- Whether to keep PascalCase command names (matches the macros) or add
  lowercase aliases like pokeemerald (`lock`, `faceplayer`).
