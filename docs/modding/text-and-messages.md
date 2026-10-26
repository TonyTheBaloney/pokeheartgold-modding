<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Text and messages

> AI-generated; not affiliated with pret. See AI.md at the repository root.

A reference for everything about game text: where messages live, how they are encoded,
every `{...}` code, the string buffers that fill `{STRVAR_1 ...}`, text colors, fonts,
the character map and how much fits on a line. Other guides explain codes one at a
time where they come up. This page has all of them in one place.

**In short:** text is in JSON message banks (`files/msgdata/msg/msg_NNNN.json`, plus
`data/maps/<Map>/text.json` and inline strings in `scripts.pory`). Write `’` and `“ ”`,
not `'` and `"`. End a line with `\n`, and after the second line of a dialogue box use
`\f` (scroll) or `\r` (new box). A line in the dialogue box can be **216 pixels**
wide, about 36 letters. `{STRVAR_1 K, S, 0}` prints string slot **S**, which a
`buffer...` command fills. The **K** is only a label.

| pokeemerald | here |
|---|---|
| `data/text/*.inc`, `.string "..."` | JSON banks, one file per bank, messages by number |
| `charmap.txt` (gflib) | `tools/msgenc/charmap.txt` (UTF-16 codes) |
| `{STR_VAR_1}`, `{STR_VAR_2}`, `{STR_VAR_3}` | `{STRVAR_1 K, 0, 0}` ... `{STRVAR_1 K, 7, 0}`: 8 slots in scripts |
| `{COLOR RED}{SHADOW LIGHT_RED}` | `{COLOR 1}`: one number picks both |
| `\p` (new box), `\l` (scroll) | `\r` (new box), `\f` (scroll) |
| `{PAUSE n}` | `{PAUSE n}` |

## Contents

1. [Message banks](#1-message-banks)
2. [Characters](#2-characters)
3. [Line breaks and boxes](#3-line-breaks-and-boxes)
4. [Control codes](#4-control-codes)
5. [String buffers (`STRVAR`)](#5-string-buffers-strvar)
6. [Colors](#6-colors)
7. [Fonts](#7-fonts)
8. [Line width](#8-line-width)
9. [Recipes](#9-recipes)

## 1. Message banks

A **bank** is one file of numbered messages. The game has 829 of them, `msg_0000` to
`msg_0828`, built into the `msgdata/msg` NARC. The order of
[files/msgdata/NARC_msg.txt](../../files/msgdata/NARC_msg.txt) gives each bank its
number.

### Where each bank's text lives

| Source | Banks | Edit it with |
|---|---|---|
| `files/msgdata/msg/msg_NNNN.json` | most of them | a text editor |
| `data/maps/<Map>/text.json` and the strings in `data/maps/<Map>/scripts.pory` | one per map (`msg_0047_D01R0101` and so on) | `scripts.pory` ([SCRIPTING.md](SCRIPTING.md)), `mapkit text add` |
| `data/items/items.json` | `msg_0222` (names), `msg_0221` (descriptions) | [items.md](items.md) |
| `files/poketool/trainer/trainers.json` | `msg_0729` (trainer names, generated at build), `msg_0728` (battle text, from `trmsg.py build`) | [trainer-text.md](trainer-text.md) |

### The JSON format

```json
{
  "key": 65256,
  "messages": [
    { "id": "msg_0000_00000", "en_US": "EXIT" },
    { "id": "msg_0000_00006", "en_US": ["What will you do with the\n", "selected photo?"] },
    { "id": "msg_0412_00001", "garbage": 0 }
  ]
}
```

- **`key`** is the 16-bit encryption key stored in the bank's header. The game reads
  it from the file, so any value works. Keep the existing one to keep the ROM
  matching.
- **`id`** names the message. msgenc writes `#define msg_0000_00006 6` into the
  generated header `msgdata/msg/msg_0000.h`. The **position** in the array is the
  number the game uses, not the name. Inserting a message shifts every one after it,
  and C code that uses a number (rather than the name) then reads the wrong message.
  Add new messages at the end.
- **`en_US`** is a string or an array of strings. An array is joined with nothing in
  between, so it is only a way to split long text. The `\n` at the end of each piece
  is what makes the line break.
- **`garbage`: n** is a placeholder message of n spaces. Retail has some. Leave them
  so later numbers don't move.
- Entries in a map's `text.json` that have `"from"` and no `en_US` are filled from
  `scripts.pory` by mapkit. Edit the string in the script.

msgenc ([tools/msgenc](../../tools/msgenc)) encodes each bank at build time. Any
character it can't find in the charmap stops the build with
`unrecognized character in <file>: line L pos P value X`.

### Using a bank

From C, see [ui.md §5](ui.md#strings-and-message-files) (`NewMsgDataFromNarc`,
`ReadMsgDataIntoString`, `ReadMsgData_ExpandPlaceholders`). From a map script, a
string in `npcmsg("...")` goes into the map's own bank. `msgboxextern(bank, msg)`
shows a message from another bank ([script-commands.md](script-commands.md#text)).

### Common banks

| Bank | Holds | Read by |
|---|---|---|
| `msg_0040` | gender symbols and other short pieces | `BufferGenderSymbol` |
| `msg_0197` | battle messages | battle scripts ([abilities.md](abilities.md), [battle-engine.md](battle-engine.md#the-commands)) |
| `msg_0221`, `msg_0222`, `msg_0223`, `msg_0224` | item descriptions, names, names with "a/an", plurals | `BufferItemName...` |
| `msg_0226` | bag pocket names | `BufferPocketName` |
| `msg_0237`, `msg_0238` | species names, with "a/an" | `BufferSpeciesName...` ([adding-a-species.md](adding-a-species.md)) |
| `msg_0279`, `msg_0280`, `msg_0281` | location names | `BufferLocationName` |
| `msg_0443`, `msg_0044` | stat names, status names | `BufferStatName`, `BufferStatusName` |
| `msg_0720`, `msg_0034` | ability names, nature names | `BufferAbilityName`, `BufferNatureName` |
| `msg_0728`, `msg_0729` | trainer battle text, trainer names | [trainer-text.md](trainer-text.md) |
| `msg_0730`, `msg_0731` | trainer class names, with "a/an" | `BufferTrainerClassName...` ([trainer-classes.md](trainer-classes.md)) |
| `msg_0735` | type names | `BufferTypeName` ([adding-a-type.md](adding-a-type.md)) |
| `msg_0750` | move names | `BufferMoveName` ([moves.md](moves.md)) |

All `Buffer...` functions are in [src/message_format.c](../../src/message_format.c).
Each one opens its bank there.

### Adding a bank

1. Create `files/msgdata/msg/msg_0829.json` (the next free number) with any `key`.
2. Add `NARC_msg_msg_0829_bin` as a new **last** line of
   `files/msgdata/NARC_msg.txt`. A line in the middle renumbers every bank after it.
3. In C, `msg_0829` (the bank) comes from `msgdata/msg.naix`, and the message names
   from `#include "msgdata/msg/msg_0829.h"`.

[phone.md](phone.md) adds a bank this way for a new phone contact.

## 2. Characters

Characters are 16-bit codes. [tools/msgenc/charmap.txt](../../tools/msgenc/charmap.txt)
maps them to Unicode (`012B=A`). The English font has glyphs for codes `0x0001`-`0x01FD`:

| Codes | Characters |
|---|---|
| `0x0001`-`0x0120` | Japanese (full-width space, kana, kanji-width symbols) |
| `0x0121`-`0x012A` | `0`-`9` |
| `0x012B`-`0x015E` | `A`-`Z`, `a`-`z` |
| `0x015F`-`0x01A7` | accented letters, `Œ œ Ş ş ª º ¹ ² ³` |
| `0x01A8`-`0x01EA` | punctuation and symbols (below) |
| `0x0400`-`0x0D65` | Korean (only in the charmap, no English glyphs) |

Symbols: `$ ¡ ¿ ! ? , . … · / ‘ ’ “ ” „ 《 》 ( ) ♂ ♀ + - * # = & ~ : ; ♠ ♣ ♥ ♦ ★ ◉ ● ■ ▲ ◆ @ ♪ % ☀ ☁ ☂ ☃ ☺ ♚ ♛ ☹ ↗ ↘ ☽ ° _ ＿`.

Things to know:

- **No straight quotes.** `'` and `"` are not in the charmap, so the build fails. Use
  `’` (apostrophe), `‘ ’` and `“ ”`. Retail writes `Pokémon’s`.
- **`₧₦`** is the PKMN ligature, two glyphs 12 px wide each: `"a ₧₦ Trainer"`.
- The space is `0x01DE` (a normal space). `0x01E2` is a narrow space (U+2009).
  `0x0001` is the Japanese full-width space.
- **Raw codes:** `{01AB}` (four hex digits in braces) inserts that code directly.
- `é` is a normal letter, so `Pokémon` and `POKéMON` both work.

## 3. Line breaks and boxes

| Write | Code | Effect ([src/render_text.c](../../src/render_text.c)) |
|---|---|---|
| `\n` | `0xE000` | next line |
| `\r` | `0x25BC` | show the arrow, wait for A/B, **clear** the box and continue at the top |
| `\f` | `0x25BD` | show the arrow, wait for A/B, **scroll** up one line and continue on the last line |

The dialogue box has **two lines** (32 px). The usual pattern:

```
"First line\n"
"second line\r"         ← new box
"Third line\n"
"fourth line\f"         ← scroll: the fourth line moves up
"fifth line"
```

A third line without `\r` or `\f` draws below the box. After the last line, put
nothing: the script's `waitbutton`/`closemsg` handles the end.

In `trainers.json` the codes are written `\\n`, `\\r`, `\\f`
([trainer-text.md](trainer-text.md#text-format)). In `scripts.pory` and the JSON
banks they are written `\n`, `\r`, `\f`.

## 4. Control codes

A code in braces becomes `0xFFFE`, the command, the number of arguments, then the
arguments. All of them come from the end of the charmap.

| Code | Command | Effect | Retail uses |
|---|---|---|---|
| `{STRVAR_1 K, S, 0}` | `0x01KK` | the text in string slot S ([§5](#5-string-buffers-strvar)) | 9,002 |
| `{STRVAR_3 K, S, 0}`, `{STRVAR_4 ...}`, `{STRVAR_34 ...}` | `0x03KK`, `0x04KK`, `0x34KK` | the same; used in Wi-Fi Plaza, Pokéathlon and group text | 208 |
| `{COLOR n}` | `0xFF00` | text color ([§6](#6-colors)) | 3,568 |
| `{SIZE 200}` / `{SIZE 100}` | `0xFF01` | taller letters (each pixel row drawn twice, from the third row down) / normal. Width doesn't change | 31 (Pokéathlon announcer) |
| `{ALN_CENTER}` | `0x0205` | centre the rest of this line in the window | 233 |
| `{ALN_RIGHT}` | `0x0206` | right-align the rest of this line | 6 |
| `{CURSOR_X n}` | `0x0203` | move to x = n pixels (from the window's left edge) | 34 |
| `{CURSOR_Y n}` | `0x0204` | move to y = n pixels | 3 |
| `{PAUSE n}` | `0x0201` | stop for n frames (60 = 1 second), then continue | 65 |
| `{WAIT n}` | `0x0202` | pass n to the screen's text callback (below) | 37 |
| `{YESNO n}` | `0x0200` | draw a 24×32 icon (number n) at the right end of the window | 738 |
| `{UNK_207}`, `{UNK_208}` | `0x0207`, `0x0208` | like `\r` and `\f`, and also skip a `\n` right after | 0 |
| `{TRNAME}` | `0xF100` | the rest of the message is a 9-bit packed name | 10 (`msg_0246`) |

Details:

- **`{YESNO 0}` does not make a Yes/No menu.** It only draws the icon that retail puts
  at the end of a question. The choice comes from the commands after the message
  (`getmenuchoice`, [scripting-basics.md §5](scripting-basics.md#5-asking-a-question)).
- **`{WAIT n}` depends on the screen.** The field dialogue has no callback, so it does
  nothing in map scripts. The Bag uses 3 and 4 for the TM boot-up sound
  (`BagApp_PrintMessageCallback`), and the evolution scene uses 3-5 for fanfares
  (`EvolutionScene_TextCallback`).
- `{ALN_CENTER}` and `{ALN_RIGHT}` measure up to the next `\n`. Put one at the start
  of each line you want aligned.
- **A misspelled code doesn't fail the build.** msgenc reads `{COLOUR 1}` as the raw
  code `0x0001` (a Japanese space). Search the built text if a code seems to be
  ignored.

## 5. String buffers (`STRVAR`)

A `MessageFormat` holds numbered string **slots**. Code fills them (`BufferItemName`
and so on), then `StringExpandPlaceholders` replaces each `{STRVAR_...}` in a message
with the contents of a slot ([src/message_format.c](../../src/message_format.c)).

**Only the slot number matters.** In `{STRVAR_1 K, S, 0}`:

| Part | Meaning | Read by the game? |
|---|---|---|
| `K` | the kind of value (8 = item, 3 = trainer name ...) | **no**, a label from the original text tools |
| `S` | the slot | **yes** |
| `0` | always 0 in retail | no |

So `bufferitemname(0, ...)` followed by `{STRVAR_1 1, 0, 0}` still prints the item. Use
the matching K anyway so the text stays readable.

### Slots

| Where | Slots | Max characters per slot |
|---|---|---|
| map scripts (`script_manager.c`) | 8 (0-7) | 63 |
| `MessageFormat_New` (most screens) | 8 | 31 |
| phone calls | 16 | 36 |
| other screens | `MessageFormat_New_Custom(count, size, heap)` | size - 1 |

A string that doesn't fit isn't copied (the slot keeps its old text). A slot number
past the count is out of bounds. In scripts, an expanded message can be up to 1024
characters.

### Filling slots from a script

Fill the slot, then print the message:

```
bufferitemname(0, VAR_SPECIAL_x8004)
bufferint(1, VAR_SPECIAL_x8006)
npcmsg("{STRVAR_1 8, 0, 0} will cost {STRVAR_1 50, 1, 0} BP.\n"
       "Is that OK? {YESNO 0}")
```

Slots stay filled until something overwrites them, so a later message can reuse them.
The most used commands (all 61 are in
[script-commands-list.md](script-commands-list.md#string-buffers)):

| Command | Fills the slot with | Usual K |
|---|---|---|
| `bufferplayersname(slot)` | the player's name | 3 |
| `bufferrivalsname(slot)` | the rival's name | 3 |
| `bufferitemname(slot, item)` | an item name | 8 |
| `bufferpocketname(slot, pocket)` | a Bag pocket | 27 or 31 |
| `bufferint(slot, value)` | a number, no padding | 50-56 |
| `buffermonspeciesname(slot, party_pos)` | the species of a party Pokémon | 1 |
| `bufferpartymonnick(slot, party_pos)` | a party Pokémon's nickname | 0 |
| `bufferspeciesname(slot, species, 0, 0)` | a species name | 1 |
| `buffermovename(slot, move)` | a move name | 6 |
| `buffertypename(slot, type)` | a type name | 15 |
| `buffertrainerclassname(slot, class)` | a trainer class | 14 |
| `buffermapsecname(slot, mapsec)` | a location name | 4 |

### The K labels in retail text

Retail text uses these K values. The game ignores them, but they tell you what a
message expects.

| K | Holds | K | Holds |
|---|---|---|---|
| 0 | Pokémon nickname | 14 | trainer class |
| 1 | species name | 15 | type |
| 3 | player or trainer name | 17 | status condition |
| 4 | location | 26 | battle cup |
| 5 | ability | 27, 31 | Bag pocket |
| 6 | move | 33 | hour |
| 8 | item | 50-56 | numbers (higher K for longer numbers: 52 item counts, 54 coins, 55 money, 56 steps) |
| 11 | PC box name | 13 | stat |

### In battle

Battle messages (`msg_0197`) are filled by the message's **tag**, in order: with
`TAG_NICKNAME_ABILITY` the nickname goes into slot 0 and the ability into slot 1, so
the text says `{STRVAR_1 1, 0, 0}’s {STRVAR_1 5, 1, 0}`. See
[battle-engine.md](battle-engine.md#the-commands) and
[abilities.md](abilities.md).

### Where placeholders are not expanded

Trainer battle text (`msg_0728`) is printed as stored, so `{STRVAR_1 ...}` shows
nothing useful there ([trainer-text.md](trainer-text.md#text-format)). Any C code that
prints with `ReadMsgDataIntoString` instead of `ReadMsgData_ExpandPlaceholders` or
`StringExpandPlaceholders` behaves the same way.

## 6. Colors

`{COLOR n}` sets the letter color to palette index `2n+1` and the shadow to `2n+2`.
So the colors depend on the window's palette. The field dialogue box uses palette 12,
loaded from `graphic/font` file 8 (`LoadFontPal1`, `FieldMessage_LoadTextPalettes`):

| Code | Letter | Shadow | Retail uses it for |
|---|---|---|---|
| `{COLOR 0}` | dark gray `#52525A` | light gray `#A4A4AC` | normal text (the default) |
| `{COLOR 1}` | red `#EE2010` | pink `#FFACBD` | gifts, key items, warnings |
| `{COLOR 2}` | blue `#0073FF` | light blue `#7BBDEE` | Bag pockets, things to remember |
| `{COLOR 3}`, `{COLOR 4}` | black | black | not used in dialogue; other screens load other palettes |

Write `{COLOR 1}Master Ball{COLOR 0}`. A color lasts until the next `{COLOR}` or the
end of the message.

**`{COLOR 255}`** swaps between the current color and a remembered one. The first
`{COLOR 255}` in a message only remembers the current color (nothing changes). The
next one switches back to it. `{COLOR 100}`-`{COLOR 106}` set the remembered color to
0-6 without changing the current one. Retail's "a/an" banks (`msg_0223`, `msg_0238`
...) wrap every name as `a {COLOR 255}Master Ball{COLOR 0}`. In practice that prints
the name in the color the surrounding text already has.

The other font palette, file 7 (`LoadFontPal0`, palette 13 in the field), has red,
green (`#29D518`) and blue at `{COLOR 1}`, `{COLOR 2}` and `{COLOR 3}`. In C, the
starting colors are the `MAKE_TEXT_COLOR(letter, shadow, background)` argument of
`AddTextPrinterParameterizedWithColor` ([ui.md](ui.md#printing)).

## 7. Fonts

Fonts are in the `graphic/font` NARC (`files/graphic/font/font_*.bin`). The ids are
`enum Font` in [include/font.h](../../include/font.h):

| Id | File | Used for | Width of `A` / `i` / space |
|---|---|---|---|
| `FONT_SYSTEM` (0) | 0 | menus, lists, most screens | 6 / 3 / 6 |
| `FONT_MESSAGE` (1) | 1 | dialogue (`DialogBox_PrintMessage`) | 6 / 3 / 6 |
| `FONT_SUBSCREEN` (2) | 2 | touch screen | 7 / 4 / 5 |
| `FONT_UNOWN` (3) | 3 | Unown letters (fixed width 12) | 12 |
| `FONT_UNK_4` (4) | 4 | Dowsing Machine, friend roster | |
| `FONT_UNK_5` (5) | 10 | | |

The other files: 5 is digit graphics for `MessagePrinter`, 6 is tiles, 7-9 are
palettes.

Fonts 0, 1 and 3 are loaded at boot. Load the others with
`FontID_Alloc(font, heapID)` and free them with `FontID_Release`.

**The font file format** ([src/font_data.c](../../src/font_data.c)): a 16-byte header
(header size, offset of the width table, glyph count = 509, fixed width, fixed height,
cell width and height in tiles = 2×2), then 509 glyphs of 2×2 tiles at 2 bits per
pixel (16×16 px, 64 bytes each), then the width table, one byte per glyph. Character
code `c` uses glyph `c - 1`. A code past the last glyph is drawn as `?` (glyph 428).
No tool here converts these files to PNG yet.

## 8. Line width

`FONT_MESSAGE` has no extra letter spacing: a line is as wide as its glyphs added up.
Widths in pixels (from `font_00000001.bin`):

| px | Characters |
|---|---|
| 3 | `i` |
| 4 | `l ì í î ï ¡` |
| 5 | `f j , . ‘ ’ : ; °` |
| 6 | space, digits, every other letter, most symbols (`! ? … / “ ” ( ) - & ♂ ♀ %` ...) |
| 7 | `$` |
| 10 | `Æ æ Œ œ` |
| 12 | `₧ ₦` (so `₧₦` is 24) |

| Window | Width | About |
|---|---|---|
| dialogue box (`DialogBox_AddWindowToLayer3`, 27 tiles) | **216 px** | 36 letters |
| sign with a map picture (`DialogBox_AddWindowToLayer3WithXOffset` types 0-1, 20 tiles) | 160 px | 26 letters |

Retail's longest lines are exactly 216 px. `{STRVAR_1 ...}` adds its contents, so
leave room for the longest value it can hold:

| Slot holds | Longest | px |
|---|---|---|
| player name (`PLAYER_NAME_LENGTH` 7) | `MMMMMMM` | 42 |
| nickname or species (`POKEMON_NAME_LENGTH` 10) | `CHARMANDER` | 60 |
| item | `EnergyPowder` | 72 |
| move | `ThunderPunch` | 72 |
| trainer class | `₧₦ Breeder` | 70 |
| location | `Sunyshore Market` | 94 |

**`mapkit validate -w`** checks every line of map text (`text.json` and the strings in
`scripts.pory`) and warns about each line over 216 px (`text-width`). It counts
`{STRVAR_1 K, ...}` as the longest name for K (read from the banks above, so longer
names you add are included) and numbers as 0. No retail line warns.

```
data/maps/Cherrygrove/scripts.pory:59: warning [text-width] line is 259 px (names counted at their longest), the text box is 216: 'You’re a rookie Trainer, aren’t you? I can tell!'
```

It doesn't check other banks (`files/msgdata/msg/`), and it can't tell signs (160 px)
from dialogue. To measure any line by hand (run from the repository root):

```sh
python3 - "It looks like the strange writing on the" <<'EOF'
import struct, sys
cm = {}
for line in open('tools/msgenc/charmap.txt', encoding='utf-8-sig'):
    line = line.rstrip('\r\n')
    if '=' in line and not line.startswith('//') and not line.split('=', 1)[1].startswith('{'):
        code, ch = line.split('=', 1)
        cm[ch] = int(code, 16)
d = open('files/graphic/font/font_00000001.bin', 'rb').read()
_, start, count = struct.unpack('<III', d[:12])
print(sum(d[start + cm[c] - 1] for c in sys.argv[1]), 'px of 216')
EOF
```

## 9. Recipes

**A message with the player's name and an item in blue:**

```
bufferplayersname(0)
bufferitemname(1, ITEM_HYPER_POTION)
npcmsg("{STRVAR_1 3, 0, 0}! Take this\n"
       "{COLOR 2}{STRVAR_1 8, 1, 0}{COLOR 0} with you.")
```

**A long speech:** keep each line under 216 px, `\n` after the first line of a box
and `\r` (new box) or `\f` (scroll) after the second.

**A dramatic pause:** `"Wait...{PAUSE 30} Is that...?"`.

**Rename something everywhere:** names come from their banks (table in
[§1](#common-banks)), so change them there once. Dialogue that spells the name out
(rather than using a slot) has to be changed too. Search all text with
`grep -rn "Old Name" files/msgdata/msg data/maps`.

**Change the dialogue text colors:** edit palette file 8 (`files/graphic/font/font_00000008.bin`,
an NCLR). Indices 1-2 are normal text, 3-4 `{COLOR 1}`, 5-6 `{COLOR 2}`. Other
screens load the same file, so the change shows there too.
