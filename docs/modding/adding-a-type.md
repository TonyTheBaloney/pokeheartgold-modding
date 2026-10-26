<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Adding a type

> AI-generated; not affiliated with pret. See AI.md at the repository root.

A type is a number from 0 to 17 (`TYPE_NORMAL` ... `TYPE_DARK`, with 9 the `???` type).
Gen 4 already decides physical or special per move (`"category"` in
`battle_moves.json`), so a new type is only a number. You give it a name, add it to
the type chart, draw two icons, and pick a color for the battle move buttons. A few
tables have one row per type, and those need a new row.

This guide adds **Fairy** with its Gen 6 matchups. Steps 1-7 were built together with
`make release`; see [Not verified](#not-verified) for what wasn't tried in game.

| pokeemerald | here |
|---|---|
| `include/constants/pokemon.h` (`TYPE_*`, `NUMBER_OF_MON_TYPES`) | `include/constants/pokemon.h` (`TYPE_*`; there is no count, step 1 adds one) |
| `gTypeNames` in `src/battle_main.c` | `files/msgdata/msg/msg_0735.json` |
| `gTypeEffectiveness` in `src/battle_main.c` | `sTypeEffectiveness` in `src/battle/battle_util.c` |
| `graphics/types/*.png` + `sMoveTypeToOamPaletteNum` | `graphics/battle_sprites/type_icons/*.png` + `src/type_icon_resources.c`; the Pokédex has its own icons in `files/graphic/zukan_gra/` |

## What to change

| Step | File | Needed? |
|---|---|---|
| [1. Constant](#1-the-constant) | `include/constants/pokemon.h` | yes |
| [2. Name](#2-the-name) | `files/msgdata/msg/msg_0735.json` | yes: the name is read by type id |
| [3. Type chart](#3-the-type-chart) | `src/battle/battle_util.c` | yes, or the type is neutral to everything |
| [4. Battle icon](#4-the-type-icon-summary-bag-battle-pc) | `graphics/battle_sprites/`, `src/type_icon_resources.c`, 2 C files | yes: the table is read by type id, and the contest icons come right after the types |
| [5. Move button color](#5-the-move-button-color-in-battle) | `include/overlay_06.h` | yes: the table is read by type id |
| [6. Pokédex icon](#6-the-pokédex-icon) | `files/graphic/zukan_gra/`, `src/application/pokedex/pokedex_text_util.c` | yes: the table is read by type id |
| [7. Pokémon and moves](#7-giving-the-type-to-pokémon-and-moves) | `personal.json`, `battle_moves.json` | to use it |
| [8. Held items](#8-optional-held-items) | `battle_util.c`, a battle subscript, `items.json` | optional |

Asserts are compiled out of `make release` (`include/assert.h`), so a table that is
one row short is read past its end, with no error. The result is the wrong icon, a
garbage palette, or a crash, so do steps 1-6 together.

The JSON converters read `TYPE_*` from the header (`tools/pokedata/pokedata.py` for
moves, the C preprocessor for `personal.json`), so `"TYPE_FAIRY"` works in both files
once the constant exists.

**Saves.** A Pokémon's types aren't saved. They are read from its species data
whenever they're needed (`GetBoxMonDataInternal`, `src/pokemon.c:863`), so retyping a
species changes the Pokémon already in a save, and a new type keeps saves
compatible.

## 1. The constant

`include/constants/pokemon.h`, after `TYPE_DARK` (line 35):

```c
#define TYPE_DARK           17
#define TYPE_FAIRY          18

#define NUM_TYPES           19 // type icons for contest categories come after the types
```

The new type must be 18. Types are indexes into tables (names, icons, button
colors), and 255, 254 and 253 are taken (`TYPE_NONE`, `TYPE_FORESIGHT`,
`TYPE_ENDTABLE`). `NUM_TYPES` is new: step 4 uses it.

## 2. The name

`files/msgdata/msg/msg_0735.json`, at the end. The position is the type id:

```json
    {
      "id": "msg_0735_00018",
      "en_US": "FAIRY"
    }
```

`BufferTypeName` (`src/message_format.c:229`) reads this file by type id, for
battle messages that name a type (Conversion's "X transformed into the FAIRY type!",
Color Change's), the Battle Hall and the Wi-Fi Plaza. Gen 4
writes type names in capitals. The longest is "ELECTRIC" (8 letters).

**Easy Chat** also uses this file as its type word list. It offers 18 words
(`EC_WORDS_TYPE_COUNT`, `include/constants/easy_chat.h:30`). Don't raise the count:
every Easy Chat word after the types would get a new id, which breaks saved mail
and Trainer Card messages (as for abilities, [abilities.md](abilities.md#limits)).
Fairy just isn't an Easy Chat word.

## 3. The type chart

`sTypeEffectiveness` (`src/battle/battle_util.c:2086`) is a list of
`{ attacking type, defending type, multiplier }`. A pair that isn't listed is
neutral. The multipliers are `TYPE_MUL_SUPER_EFFECTIVE` (×2),
`TYPE_MUL_NOT_EFFECTIVE` (×½) and `TYPE_MUL_NO_EFFECT` (×0).

Add the new rows **before** the `TYPE_FORESIGHT` row (line 2195):

```c
    { TYPE_STEEL,     TYPE_STEEL,     TYPE_MUL_NOT_EFFECTIVE   },
    { TYPE_FAIRY,     TYPE_FIGHTING,  TYPE_MUL_SUPER_EFFECTIVE },
    { TYPE_FAIRY,     TYPE_DRAGON,    TYPE_MUL_SUPER_EFFECTIVE },
    { TYPE_FAIRY,     TYPE_DARK,      TYPE_MUL_SUPER_EFFECTIVE },
    { TYPE_FAIRY,     TYPE_FIRE,      TYPE_MUL_NOT_EFFECTIVE   },
    { TYPE_FAIRY,     TYPE_POISON,    TYPE_MUL_NOT_EFFECTIVE   },
    { TYPE_FAIRY,     TYPE_STEEL,     TYPE_MUL_NOT_EFFECTIVE   },
    { TYPE_FIGHTING,  TYPE_FAIRY,     TYPE_MUL_NOT_EFFECTIVE   },
    { TYPE_BUG,       TYPE_FAIRY,     TYPE_MUL_NOT_EFFECTIVE   },
    { TYPE_DARK,      TYPE_FAIRY,     TYPE_MUL_NOT_EFFECTIVE   },
    { TYPE_POISON,    TYPE_FAIRY,     TYPE_MUL_SUPER_EFFECTIVE },
    { TYPE_STEEL,     TYPE_FAIRY,     TYPE_MUL_SUPER_EFFECTIVE },
    { TYPE_DRAGON,    TYPE_FAIRY,     TYPE_MUL_NO_EFFECT       },
    { TYPE_FORESIGHT, TYPE_FORESIGHT, TYPE_MUL_NO_EFFECT       },
    { TYPE_NORMAL,    TYPE_GHOST,     TYPE_MUL_NO_EFFECT       },
    { TYPE_FIGHTING,  TYPE_GHOST,     TYPE_MUL_NO_EFFECT       },
    { TYPE_ENDTABLE,  TYPE_ENDTABLE,  TYPE_MUL_NO_EFFECT       }
```

Where a row goes matters:

- **Before `TYPE_FORESIGHT`.** When the target is under Foresight or Odor Sleuth, or
  the attacker has Scrappy, the damage loop stops at the `TYPE_FORESIGHT` row
  (`BattleSystem_ApplyTypeEffectiveness`, line 2279). The two rows after it, Normal
  and Fighting against Ghost, are the immunities those effects remove. If you add an
  immunity that Foresight should also remove, put it after that row.
- **Order within the list.** Each matching row multiplies the damage and rounds
  down, one row at a time. Against a dual-type target, the order of the two rows
  can change the result by 1 HP. It doesn't change effectiveness.

The same table is used, unchanged, by:

| What | Where |
|---|---|
| damage, and the "super effective" messages | `BattleSystem_ApplyTypeEffectiveness` (line 2231) |
| the trainer AI's effectiveness checks | `CalcTypeEffectivenessFlags` (line 2334), `CalculateTypeEffectiveness` (line 2579) |
| Conversion 2 (picks a type that resists the last move) | `GetTypeEffectivnessData` (line 2564), `BtlCmd_TryConversion2` (`battle_command.c:2881`) |

Some effects only apply to certain rows (`BattleSystem_IsTypeMatchupActive`, line
2202). Iron Ball, Ingrain, Roost and Gravity remove Flying's immunity to Ground.
Miracle Eye removes Dark's immunity to Psychic. A Fairy immunity (Dragon) isn't
affected by any of them.

**Gen 6 also changed Steel**: it no longer resists Ghost or Dark. To match, delete
the `{ TYPE_GHOST, TYPE_STEEL, ... }` and `{ TYPE_DARK, TYPE_STEEL, ... }` rows.

## 4. The type icon (summary, bag, battle, PC)

One set of icons, `graphics/battle_sprites/type_icons/*.png` (built into the archive
`a/0/0/8`, [graphics-sources.md](graphics-sources.md#6-graphicsbattle_sprites-a008)), is
used by the summary screen, the bag (TMs), the move relearner, the battle move info, the
battle party menu, the PC and the Wi-Fi Plaza. `src/type_icon_resources.c` maps a type to
an archive member and a palette row:

```c
static const int sTypeIconGfxCharFileIds[23] = {
    234, 225, 227, 235, 229, 237, 231, 228, 238, 236, 226, 241, 233, 222, 223, 230, 221, 224, 240, 219, 220, 232, 239
};

static const u8 sTypeIconGfxPlttOverrides[23] = { 0, 0, 1, 1, 0, 0, 2, 1, 0, 2, 0, 1, 2, 0, 1, 1, 2, 0, 0, 1, 1, 2, 0 };
```

The first 18 entries are the types. **Entries 18-22 are the five contest
categories** (Cool, Beauty, Cute, Smart, Tough), which the move relearner and the
battle party menu reach with `contest category + 18`. Fairy has to be entry 18, so
the contest icons move up by one.

### The icon file

An icon is a 32×16 PNG with 16 colors (`type_icons/psychic.png`...). All the type icons
share one palette file, `type_icons/palette.pal`, which holds three 16-color palettes;
`sTypeIconGfxPlttOverrides` chooses one of them for each type (`"palette_row"` in
`members.json`, so each PNG shows its own colors). This is palette 1, the one Psychic, Flying, Water
and Ice use:

| Index | Color | Used by |
|---:|---|---|
| 0 | transparent | |
| 1, 2, 3 | lavender, light purple, dark purple | Flying, Ghost |
| 4, 5, 6 | blue, light cyan, pale cyan | Water, Ice |
| 7 | dark purple | Poison, Ghost |
| 8, 9, 10 | pink, peach, brown | Psychic |
| 11, 12 | purple, light pink | Poison |
| 13 | grey | Ice |
| 14, 15 | grey (letter shadow), white (letters) | all |

Every icon has the same layout: a highlight row along the top, the body color, a
shadow row along the bottom, and the name in white (15) with a grey shadow (14) one
pixel right and down. Psychic is 9 / 8 / 10. The Fairy icon used here is 9 / 12 / 11:
Psychic's frame recolored, with "FAIRY" written in the same 4-pixel-wide letters
(F, I and R can be copied from FIRE).

The other two palettes hold the other types' colors. Don't change colors that other
icons use. Indexes that no icon uses are free; check by converting each icon to PNG
and looking at the indexes it uses.

Copy an existing icon as a template and draw on it, keeping its colors' indexes, then
add it **at the end** of `members` in `graphics/battle_sprites/members.json` (adding at
the end keeps every other member number). It becomes member 346:

```sh
cp graphics/battle_sprites/type_icons/psychic.png graphics/battle_sprites/type_icons/fairy.png
# ... draw fairy.png (32x16, 4-bit indexed) ...
```

```json
    {"file": "type_icons/fairy.png", "format": "ncgr_v101_sprite_32k_lz", "palette": "type_icons/palette.pal", "palette_row": 1, "cell": "type_icons/cells.NCER.json"}
```

The format and cells are the other icons'. `make` then builds the icon into the
archive.

### The tables

In `src/type_icon_resources.c`, insert the new member (346) and its palette (1) at
position 18, and make both tables 24 long:

```c
static const int sTypeIconGfxCharFileIds[24] = {
    234, 225, 227, 235, 229, 237, 231, 228, 238, 236, 226, 241, 233, 222, 223, 230, 221, 224, 346, 240, 219, 220, 232, 239
};

static const u8 sTypeIconGfxPlttOverrides[24] = { 0, 0, 1, 1, 0, 0, 2, 1, 0, 2, 0, 1, 2, 0, 1, 1, 2, 0, 1, 0, 1, 1, 2, 0 };
```

Then move the contest icons: replace `+ 18` with `+ NUM_TYPES` in three places:

- `src/application/move_relearner/move_relearner_app.c:1423`:
  `type = GetMoveAttr(move, MOVEATTR_CONTEST_TYPE) + NUM_TYPES;`
- `src/battle/battle_party_menu.c:3212` and `:3217`:
  `(u8)(GetMoveAttr(..., MOVEATTR_CONTEST_TYPE) + NUM_TYPES)`

Both files include `constants/pokemon.h` already. HGSS has no contests, but these
code paths still exist.

## 5. The move button color in battle

The four move buttons on the touch screen are colored by move type.
`sMoveTypePalettes` (`include/overlay_06.h:378`) has one 16-color palette per type,
in BGR555 (`0bBBBBBGGGGGRRRRR`). Only entries 2-9 differ between types: 2-8 are the
button, light to dark, and 9 is its highlight. The others are shared. Add a palette
and append it to the list:

```c
static const u16 sMoveTypePalette_Fairy[] = {
    0x75CD,
    0x7FFF,
    0x5E7F,
    0x5A3F,
    0x51DE,
    0x49BD,
    0x3D59,
    0x30F4,
    0x24AF,
    0x6F1F,
    0x18C6,
    0x0000,
    0x318C,
    0x52F9,
    0x637C,
    0x0000,
};

static const u16 *const sMoveTypePalettes[] = {
    ...
    sMoveTypePalette_Dark,
    sMoveTypePalette_Fairy,
};
```

This palette is Psychic's with the hue moved to pink (340°) and the saturation
lowered by a quarter. To make one for another color, convert a similar type's
entries 2-9 to RGB (each channel × 8), change them, and convert back.

## 6. The Pokédex icon

The Pokédex draws its own, larger type icons (48×16) on the entry page and in the
popup after a catch. They are PNGs in `files/graphic/zukan_gra/`: members 36-52, one
per type, with `???` reusing Normal's. `src/application/pokedex/pokedex_text_util.c`
maps each type to a file and to one of four palettes:

```c
static const u8 sTypeIconPaletteNums[19] = { 0, 2, 0, 3, 1, 1, 3, 2, 0, 0, 2, 2, 1, 1, 1, 0, 2, 3, 1 };

static const u32 sTypeIconGfxCharFileIds[19] = { 36, 42, 50, 46, 44, 41, 47, 43, 45, 36, 37, 39, 38, 40, 51, 49, 52, 48, 123 };
```

(Make both 19 long and add the last value.) The archive's members are the files
listed in `files/graphic/zukan_gra/meson.build`, in file-number order, so a new icon
is the next free number, `zukan_gra_00000123.png` (the build put it at member 123).
Add it to the end of `zukan_gra_png_clobber` in that `meson.build`. That file has Windows line endings (CRLF), so
keep them when you edit it.

**The PNG format** is unusual:

- It is 8×96, 4-bit **grayscale**: twelve 8×8 tiles in a column. Tiles 0-7 are the
  left 32×16 (four across, two down) and tiles 8-11 the right 16×16 (two across, two
  down), as `zukan_gra_00000033.NCER` places them.
- The color index of a pixel is **15 minus** its gray level (0-15). `nitrogfx` reads
  grayscale this way, so white is index 0.
- Each icon uses only a few indexes of its palette. In every icon the letters are
  index 14 (gray level 1) with a shadow of index 15 (gray level 0), one pixel right
  and down. The frame and background colors differ per icon.

Copy a type with the colors you want (Psychic for Fairy), and change only the letters.
The letters are 2 pixels thick, and several icons can lend you letters: FIRE has F,
I, R; GRASS has A; FLYING has Y. This script turns an icon into a 48×16 image to
edit and back. It uses Pillow, and ImageMagick to write 4-bit grayscale, which
Pillow can't:

```python
# dexicon.py: python3 dexicon.py unpack in.png out48.png | pack in48.png out.png
import subprocess, sys
from PIL import Image

PLACES = [((i % 4) * 8, (i // 4) * 8) for i in range(8)] + [(32 + (i % 2) * 8, (i // 2) * 8) for i in range(4)]

def unpack(src, dst):
    strip, wide = Image.open(src).convert("L"), Image.new("L", (48, 16))
    for i, (x, y) in enumerate(PLACES):
        wide.paste(strip.crop((0, i * 8, 8, i * 8 + 8)), (x, y))
    wide.save(dst)

def pack(src, dst):
    wide, strip = Image.open(src).convert("L"), Image.new("L", (8, 96))
    for i, (x, y) in enumerate(PLACES):
        strip.paste(wide.crop((x, y, x + 8, y + 8)), (0, i * 8))
    strip.save(dst)
    subprocess.run(["magick", dst, "-depth", "4", "-define", "png:color-type=0",
                    "-define", "png:bit-depth=4", "PNG:" + dst], check=True)

{"unpack": unpack, "pack": pack}[sys.argv[1]](sys.argv[2], sys.argv[3])
```

Keep the 16 gray levels exact (0, 17, 34 ... 255) when you draw. Converting
`zukan_gra_00000051.png` with this ImageMagick command and then with `nitrogfx`
gives the same sprite data as the original.

## 7. Giving the type to Pokémon and moves

Species types are in `files/poketool/personal/personal.json`
([pokemon.md](pokemon.md#base-stats-types-abilities-items-tmhm)), move types in
`files/poketool/waza/battle_moves.json` ([moves.md](moves.md#move-data-battle_movesjson)):

```json
      "types": [
        "TYPE_FAIRY",
        "TYPE_FAIRY"
      ],
```

```json
    "MOVE_CHARM": {
        "effect": "MOVE_EFFECT_ATK_DOWN_2",
        "category": "CATEGORY_STATUS",
        "power": 0,
        "type": "TYPE_FAIRY",
```

A single-type Pokémon lists its type twice. The Gen 6 changes for Pokémon and moves
in HGSS:

| Species | Gen 6 types |
|---|---|
| Cleffa, Clefairy, Clefable, Togepi, Snubbull, Granbull | Fairy |
| Togetic, Togekiss | Fairy / Flying |
| Igglybuff, Jigglypuff, Wigglytuff, Azurill | Normal / Fairy |
| Marill, Azumarill | Water / Fairy |
| Mime Jr., Mr. Mime, Ralts, Kirlia, Gardevoir | Psychic / Fairy |
| Mawile | Steel / Fairy |

| Move | Gen 6 type |
|---|---|
| Charm, Sweet Kiss, Moonlight | Fairy |

A move's animation doesn't depend on its type, so retyped moves look the same.

## 8. Optional: held items

These need a new item, which [items.md](items.md#adding-an-item) covers (constant,
`items.json`, names, icon). Hold effects are numbered up to 146
(`HOLD_EFFECT_EVOLVE_DUSCLOPS`, `include/constants/items.h:306`), so new ones start
at 147.

**A type-boosting item** (Gen 6 Pixie Plate's boost, or a Fairy Incense). Add a hold
effect and a row to `sTypeEnhancingItems` (`battle_util.c:5470`). Every row there
boosts by the item's hold effect parameter (20 for the existing items):

```c
    { HOLD_EFFECT_STRENGTHEN_FAIRY,    TYPE_FAIRY    },
```

**A resist berry** (Roseli Berry: halves a super-effective Fairy hit). This one is a
battle script, `files/battledata/script/subscript/subscript_0264_SuperEffectiveBerries.s`.
It compares the holder's hold effect against each `HOLD_EFFECT_WEAKEN_SE_*` and then
the move type against a number. Add a compare after the Steel one (line 39) and a
branch:

```
    CompareVarToValue OPCODE_EQU, BSCRIPT_VAR_TEMP_DATA, HOLD_EFFECT_WEAKEN_SE_FAIRY, _fairy
    GoTo _262

_fairy:
    CompareVarToValue OPCODE_EQU, BSCRIPT_VAR_CALC_TEMP, TYPE_FAIRY, _245
    GoTo _262
```

`_245` plays the animation, halves the damage and prints "The {item} weakened
{Pokémon}'s power!". The trainer AI doesn't know about resist berries, as for the
existing ones.

**Natural Gift** takes its type and power from the berry's `"naturalGiftType"` and
`"naturalGiftPower"` in `items.json`, so a berry can be Fairy with no code.

**Not covered: Pixie Plate and Arceus.** Arceus's form number *is* its type
(`BoxMon_UpdateArceusForm`, `src/pokemon.c:3450`), so Fairy Arceus would be form 18.
That needs form data and sprites the game doesn't have (`ARCEUS_FORM_MAX`,
`src/pokemon.c:2311`), a Judgment case in four places (`GetArceusTypeByHeldItemEffect`
`src/pokemon.c:3461`, `GetDynamicMoveType` `battle_util.c:6633`, `trainer_ai.c:2738`
and `:2976`, `battle_controller_opponent.c:1237`), and a case in the Judgment effect
script (`effect_script_0268.s`).

## What else lists types

Checked, with what happens to Fairy if you change nothing:

| Feature | Where | With Fairy |
|---|---|---|
| Hidden Power | `battle_command.c:3686`, `battle_util.c:6691`, `trainer_ai.c:2829`, `:3055`, `battle_controller_opponent.c:1300`, `scrcmd_pokemon_misc.c:583` | never Fairy: the formula gives Fighting to Dark and skips `???`. Gen 6+ is the same. |
| Conversion | `BtlCmd_TryConversion` (`battle_command.c:2357`) | works: it copies a move's type |
| Pokédex search by type | `include/application/pokedex/pokedex_internal_constants.h:57-76`, `pokedex_search.c`, the search screen | no Fairy button. A Pokémon is found under its other type; a pure Fairy one (Clefairy) can't be found by type. A button needs new screen graphics (`sSearchTypeOptionRects`, `pokedex_screen_setup.c:324`). |
| Battle Hall | `src/frontier/battle_hall_app.c`, `include/frontier/battle_hall_data.h:13` | a fixed board of 17 types plus the Matron; Fairy isn't a choice. Its ranks are saved per cell, so a new cell changes the save. |
| Wi-Fi Plaza favorite type | `sWiFiPlazaTypeChoices`, `src/wifi_plaza/wifi_plaza_apps.c:201` | not offered |
| Following Pokémon | `FollowMonSituation_ConvertType` (`src/field/follow_mon_interaction.c:753`) | Fairy has no case and becomes `FOLLOW_MON_TYPE_NONE`, so a rule that asks for a type never matches it. Mapping it to another type (`case TYPE_FAIRY: return FOLLOW_MON_TYPE_PSYCHIC;`) borrows that type's lines. |
| Pal Park score | `src/catching_show.c` | works (a bit per type, up to 32) |
| Trainer AI scripts | `asm/trainer_ai_data.s` (raw bytes, [trainers.md](trainers.md#the-ai-scripts)) | type checks in them are fixed numbers; not checked for anything Fairy should be added to |
| Easy Chat | [step 2](#2-the-name) | not a word |

## Checklist

- [ ] `TYPE_FAIRY 18` and `NUM_TYPES 19` in `include/constants/pokemon.h`
- [ ] `msg_0735_00018` "FAIRY" at the end of `msg_0735.json`
- [ ] chart rows in `sTypeEffectiveness`, before `TYPE_FORESIGHT`
- [ ] `type_icons/fairy.png`, last in `graphics/battle_sprites/members.json` (member
      346); entry 18 in both tables in
      `type_icon_resources.c`; `+ 18` → `+ NUM_TYPES` (3 places)
- [ ] `sMoveTypePalette_Fairy` appended to `sMoveTypePalettes`
- [ ] `zukan_gra_00000123.png`, listed in `meson.build`; both tables in
      `pokedex_text_util.c`
- [ ] the type in `personal.json` and `battle_moves.json`
- [ ] `make release`

## Not verified

- Steps 1-7 were built together (with Clefairy and Charm made Fairy) and the ROM
  built. Nothing was tried in game: not the icons on each screen, the button color,
  the damage numbers, or the messages.
- The held items in step 8 were not built.
- The palette numbers that `sTypeIconPaletteNums` picks were not traced to the
  colors the Pokédex shows. The Fairy Pokédex icon reuses Psychic's palette and
  indexes, so it should look like Psychic's with new letters.
