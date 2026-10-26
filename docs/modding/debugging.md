<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Debugging

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers how to find out what the game is doing: what the build gives you to
debug with, which emulators can help, printing messages (`DebugPrintf`, or gdb's
`dprintf` with no rebuild), breakpoints and stepping with gdb, catching failed
assertions and failed allocations, and adding a debug menu opened with SELECT.

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `DebugPrintf` / `MgbaPrintf` (mGBA's log) | nothing is built in: `OS_Printf` compiles to nothing. Add the 30-line `DebugPrintf` from §3. It prints in melonDS and no$gba |
| `AGB_ASSERT` | `GF_ASSERT`, but a failed assert does **nothing** outside a link session (§5) |
| mGBA's GDB server + `pokeemerald.elf` | melonDS's GDB stub + `build/heartgold.us/main.nef` (§4) |
| `pokeemerald.map` | `build/heartgold.us/main.nef.xMAP` |
| "Add a debug menu" (`debug.c`) | a shared script opened with SELECT in the overworld (§6) |
| one address = one function | most code is in **overlays**, which share addresses: one address can be 30+ functions (§4.4) |

The files:

| File | What |
|---|---|
| `build/heartgold.us/main.nef` | ELF with every symbol, the types and line numbers (but no code bytes; gdb reads those from the emulator) |
| `build/heartgold.us/main.nef.xMAP` | linker map: address, size and object file of every function and variable, overlay by overlay |
| [tools/debug/pokeheartgold.gdb](../../tools/debug/pokeheartgold.gdb) | gdb setup: source paths, `$loaded("overlay")`, `debuglog`, `whereis` |
| [include/assert.h](../../include/assert.h), [src/error_handling.c](../../src/error_handling.c) | `GF_ASSERT` and what a failed one does |

## 1. What the build gives you

- **Symbols, types and lines.** The C files are compiled with `-sym on`
  ([meson.build](../../meson.build)), so `main.nef` has every function and global
  variable, every struct type, and a line table. gdb can show `ptype struct FieldSystem`,
  print globals and stop at `field_control.c:300`.
- **Optimized code.** Everything is built `-O4,p`. Local variables mostly live in registers
  and the debug info doesn't say which, so gdb usually can't print locals. Print function
  arguments from registers instead: at a function's first instruction, arguments 1-4
  are `$r0`-`$r3`. Pointers to structs can be cast: `print *(FieldSystem *)$r0`.
- **A retail SDK.** The SDK is configured `SDK_FINALROM`, which turns `OS_Printf`,
  `OS_TPrintf`, `OS_Warning` and `OS_Panic` into nothing (`OS_Panic` into
  `OS_Terminate`, an endless halt). `OS_SPrintf` / `OS_VSNPrintf` (formatting into a
  buffer) are in the ROM and work.

**Finding a function from an address**, without gdb:

```sh
nm -n build/heartgold.us/main.nef | grep -i 0203fe74      # static code: one answer
grep -i "021E6AF4" build/heartgold.us/main.nef.xMAP        # overlay code: one line per overlay
nm build/heartgold.us/main.nef | grep " StartMapSceneScript$"   # address of a function
```

The plain `nm` works; you don't need an ARM toolchain for it. For an address inside a
function (not its start), use `whereis` from the gdb script (§4.4).

Adding any debug code changes the ROM, so `make` fails its checksum tests. Build with
`make release` while you debug; that is the same as for any mod
([README.md](README.md#building-a-modified-rom)).

## 2. Emulators

| Emulator | Prints `DebugPrintf` | gdb | Other tools |
|---|---|---|---|
| **melonDS** (1.0 or later) | yes, to the terminal it was started from | yes: built-in GDB stub | none for memory; use gdb |
| **no$gba** (debug version, Windows; free) | yes, in its debug message window | no | its own debugger: breakpoints, memory, disassembly; loads symbols (§4.6) |
| **DeSmuME** | no (read `gDebugLog` instead, §3) | yes (`--arm9gdb=PORT` on builds that have it) | memory viewer, disassembler |

melonDS is the one this guide uses. To turn on its GDB stub: **Config > Emu settings >
Devtools**, tick **Enable GDB stub**. The ARM9 port is 3333 (the game's code runs on the
ARM9; 3334 is the ARM7, which runs sound and Wi-Fi). Tick **Break on startup** to stop
before the first instruction. The stub doesn't work with the JIT recompiler, so leave the
JIT off (it is off by default).

## 3. printf

### Adding `DebugPrintf`

`DebugPrintf` formats like `printf` and sends the line two ways:

- to the **no$gba debug port** at `0x04FFFA18`: the emulator prints the string plus a
  newline. melonDS and no$gba support it. Other emulators and a real DS ignore the
  write, so the call is harmless anywhere.
- to **`gDebugLog`**, a 2 KB ring buffer in RAM, for emulators without the port: read it
  with the gdb command `debuglog` (§4), or in a memory viewer at the address
  `nm build/heartgold.us/main.nef | grep gDebugLog` prints.

`include/debug_print.h`:

```c
#ifndef POKEHEARTGOLD_DEBUG_PRINT_H
#define POKEHEARTGOLD_DEBUG_PRINT_H

void DebugPrintf(const char *fmt, ...);

#endif // POKEHEARTGOLD_DEBUG_PRINT_H
```

`src/debug_print.c`:

```c
#include "debug_print.h"

#include "global.h"

// no$gba debug port: write the address of a 0-terminated string, the emulator
// prints it plus a newline. melonDS supports it too; other emulators and real
// hardware ignore the write.
#define REG_NOCASH_STRING_OUT_LF (*(vu32 *)0x04FFFA18)

#define DEBUG_LOG_SIZE 0x800

// The last DEBUG_LOG_SIZE characters printed, for emulators without the port:
// read them from gdb or a memory viewer. gDebugLogPos is where the next one goes.
char gDebugLog[DEBUG_LOG_SIZE];
u32 gDebugLogPos;

void DebugPrintf(const char *fmt, ...) {
    char line[128];
    va_list args;
    int i;

    va_start(args, fmt);
    OS_VSNPrintf(line, sizeof(line), fmt, args);
    va_end(args);

    REG_NOCASH_STRING_OUT_LF = (u32)line;

    for (i = 0; line[i] != '\0'; i++) {
        gDebugLog[gDebugLogPos++ % DEBUG_LOG_SIZE] = line[i];
    }
    gDebugLog[gDebugLogPos++ % DEBUG_LOG_SIZE] = '\n';
}
```

Add it to the build in two places. It goes in the static ARM9 (the code that is always
loaded), so every overlay can call it:

- [src/meson.build](../../src/meson.build): add `'debug_print.c',` to the list (it is
  alphabetical; next to `'error_handling.c',` is fine).
- [main.lsf](../../main.lsf): in the `Static main` block, add
  `Object main.nef.p/src_debug_print.c.o` next to `Object main.nef.p/src_error_handling.c.o`.
  A `.c` file the `.lsf` doesn't name isn't linked, and the build fails with an
  undefined `DebugPrintf`.

It costs a little over 2 KB of main RAM (the log and the function). That moves every overlay
up by the same amount; [engine.md](engine.md#5-overlays) explains why that is usually
fine. Make `DEBUG_LOG_SIZE` smaller if RAM is tight.

### Using it

```c
#include "debug_print.h"

DebugPrintf("map %d, x %d, z %d", fieldSystem->location->mapId,
    PlayerAvatar_GetXCoord(fieldSystem->playerAvatar), PlayerAvatar_GetZCoord(fieldSystem->playerAvatar));
```

- `%d %u %x %s %c %p` work. There is no `%f` (the game has no floats; fixed-point `fx32`
  values print with `%d`, and are 4096 per 1.0).
- A line is cut at 127 characters.
- It is not safe from an interrupt handler (`line` is on the stack, but two
  `DebugPrintf` calls could interleave in `gDebugLog`).
- In melonDS, the line appears in the terminal melonDS was started from. On Windows,
  start melonDS from a console (`cmd`, PowerShell) to see it.

Before a release, delete the calls (or keep them; on hardware they only cost time).

### printf without rebuilding: gdb `dprintf`

With gdb attached (§4), `dprintf` prints at any function or line and lets the game
continue, with no change to the ROM:

```
(gdb) dprintf StartMapSceneScript,"script %d\n",$r1
(gdb) continue
script 2064
script 3
```

`StartMapSceneScript(fieldSystem, script, object)` gets the script id as its second
argument, so `$r1` at its first instruction is the id. This prints every map script,
sign and std script the player starts (§6 of [script-commands.md](script-commands.md)
explains the ids). It is slower than `DebugPrintf` (the emulator stops and gdb prints)
but needs nothing compiled in.

## 4. gdb

### 4.1 Setup

You need a gdb that can debug ARM. On Linux, the distribution's `gdb` usually can (run
`gdb -batch -ex "set architecture armv5te"`: it should print "The target architecture is
set to armv5te"). Otherwise install `gdb-multiarch` (Debian, Ubuntu) or
`arm-none-eabi-gdb` (devkitARM, Arm GNU toolchain). The gdb script uses Python, which
the usual builds have.

1. Build: `make release`.
2. Start melonDS with the GDB stub on (§2), and open `build/heartgold.us/pokeheartgold.us.nds`.
3. From the repository root:

```sh
gdb -x tools/debug/pokeheartgold.gdb build/heartgold.us/main.nef
(gdb) target remote localhost:3333
```

If melonDS is set to break on startup, gdb stops at the first instruction; type
`continue`. Otherwise the game pauses where it was. Rebuild and reload the ROM, and gdb
needs `file build/heartgold.us/main.nef` (or a restart) to read the new symbols. Old
breakpoints still point at old addresses; delete and set them again.

[tools/debug/pokeheartgold.gdb](../../tools/debug/pokeheartgold.gdb) sets the
architecture, and then:

- **Adds every folder under `src/`, `lib/src/` and `asm/` as a source directory.** The
  compiler writes Windows-style paths (`\home\...\src\field\/field_control.c`) into the
  debug info, which gdb on Linux can't open. It does find a source by file name in the
  directory list, so `list` and stepping show the C. If two folders have a file with the
  same name, gdb may show the wrong one.
- Defines `$loaded("name")`, `debuglog` and `whereis` (below).

### 4.2 Commands you'll use

| Command | Does |
|---|---|
| `break StartMapSceneScript` | stop when a function starts |
| `break field_control.c:300` | stop at a line |
| `tbreak X` | stop once, then delete the breakpoint |
| `break X if $r1 == 2072` | stop only when the condition holds |
| `info breakpoints`, `delete 2`, `disable 2` | list, delete, turn off |
| `continue` (`c`), Ctrl-C | run; stop wherever the game is |
| `next` (`n`), `step` (`s`), `finish` | next line, into a call, to the end of this function |
| `stepi`, `x/8i $pc` | one instruction; show the next 8 instructions |
| `info registers`, `print/x $r0` | registers |
| `print *(FieldSystem *)$r0` | a struct an argument points to |
| `print gSystem.newKeys`, `print/x gSystem` | a global (here: buttons pressed this frame) |
| `ptype struct PlayerAvatar` | the layout of a type |
| `x/32xb ADDR`, `x/s ADDR` | raw memory as bytes, as a string |
| `watch *(u8 *)0x021D2000` | stop when that byte is written |
| `dprintf FUNC,"fmt",args` | print and continue (§3) |
| `debuglog` | what `DebugPrintf` wrote (needs §3) |
| `whereis $pc` | which function(s) an address belongs to (§4.4) |

### 4.3 Breakpoints worth keeping

| Breakpoint | Catches |
|---|---|
| `break GF_AssertFail` | every failed `GF_ASSERT` (§5). Then `info symbol $lr` (or `whereis $lr`) names the function that asserted |
| `break AllocFail` | every failed `Heap_Alloc` (out of memory). The caller gets `NULL` and usually crashes a moment later; this stops before that |
| `dprintf StartMapSceneScript,"script %d\n",$r1` | which script runs when you talk, step on a trigger, read a sign |
| `break Save_VarsFlags_SetFlagInArray if $r1 == 0x6A` | who sets a flag (0x6A is `FLAG_GOT_STARTER`; ids in [include/constants/flags.h](../../include/constants/flags.h)). Then `info symbol $lr` |
| `break PrintErrorMessageAndReset` | the "An error has occurred" screen (only in link modes) |

Script `SetFlag` goes through `Save_VarsFlags_SetFlagInArray`. A few places in C may
write a flag's byte directly, which this breakpoint misses; a watchpoint on the byte
(`Save_VarsFlags_GetFlagAddr` returns it) catches those too.

### 4.4 Overlays: one address, many functions

Most code is in overlays, and overlays that replace each other start at the same address
([engine.md](engine.md#5-overlays)). In the unmodified US HeartGold build,
`FieldInput_Process` starts at `0x021E6AF4` while the map is loaded, and `0x021E6B00`
(12 bytes into it) is also inside a function of each of 32 other overlays (the Pokédex,
the PC, Voltorb Flip...). Adding code moves these addresses. This affects gdb in three
ways:

- **gdb's names can be wrong.** It labels an overlay address with whichever symbol it
  finds first, so `info line`, `x/i`, `bt` and stepping can name the wrong function and
  file:

  ```
  (gdb) info line *0x21e6b00
  Line 1327 of "...\src\/alph_puzzle.c" starts at address 0x21e6b00 <AlphPuzzle_UpdateHoverGraphicOnBg+68> ...
  ```

  The address is right; the name isn't. Ask `whereis`:

  ```
  (gdb) whereis 0x21e6b00
  0x021e6b00  WifiConnection_ClassifyErrorCode+144  (src_wifi_connection.c.o)
  0x021e6b00  FieldInput_Process+12  (src_field_field_control.c.o)
  0x021e6b00  PCBox_CanSwapHeldItems+96  (src_application_pc_box_pc_box.c.o)
  ...
  ```

  and pick the one whose overlay is loaded.

- **A breakpoint stops in whichever overlay is loaded there.** A breakpoint on a field
  function also stops in the Pokédex when you open it. Add a condition:

  ```
  (gdb) break FieldInput_Process if $loaded("field")
  ```

  `$loaded("name")` reads the game's list of loaded overlays (`sOverlayRegions` in
  [src/poke_overlay.c](../../src/poke_overlay.c)). Names are the ones in
  [main.lsf](../../main.lsf): `field`, `OVY_2`, `OVY_12` (battle)... The xMAP line from
  `whereis` names the object file; `grep` that file name in `main.lsf` to see its overlay.

- **Breakpoints survive overlay loads in melonDS.** Its stub keeps breakpoints itself
  instead of writing a breakpoint instruction into RAM, so loading an overlay over the
  address doesn't erase them. (An emulator that writes the instruction into RAM loses the
  breakpoint when the overlay is loaded again.)

Static ARM9 code (addresses below `0x021E5900`, roughly) has one function per address and
none of these problems: `GF_AssertFail`, `Heap_Alloc`, `StartMapSceneScript`, the script
engine.

### 4.5 When the game freezes or crashes

1. Press Ctrl-C in gdb. The game stops where it is.
2. `whereis $pc` and `whereis $lr`: where it is and (usually) who called it.
3. `x/8i $pc`: the instructions there.
4. `bt` may work for a few frames; on optimized Thumb code without frame info it often
   stops early or guesses. `x/32xw $sp` shows the stack; return addresses are the
   values that `whereis` resolves to code.

Common causes:

| Symptom | Look at |
|---|---|
| `$pc` in the middle of nowhere, or in an overlay that shouldn't be loaded | code called into an overlay that isn't loaded; see [engine.md](engine.md#loading-and-unloading) |
| `$pc` near `0` or reading address 0 | a `NULL` pointer, often from a failed allocation (`break AllocFail`) |
| a loop in `OS_Terminate` | an `OS_Panic` in SDK code |
| stuck in a script (no input, no crash) | `dprintf StartMapSceneScript`, then the script's `Wait...` commands; `break RunScriptCommand` and step |

### 4.6 no$gba symbols

no$gba's debugger shows labels from a `.sym` file next to the ROM with the same name:
one `ADDRESS NAME` per line, and `.arm` / `.thumb` as the name to mark ARM or Thumb
code. no$gba also says it reads ELF files directly, so try `main.nef` first. To make a
`.sym`:

```sh
nm -n build/heartgold.us/main.nef \
  | awk '$3 == "$a" { print $1, ".arm"; next } $3 == "$t" { print $1, ".thumb"; next }
         $3 !~ /^\$/ && $2 ~ /[TtDdBb]/ { print $1, $3 }' \
  > build/heartgold.us/pokeheartgold.us.sym
```

Overlay addresses get many labels each (§4.4).

## 5. Assertions

`GF_ASSERT(expr)` ([include/assert.h](../../include/assert.h)) calls `GF_AssertFail` when
`expr` is false. `GF_AssertFail` ([src/error_handling.c](../../src/error_handling.c))
only does something during a link session (wireless or Wi-Fi): it shows "An error has
occurred" and resets. **In normal play it returns, and the game continues** with whatever
was wrong. A failed heap allocation is the same: `AllocFail` in
[src/heap.c](../../src/heap.c) returns, and `Heap_Alloc` returns `NULL`.

So while you test a mod, keep `break GF_AssertFail` and `break AllocFail` set. When one
stops, `whereis $lr` is the function that failed (the assert is often in a small helper;
`finish` and `whereis $lr` again to go one caller up).

Without gdb, make each assert print its file and line (with §3 added). In
[include/assert.h](../../include/assert.h), replace the `PM_KEEP_ASSERTS` definition:

```c
#define GF_ASSERT(expr) ((expr) ? (void)0 : GF_AssertFailAt(__FILE__, __LINE__))
```

declare `void GF_AssertFailAt(const char *file, int line);` in
[include/error_handling.h](../../include/error_handling.h), and add to
[src/error_handling.c](../../src/error_handling.c):

```c
#include "debug_print.h"

void GF_AssertFailAt(const char *file, int line) {
    DebugPrintf("GF_ASSERT failed: %s:%d", file, line);
    GF_AssertFail();
}
```

The compiler's `__FILE__` is only the file name (`field_control.c`), so this adds one
short string per source file. It does make every assert a little bigger, which moves
code in every overlay; check free RAM afterwards ([engine.md](engine.md#6-heaps)).
(`__return_address()`, which some CodeWarrior versions have, is not a built-in here: it
compiles to a call to an undefined function and the link fails.)

## 6. A debug menu

This adds a menu that opens with **SELECT** in the overworld, with three entries: heal
the party, 99 Rare Candies, 100,000 money. It is a shared ("std") script, so it works on
every map, and its text comes from a shared message file. SELECT does nothing in the
overworld in HeartGold (the registered item is Y), so nothing else is lost.

Five files change:

**1. The script id**, in
[include/constants/std_script.h](../../include/constants/std_script.h), after
`std_fade_end_rival_outro_music`:

```c
#define std_debug_menu                 2072
```

Ids 2000-2499 are `std_misc`: script `id - 2000` of
`files/fielddata/script/scr_seq/scr_seq_0003.s`, with messages from `msg_0040`
(`sScriptBankMapping` in [src/script_manager.c](../../src/script_manager.c)). Retail
uses 0-71, so 2072 is the next free one.

**2. The script**, in
[files/fielddata/script/scr_seq/scr_seq_0003.s](../../files/fielddata/script/scr_seq/scr_seq_0003.s).
Add `ScrDef scr_seq_0003_072` after `ScrDef scr_seq_0003_071` (before `ScrDefEnd`), and
the script at the end of the file, before the final `.balign 4, 0`:

```
scr_seq_0003_072:
	PlaySE SEQ_SE_DP_SELECT
	LockAll
	NPCMsg msg_0040_00117
	MenuInit 1, 1, 0, 1, VAR_SPECIAL_RESULT
	MenuItemAdd msg_0040_00118, 255, 0
	MenuItemAdd msg_0040_00119, 255, 1
	MenuItemAdd msg_0040_00120, 255, 2
	MenuExec
	Switch VAR_SPECIAL_RESULT
	Case 0, _debug_heal
	Case 1, _debug_rare_candy
	Case 2, _debug_money
	GoTo _debug_close

_debug_heal:
	HealParty
	GoTo _debug_done

_debug_rare_candy:
	GiveItem ITEM_RARE_CANDY, 99, VAR_SPECIAL_RESULT
	GoTo _debug_done

_debug_money:
	AddMoney 100000
_debug_done:
	NPCMsg msg_0040_00121
	WaitABPress
_debug_close:
	CloseMsg
	ReleaseAll
	End
```

And in
[files/fielddata/script/scr_seq/event_0003.h](../../files/fielddata/script/scr_seq/event_0003.h),
after the `_071` line:

```c
#define _EV_scr_seq_0003_072 72
```

The script is in the assembler format of the shared script files, not `scripts.pory`.
The commands are the same ones (macros in
[asm/macros/script.inc](../../asm/macros/script.inc));
[script-commands.md](script-commands.md) lists them. `MenuInit` takes x, y, the first
cursor row, whether B cancels (1), and the result var. `MenuItemAdd` takes the message,
a help message (255 = none) and the value it writes. B writes `0xFFFE`, which falls
through to `_debug_close`.

**3. The text**, at the end of `messages` in
[files/msgdata/msg/msg_0040.json](../../files/msgdata/msg/msg_0040.json) (retail ends at
`msg_0040_00116`):

```json
    {
      "id": "msg_0040_00117",
      "en_US": "Debug menu"
    },
    {
      "id": "msg_0040_00118",
      "en_US": "Heal party"
    },
    {
      "id": "msg_0040_00119",
      "en_US": "99 Rare Candies"
    },
    {
      "id": "msg_0040_00120",
      "en_US": "100000 money"
    },
    {
      "id": "msg_0040_00121",
      "en_US": "Done."
    }
```

`NPCMsg` takes the message number as one byte, so this file can't go past 255 messages.
[text-and-messages.md](text-and-messages.md) covers the format.

**4. The button**, in `FieldInput_Process` in
[src/field/field_control.c](../../src/field/field_control.c), just before the start
menu check (`if (fieldInput->menu && FieldSystem_MapIsNotMysteryZone(...`):

```c
    if (fieldInput->stationary && (fieldInput->newKeys & PAD_BUTTON_SELECT)) {
        StartMapSceneScript(fieldSystem, std_debug_menu, NULL);
        return 1;
    }
```

`stationary` is set only when the player isn't between steps; returning 1 tells the
field that an event started. To also log the position (with §3, and
`#include "debug_print.h"` at the top):

```c
        DebugPrintf("debug menu: map %d, x %d, z %d", fieldSystem->location->mapId,
            PlayerAvatar_GetXCoord(fieldSystem->playerAvatar), PlayerAvatar_GetZCoord(fieldSystem->playerAvatar));
```

**5. Build** with `make release`.

### More entries

Add a `MenuItemAdd`, a message, a `Case` and a label. Useful commands for a debug menu
(all in [script-commands.md](script-commands.md)):

| Entry | Commands |
|---|---|
| give a Pokémon | `GiveMon SPECIES_X, level, item, form, ability, VAR_SPECIAL_RESULT` |
| set a story flag / var | `SetFlag FLAG_X`, `SetVar VAR_X, value` ([story-progression.md](story-progression.md)) |
| warp | `Warp MAP_X, 0, x, z, direction` (the 0 is unused) |
| start a battle | `WildBattle SPECIES_X, level`; trainers: [trainers.md](trainers.md) |
| a submenu | another `MenuInit` ... `MenuExec` block, then `GoTo` back |

For something the script commands can't do (walk through walls, print a value), add a
script command ([script-commands.md](script-commands.md#6-adding-a-command)) or check
another button in C next to the SELECT check.

### Before a release

Remove the SELECT check (step 4). The script and text can stay; nothing else calls
`std_debug_menu`. None of this touches the save file.

## Not verified

- Nothing here was run in an emulator. `DebugPrintf` and the debug menu (§3, §6) were
  built and linked into the US HeartGold ROM (`make release`) and then removed; the gdb
  script and every gdb command in §4 that doesn't need a running game (`break` by name
  and line, `list`, `ptype`, `whereis`, `dprintf`, the `$loaded` condition) were run
  against `main.nef` without an emulator.
- melonDS's handling of the debug port (prints to its log, which its desktop frontend
  writes to stdout), its GDB stub settings, its default port 3333 and its breakpoints not
  being written into RAM come from reading melonDS's source, not from running it.
- no$gba printing writes to `0x04FFFA18`, its `.sym` format and its reading of ELF files
  come from its documentation; DeSmuME's `--arm9gdb` option from older reports. Neither
  was tried.
- `$loaded` and `debuglog` read game memory, so they were only checked for syntax.
- The `GF_AssertFailAt` macro in §5 was compiled in a test file, not built into the
  whole ROM; how much bigger the code gets wasn't measured.
- Whether `MenuInit` at 1, 1 overlaps the "Debug menu" text box: retail uses the same
  position after a message (`MenuInitStdGmm 1, 1, ...` in `scr_seq_0003.s`).
