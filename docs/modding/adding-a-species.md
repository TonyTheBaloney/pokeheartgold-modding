<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Adding a new species

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide adds a Pokémon after Arceus, from the constant to a wild encounter: data,
text, Pokédex, sprites, icon, footprint, cry, the following Pokémon and the Pokéathlon.
The steps were done on a copy of the repository with a test species, `SPECIES_NEWMON`,
made from Pikachu's data and graphics; HeartGold and SoulSilver both build with it.
**It has not been played**: see [Not verified](#not-verified).

The examples use `SPECIES_NEWMON` and copy Pikachu (species 25) wherever a step needs
something to start from. Replace both with yours.

If you know pokeemerald's "adding a new Pokémon" tutorial: it is the same list of
tables, but here many of them are binary archives or JSON lists in species order, and
the eggs and the alternate forms come right after the last species, so they move.

## 0. Before you start

**The number.** The new species is **494**, right after Arceus. Its Pokédex number is its
species number. `SPECIES_EGG`, `SPECIES_BAD_EGG` and the form entries
(`SPECIES_DEOXYS_ATK` ... `SPECIES_ROTOM_MOW`) move up by one. They are only used
through their names, so moving them is safe; what matters is that every list in species
order gets the new entry **in the right place**, and each step below says where.

A second species is 495, and so on; repeat each step. Some steps differ for the second
one and are marked.

**Saves.** One new species keeps the save layout, and so existing saves, unchanged
(checked with `tools/savemap/savemap.py`). A second one does not: the Battle Hall's
per-species records hold species 0-494 (`stats[3][495]` in
[include/frontier_save_access.h](../../include/frontier_save_access.h)), and species 495
would write past them. Raise that `495` and accept that the extra save data changes.
Past 496 the Pokédex save (`caughtLanguages` in [include/pokedex.h](../../include/pokedex.h))
and the Pokéathlon medals (`bytes1F0`, one byte per species, in
[include/pokeathlon/pokeathlon_save.h](../../include/pokeathlon/pokeathlon_save.h)) grow
too. See [save-data.md](save-data.md).

**Binary archives.** Seven steps edit binary files. They use `nitroarc`, which the build
makes, to unpack an archive into numbered files and pack it again (this gives back the
same file byte for byte):

```sh
NARC=build/heartgold.us/tools/nitroarc/nitroarc
mkdir -p /tmp/narc && cp files/poketool/pokegra/height.narc /tmp/narc/
$NARC -xf /tmp/narc/height.narc                  # -> /tmp/narc/height.narc.d/00000.bin ...
# ... add or change files in height.narc.d ...
ls /tmp/narc/height.narc.d | sort > /tmp/narc/order.txt
$NARC -cf files/poketool/pokegra/height.narc -T /tmp/narc/order.txt /tmp/narc/height.narc.d
```

Unpack a copy, not the file in `files/`: `-x` writes the `.d` folder next to the archive.

**The checklist.**

| Step | Files | Where the new entry goes |
|---|---|---|
| [1. Constant](#1-the-constant) | `include/constants/species.h` | 494; Egg, Bad Egg and forms +1 |
| [2. C limits](#2-five-checks-in-c) | 5 C files | `SPECIES_ARCEUS` → `MAX_SPECIES`; Oak's rating |
| [3. Base stats](#3-base-stats-evolutions-moves) | `personal.json` | position 494 (before `EGG`) |
| [3. Evolutions, learnset](#3-base-stats-evolutions-moves) | `evo.json`, `level_up_learnsets.json` | by name |
| [3. Tutor moves](#3-base-stats-evolutions-moves) | `waza_oshie.json` | after Arceus |
| [4. Egg species](#4-egg-species-pmsnarc) | `pms.narc` (binary) | position 494 |
| [5. Text](#5-name-and-pokédex-text) | `msg_0237`, `msg_0238`; `msg_0803`-`msg_0828` | 494 (before Egg); at the end |
| [6. Pokédex](#6-pokédex) | `zukan_data.json`, `zukan_enc.json`, `zukan_hw_data_1_*.bin`, `johtozukan.narc` | end; sorted lists; before `egg` |
| [7. Battle sprites](#7-battle-sprites) | `pokegra/0494/`, 2 ranges, `height.narc`, `a/1/8/0` | end |
| [8. Icon, footprint](#8-icon-and-footprint) | `poke_icon_00000551.png`, `pokefoot_00000497.png`, `pokemon_icon_idx.c` | end, plus C |
| [9. Cry](#9-cry) | `sound/sound_data.json`, a WAV, `sound_playback.c` | bank 494; Shaymin Sky's moves |
| [10. Following Pokémon](#10-following-pokémon) | `src/follow_mon.c`; for its own model also a texture, `tp_param.csv`, 2 C changes | end of 3 tables |
| [11. Pokéathlon](#11-pokéathlon) | `performance.narc`, `src/pokemon.c` | end |
| [12. In the game](#12-putting-it-in-the-game) | encounters, trainers, scripts | |

## 1. The constant

In [include/constants/species.h](../../include/constants/species.h):

```c
#define SPECIES_ARCEUS     493
#define SPECIES_NEWMON     494

#define MAX_SPECIES        SPECIES_NEWMON
#define NATIONAL_DEX_COUNT SPECIES_NEWMON

#define SPECIES_EGG             495
#define SPECIES_BAD_EGG         496
#define SPECIES_DEOXYS_ATK      497
...
#define SPECIES_ROTOM_MOW       508
```

Add one to every value from `SPECIES_EGG` to `SPECIES_ROTOM_MOW`. `NUM_SPECIES` follows.

`MAX_SPECIES` and `NATIONAL_DEX_COUNT` bound the national Pokédex and the species range
checks in C (Hall of Fame, Pokéwalker, Pokéathlon, photos...), which now accept the new
species.

**Rebuild `evo.narc`.** Its size comes from `NUM_SPECIES`, but the build only watches
`evo.json`: run `touch files/poketool/personal/evo.json` (or build from a clean `build/`)
after changing this file, or the game keeps an archive one entry short.

## 2. Five checks in C

These compare with `SPECIES_ARCEUS` instead of `MAX_SPECIES`. Change each to
`MAX_SPECIES`:

| File | Function | Without the change |
|---|---|---|
| [src/pokedex.c](../../src/pokedex.c) | `DexSpeciesIsInvalid` | the Pokédex refuses the species: it is never seen or caught |
| [src/battle_record.c](../../src/battle_record.c) | `BattleRecordHeader_GetField` | Battle Videos show no Pokémon |
| [src/register_hall_of_fame.c](../../src/register_hall_of_fame.c) | `RegisterHallOfFame_GetMmodelBySpeciesFormGender` | the Hall of Fame shows a default model |
| [src/application/view_photo.c](../../src/application/view_photo.c) | `Photo_CountValidMons` | photos don't count it |

And Professor Oak's national Pokédex rating counts to a fixed number. In
`GetOakNationalDexRating` ([src/field_misc_util.c](../../src/field_misc_util.c)), change
`if (count <= 483)` to `if (count <= NATIONAL_DEX_COUNT - 10)`. 483 is 493 minus the 9
mythicals minus one; without the change Oak calls the Pokédex complete one Pokémon
before `Pokedex_NationalDexIsComplete` does.

## 3. Base stats, evolutions, moves

**Base stats** ([pokemon.md](pokemon.md#base-stats-types-abilities-items-tmhm)):
`files/poketool/personal/personal.json`, list `baseStats`, one entry per species **in
order**. Insert the new entry after `ARCEUS` and before `EGG`:

```json
    { "species": "ARCEUS", ... },
    { "species": "NEWMON", "hp": 35, "atk": 55, "def": 30, "speed": 90, "spatk": 50, "spdef": 40,
      "types": ["TYPE_ELECTRIC", "TYPE_ELECTRIC"], ... "tms": [...], "hms": [...] },
    { "species": "EGG", ... },
```

`species` is only a label; the position is what counts. Copying a whole entry from a
similar species and changing it is the easy way.

**Evolutions**: `files/poketool/personal/evo.json` is keyed by name, so add
`{ "baseSpecies": "SPECIES_NEWMON", "evos": [...] }` anywhere, and point other species'
evolutions at `SPECIES_NEWMON` as needed ([evolutions.md](evolutions.md)).

**Level-up moves**: add `"SPECIES_NEWMON": [ ... ]` to
`files/poketool/personal/level_up_learnsets.json`. Without it the species learns nothing.

**Egg moves**: `egg_moves.json` is full (the game searches only the first 2045 entries).
Give the new species egg moves only after making room
([pokemon.md](pokemon.md#egg-moves)).

**Tutor moves**: `files/fielddata/wazaoshie/waza_oshie.json`, list `tutor`, is in species
order without the two eggs. Insert `{"mon": "SPECIES_NEWMON", "moves": [...]}` right after
the `SPECIES_ARCEUS` entry (before `SPECIES_DEOXYS_ATK`). `GetMoveTutorLearnsetIndex` and
the size check in `GetMoveTutorLearnset` ([src/field/scrcmd_move_tutor.c](../../src/field/scrcmd_move_tutor.c))
follow the constants.

## 4. Egg species: pms.narc

`files/poketool/personal/pms.narc` is not an archive: it is a raw list of `u16`, the
species an egg hatches into for each species (`ReadFromPersonalPmsNarc` in
[src/pokemon.c](../../src/pokemon.c)). Insert one value at position 494:

```sh
python3 -c "
import struct; p = 'files/poketool/personal/pms.narc'; b = bytearray(open(p, 'rb').read())
b[494 * 2:494 * 2] = struct.pack('<H', 494)   # hatches into NEWMON itself
open(p, 'wb').write(b)"
```

For an evolved species, store its baby's number instead. Incense babies are in
`GetEggSpecies` ([src/pokemon.c](../../src/pokemon.c)).

## 5. Name and Pokédex text

Text banks are in `files/msgdata/msg/` ([pokemon.md](pokemon.md#pokédex-data)). Each
entry has an `id` that becomes a `#define` (the build writes `msg_0237.h`, which
`src/easy_chat.c` includes), so ids must stay unique.

**Name** (`msg_0237.json`) and **name with article** (`msg_0238.json`): one entry per
species, then Egg and Bad Egg. Insert at position 494, before `Egg`:

```json
{"id": "msg_0237_00494", "en_US": "NEWMON"},
{"id": "msg_0237_00495", "en_US": "Egg"},
{"id": "msg_0237_00496", "en_US": "Bad Egg"}
```

and `"a {COLOR 255}NEWMON{COLOR 0}"` in `msg_0238.json`. Renumber the ids after it, for
example:

```sh
python3 -c "
import json, sys
for bank in ('0237', '0238'):
    p = 'files/msgdata/msg/msg_%s.json' % bank; d = json.load(open(p, encoding='utf-8'))
    for i, m in enumerate(d['messages']): m['id'] = 'msg_%s_%05d' % (bank, i)
    open(p, 'w', encoding='utf-8').write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')"
```

**Pokédex text**: `msg_0803.json` to `msg_0828.json` have one entry per species and
nothing after. **Append** one entry to each of the 26:

| Banks | Content |
|---|---|
| `0803`, `0804` | Pokédex entry, HeartGold / SoulSilver (three lines, a list of strings) |
| `0805`-`0810` | entry in English, French, German, Italian, Spanish, Japanese (shown after trading for a foreign Pokémon) |
| `0811` | unused (`"garbage"` entries) |
| `0812`, `0813` | weight text (`0813` is used while Giratina is in its Altered Forme; same text) |
| `0814`, `0815` | height text, likewise |
| `0816` | category ("Mouse Pokémon") |
| `0817`-`0822` | name in English, French, German, Italian, Spanish, Japanese |
| `0823`-`0828` | category in the same six languages |

The weight and height strings are display only; the values are in step 6.

## 6. Pokédex

**Size data**: `files/application/zukanlist/zkn_data/zukan_data.json`, list `mon_stats`,
one entry per species with nothing after: **append**

```json
{"species": "SPECIES_NEWMON", "height": 4, "weight": 60, "body_style": 0,
 "scale_f": 272, "mon_scale_f": 524, "scale_m": 256, "mon_scale_m": 524,
 "ypos_f": 8, "mon_ypos_f": 27, "ypos_m": 9, "mon_ypos_m": 27}
```

`height` is in tenths of a metre and `weight` in tenths of a kilogram. `body_style` is the
index of its list in `body_style` below. The scale and y values place the sprite next to
the trainer in the size comparison; copy a Pokémon of similar size.

**Sorted lists**: `sorting` in the same file. Each group has lists of species, used by
the Pokédex's sort and search modes and by the GTS. Add `SPECIES_NEWMON` to:

| Group | List | Where |
|---|---|---|
| `dex_order` | `national` | at the end |
| `dex_order` | `johto` | only if it is in the Johto Pokédex (below) |
| `dex_order` | `alphabetical` | in alphabetical order |
| `dex_order` | `heaviest`, `lightest`, `tallest`, `shortest` | in order of weight / height, in both `altered` and `origin` |
| `letters` | the list of its first letter | in alphabetical order |
| `letter_groups` | `abc`, `def`, ... | in alphabetical order |
| `types` | each of its types | in national order |
| `body_style` | its body style | in national order |

A species missing from a list can't be found by that sort or search.

**Area data**: `files/application/zukanlist/zkn_data/zukan_enc.json`. Each of the eight
`method_N` objects has one key per species, then `mon_494_egg`. Insert a key before the
egg in all eight, and rename the egg's key (the build makes a constant from each name,
so names must be unique):

```json
"mon_493_arceus": [0],
"mon_494_newmon": [0],
"mon_495_egg": [0]
```

`[0]` means "found nowhere". The Pokédex area map reads these by position
(`NARC_zukan_enc_gEncounters_method_0_mon_000_none + species` in
[src/application/pokedex/pokedex_screen_setup.c](../../src/application/pokedex/pokedex_screen_setup.c)).
To show where it lives, copy the lists of a Pokémon found in the same places; a list
ends with 0, and `GOLD`/`SILVER` give separate lists per version.

**Area search masks**: `zukan_hw_data/zukan_hw_data_1_gold.bin` and `_silver.bin` (same
folder) are one byte per species, the regions the Pokédex search finds it in
(`speciesAreaMasks` in [src/application/pokedex/pokedex_search.c](../../src/application/pokedex/pokedex_search.c)).
Append one byte to each, for example a copy of Pikachu's:

```sh
for v in gold silver; do python3 -c "
import sys; p = sys.argv[1]; b = open(p, 'rb').read(); open(p, 'wb').write(b + b[25:26])" \
  files/application/zukanlist/zkn_data/zukan_hw_data/zukan_hw_data_1_$v.bin; done
```

**Johto number**: `files/poketool/johtozukan.narc` has one member, a `u16` per species:
its Johto Pokédex number, or 0. The Pokédex loops over every national number and reads
past the end without a new entry. Unpack it (see [step 0](#0-before-you-start)), append
two bytes to `00000.bin`, and pack it:

```sh
python3 -c "open('/tmp/narc/johtozukan.narc.d/00000.bin', 'ab').write(bytes(2))"   # 0: not in the Johto dex
```

### In the Johto Pokédex

Before the National Pokédex, the Pokédex, the summary and the PC show the **Johto**
number, and only species that have one appear. To make the new species Johto #257,
after Arceus' place in the list:

1. **The number**: write `257` instead of `0` as its entry in `johtozukan.narc`:

   ```sh
   python3 -c "open('/tmp/narc/johtozukan.narc.d/00000.bin', 'ab').write((257).to_bytes(2, 'little'))"
   ```

2. **The count**: `J_NUM_SPECIES` 256 → 257 in
   [include/constants/johto_dex.h](../../include/constants/johto_dex.h).
   `Pokedex_JohtoDexIsComplete` ([src/pokedex.c](../../src/pokedex.c)) needs this many,
   minus the Johto mythicals (`sJohtoMythicals`: Mew, Celebi).
3. **The list**: append `SPECIES_NEWMON` to the `johto` list in `dex_order` in
   `zukan_data.json`. The Johto Pokédex shows this list in this order, and the code
   assumes entry *n* is Johto number *n* + 1, so the order must match the numbers.
4. **Oak's rating**: in `GetOakJohtoDexRating`
   ([src/field_misc_util.c](../../src/field_misc_util.c)), `if (count <= 253)` →
   `if (count <= J_NUM_SPECIES - 3)`, and add `#include "constants/johto_dex.h"` at the top.
   As for the national rating, 253 is "one short of complete".

A number in the middle (say #20) works the same way, but every species from #20 on gets
a new number in `johtozukan.narc` and the `johto` list must be reordered to match. [pokedex.md](pokedex.md#changing-it)
has a script that regenerates `johtozukan.narc` from the list. The
save doesn't store Johto numbers, so changing them doesn't affect saves.

## 7. Battle sprites

**Pictures**: `files/poketool/pokegra/pokegra/0494/` with the same layout as the others:

```
0494/male/front.png    0494/male/back.png      160x80, 4-bit indexed (two frames side by side)
0494/female/front.png  0494/female/back.png
```

and a `.key` file next to each PNG. The build won't run without them; any species' keys
work (copy them with the PNGs). Start from a copy of a similar species' folder and draw
over it, keeping the size and 16-colour palette. For a species that looks the same for
both genders, the female files are copies of the male ones; for a genderless one they are
empty files, like `0081/female/`. The front picture's palette is the normal palette
and the back picture's is the shiny one ([pokemon.md](pokemon.md#graphics)).

Two places stop at Arceus; make them include the new folder:

- `files/poketool/pokegra/pokegra/meson.build`: `range(0, 493)` → `range(0, 495)`
  (one past the last folder);
- `tools/scripts/make_pokegra.py`: `range(0, 494)` → `range(0, 495)`.

**Sprite height** `files/poketool/pokegra/height.narc`: four members per species (the
vertical offset of each picture; `species * 4 + ...` in `GetMonPicHeightBySpeciesGenderForm`).
Append four: unpack, copy Pikachu's `00100.bin`-`00103.bin` to `01976.bin`-`01979.bin`,
pack.

**Battle animation, cry delay and shadow** `files/a/1/8/0`: one member holding 89 bytes
per species (`struct PokepicSpeciesAnimData` in [include/pokepic_anim.h](../../include/pokepic_anim.h)).
Append Pikachu's 89 bytes:

```sh
python3 -c "
p = '/tmp/narc/0.d/00000.bin'; b = open(p, 'rb').read(); open(p, 'wb').write(b + b[25 * 89:26 * 89])"
```

(after `cp files/a/1/8/0 /tmp/narc/0` and `$NARC -xf /tmp/narc/0`; pack it back to
`files/a/1/8/0`).

## 8. Icon and footprint

**Icon**: the icons are `files/poketool/icongra/poke_icon/poke_icon_NNNNNNNN.png`
(32×64, two frames), species N being file N + 7, then the eggs (501, 502) and forms
(503-550). Rather than renumber 50 files, put the new icon **at the end**, as
`poke_icon_00000551.png`, and add it to the list in that folder's `meson.build`.

Then in [src/pokemon_icon_idx.c](../../src/pokemon_icon_idx.c), in `GetMonIconNaixEx`,
before `if (species > MAX_SPECIES)`:

```c
    if (species > SPECIES_ARCEUS && species <= MAX_SPECIES) {
        return 551 + species - (SPECIES_ARCEUS + 1);
    }
```

Without it, species 494 gets file 501, the egg icon. The icon's palette (one of three)
comes from `sPokemonPalNoBySpeciesAndForm`, which has 544 entries; append one (0, 1 or
2, the palette whose colours suit the icon) and in `GetMonIconPaletteEx` add, after the
`species > MAX_SPECIES` branch:

```c
    } else if (species > SPECIES_ARCEUS) {
        species = 544 + species - (SPECIES_ARCEUS + 1);
```

A second species is then file 552 and palette entry 545 with no further C change.

**Footprint**: `files/poketool/pokefoot/pokefoot/pokefoot_NNNNNNNN.png`, species + 3
(`footprint_stamp.c`). Add `pokefoot_00000497.png` (32×16, copy one to keep the format)
and list it in that folder's `meson.build`.

## 9. Cry

A cry is a sound bank with the same number as the species: `PlayCry` plays the cry
sequence with bank `species` ([src/sound_playback.c](../../src/sound_playback.c)). Bank 494
is Shaymin's Sky Forme cry, and `IsShayminSkyCry` treats species number 494 as that
cry, so it has to move. Banks 495-699 are free.

1. In `sound/sound_data.json`, move the `BANK_PV516_SKY` entry from position 494 of
   `banks` to position 699 (replace the `null` there, put `null` at 494). Do the same for
   `WAVE_ARC_PV516_SKY` in `waveArchives`. Positions are ids
   ([music.md](music.md#whats-in-sound)).
2. Put the new cry at position 494 of both lists:

   ```json
   {"name": "BANK_PV_NEWMON", "file": "banks/BANK_PV_NEWMON.json", "waveArchives": ["WAVE_ARC_PV_NEWMON", null, null, null]}
   ```
   ```json
   {"name": "WAVE_ARC_PV_NEWMON", "file": "wave_archives/WAVE_ARC_PV_NEWMON.json"}
   ```

   with `sound/banks/BANK_PV_NEWMON.json`, one instrument as in the game's cry banks:

   ```json
   {"instruments": [{"program": 0, "type": "pcm", "archive": 0, "sample": 0, "key": 60, "release": 127}]}
   ```

   and `sound/wave_archives/WAVE_ARC_PV_NEWMON.json` naming your WAV:

   ```json
   {"waves": [{"file": "../cries/newmon.wav", "format": "pcm8"}]}
   ```

   Game cries are 8-bit PCM. To start from an existing cry,
   `python3 tools/sound/swar.py extract sound/wave_archives/WAVE_ARC_PV025.swar out/`
   gives Pikachu's as a WAV ([music.md](music.md#new-instruments)).
3. Regenerate the constants:
   `python3 tools/sound/sdat.py header sound/sound_data.json include/constants/sndseq.h`
   (the build stops if you forget).
4. In `src/sound_playback.c`, add `#include "constants/sndseq.h"` and change

   ```c
   #define CRY_BANK_SHAYMIN_SKY BANK_PV516_SKY
   #define CRY_BANK_MAX         MAX_SPECIES
   ```

A second species uses bank 495 the same way.

## 10. Following Pokémon

The Pokémon that walks behind the player needs an overworld model. Three tables in
[src/follow_mon.c](../../src/follow_mon.c) are in species order with nothing after and no
bounds check, so they **must** get an entry:

| Table | Entry for the new species |
|---|---|
| `sModelIndexLUT` (indexed by species) | the model to use, e.g. `FOLLOWER_MON_PIKACHU` |
| `sFormMaxLUT` (species - 1) | number of extra forms with their own model, `0` |
| `sFemaleFlagLUT` (species - 1) | `TRUE` to use the next model for females (Pikachu has one), else `FALSE` |

Reusing another species' model is all it takes. The model also sets whether it fits
under low ceilings (`tp_param`, read by `FollowMon_GetSizeParamBySpecies`).

### A follower model of its own

A follower model is found through three numbers that the code computes from one
**follower index** (`FOLLOWER_MON_*`, [include/constants/follow_mon_idx.h](../../include/constants/follow_mon_idx.h)):

| | Retail range | Computed as |
|---|---|---|
| follower index | `FOLLOWER_MON_BULBASAUR` 0 ... `FOLLOWER_MON_ARCEUS_DARK` 565 | `sModelIndexLUT[species]` |
| sprite id | `SPRITE_FOLLOWER_MON_BULBASAUR` 428 ... 993 | 428 + index (`FollowMon_GetSpriteID`) |
| texture (mmodel member) | `MMODEL_FOLLOWER_MON_BULBASAUR` 297 ... 862 | 297 + index (Hall of Fame, certificates) |
| movement parameters | `tp_param.csv` rows 0 ... 565 | row = index |

The next index is 566, and texture 863 is free, but sprite id 994 is taken
(`SPRITE_FOLLOWER_MON_STATIC_BUTTERFREE`). So the texture and the parameters go at the
end, and the sprite id needs a small code change.

1. **The texture.** Draw the eight 32×32 frames as one 256×32 sheet. Start from a
   similar Pokémon's:

   ```sh
   M=tools/mapkit/mapkit.sh
   $M sprite export SPRITE_FOLLOWER_MON_PIKACHU newmon_follow.png
   # ... draw over it: frames 1-2 walking up (back view), 3-4 down, 5-6 left, 7-8 right ...
   $M sprite add FOLLOWER_MON_NEWMON --like SPRITE_FOLLOWER_MON_PIKACHU --png newmon_follow.png
   ```

   `sprite add` ([overworld-sprites.md](overworld-sprites.md#adding-a-new-sprite)) copies
   Pikachu's texture as `mmodel_00000863.NSBTX`, imports your sheet into it, and adds
   `MMODEL_FOLLOWER_MON_NEWMON` (863), `SPRITE_FOLLOWER_MON_NEWMON` (1050) and its row in
   `gObjectEventGraphicsInfos` with Pikachu's drawing settings. `--png` sets the normal
   palette; the shiny one is still Pikachu's until you import it:
   `$M sprite import newmon_shiny.png SPRITE_FOLLOWER_MON_NEWMON --palette 1`.
   For a big Pokémon (eight 64×64 frames), use a big one as `--like`, such as
   `SPRITE_FOLLOWER_MON_STEELIX`.

   **Check that it got member 863** (it prints the number). The Hall of Fame and the
   certificates compute the texture as 297 + index; if you added other sprites before,
   the member is higher and they would show the wrong model. Adding the followers before
   any other sprite avoids that.
2. **The index**: `#define FOLLOWER_MON_NEWMON 566` at the end of `follow_mon_idx.h`,
   and `FOLLOWER_MON_NEWMON` as the new species' entry in `sModelIndexLUT`.
3. **The parameters**: a row at the end of
   `files/fielddata/tsurepoke/tp_param.csv`, for example a copy of Pikachu's:

   ```
   TSURE_POKE_NEWMON,0,false,false,false,0
   ```

   `too_tall` keeps it in its ball on maps that only allow short followers
   (`MAP_FOLLOWMODE_HEIGHT_RESTRICT`), `hover` is set for floating Pokémon such as Gastly and Haunter (what it changes was not checked). The first
   column is only a label: rows are read by position.
4. **The sprite id**: in `FollowMon_GetSpriteID` ([src/follow_mon.c](../../src/follow_mon.c)),
   send indexes past Arceus to the new sprite:

   ```c
   } else {
       int offset = SpeciesToOverworldModelIndexOffset(species);
       if (offset > FOLLOWER_MON_ARCEUS_DARK) {
           return SPRITE_FOLLOWER_MON_NEWMON + offset - (FOLLOWER_MON_ARCEUS_DARK + 1);
       }
       ret = SPRITE_FOLLOWER_MON_BULBASAUR + offset;
       ...
   ```
5. **The billboard**: `MapObject_GetBillboard` in
   [src/field/map_object_billboard_motion.c](../../src/field/map_object_billboard_motion.c)
   treats sprite ids 428-993 as followers, whose draw data is laid out differently. Add
   the new one:

   ```c
   if ((spriteId >= SPRITE_FOLLOWER_MON_BULBASAUR && spriteId <= SPRITE_FOLLOWER_MON_ARCEUS_DARK)
       || spriteId == SPRITE_FOLLOWER_MON_NEWMON) {
   ```

For more new followers, add them in the same order everywhere: indexes 566, 567...,
textures 863, 864..., sprite ids 1050, 1051... (what `sprite add` gives when nothing
else is added in between). Then step 4 needs no change, and step 5 becomes a range
`spriteId >= SPRITE_FOLLOWER_MON_NEWMON && spriteId <= SPRITE_FOLLOWER_MON_<LAST>`.
Female and form variants (the `sFemaleFlagLUT` / `sFormMaxLUT` entries) take the next
indexes after the base one, as in retail; that was not tried.

## 11. Pokéathlon

Pokéathlon stats are in `files/poketool/personal/performance.narc`, 20 bytes a member;
`sPokeathlonPerformanceArcIdxs` in [src/pokemon.c](../../src/pokemon.c) gives each species
its member (plus the form). Append a member: unpack, copy Pikachu's (member
`sPokeathlonPerformanceArcIdxs[25]` = 24, `00024.bin`) to `00554.bin`, pack. Then append
`554, // SPECIES_NEWMON` to the end of `sPokeathlonPerformanceArcIdxs`. That table has no
bounds check either.

## 12. Putting it in the game

With the steps above it is a full species; use `SPECIES_NEWMON` like any other:

- wild: the encounter JSON ([wild-encounters.md](wild-encounters.md));
- trainers: `trainers.json` ([trainers.md](trainers.md));
- a gift: `givemon(SPECIES_NEWMON, 5, 0, 0, 0, VAR_SPECIAL_RESULT)` in a script
  ([script-commands.md](script-commands.md));
- an evolution into it in `evo.json`.

Build with `make release` (`make` also runs the retail checksums, which now fail). Then
check in the game: its Pokédex page and area map, the battle sprite and cry, the party
and box icon, the summary, the Pokémon following you, and a Pokéathlon.

## What doesn't need changing

Checked in the code, so you can leave them:

- forms' sprites (`otherpoke.narc`) and form data: separate archives, reached by name;
- the easy chat word list: the new species isn't offered as a word unless you add it to
  the lists in `src/easy_chat_menu.c`;
- the PBR files in `files/pbr/` (only for linking with Battle Revolution).

Linking with other games (Pokéwalker, GTS, Pal Park, trades with retail games) was not
looked at. Their species checks now accept 494, and the other game won't know it.

## Not verified

The test species was built for HeartGold and SoulSilver, with all archives checked for
the expected number of members and the save layout unchanged; a second build added its
own follower model and Johto #257 (HeartGold). Nothing was played. In
particular:

- that the new Pokémon appears correctly in battle, the summary, the PC, the Pokédex
  (entry, area map, size comparison, search), the party menu, the Hall of Fame and
  following the player;
- that the cry plays and Shaymin Sky's still does;
- that eggs, Bad Eggs and the forms (Deoxys, Wormadam, Giratina, Shaymin, Rotom) still
  work after their numbers moved;
- the Johto Pokédex entry (built, with #257 in `johtozukan.narc`), and that Oak's ratings
  change at the right counts;
- the follower model of its own (built, with its texture at member 863 and its
  `tp_param` row), and how it looks and moves;
- more than one species, and female or form variants of a new follower.
