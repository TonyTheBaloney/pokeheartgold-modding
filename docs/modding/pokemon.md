<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21 -->

# Changing Pokémon data

> AI-generated; not affiliated with pret. See AI.md at the repository root.

Species are numbered by `SPECIES_*` in `include/constants/species.h`
(1–493, then `SPECIES_EGG` 494, `SPECIES_BAD_EGG` 495, then alternate forms from 496).
Most per-species files are arrays in that order. Don't reorder them.

## Base stats, types, abilities, items, TM/HM

File: `files/poketool/personal/personal.json`, array `baseStats`, one entry per species
(entry 0 is `NONE`).

```json
{
  "species": "BULBASAUR",
  "hp": 45, "atk": 49, "def": 49, "speed": 45, "spatk": 65, "spdef": 65,
  "types": ["TYPE_GRASS", "TYPE_POISON"],
  "catchRate": 45, "expYield": 64,
  "hp_yield": 0, "spatk_yield": 1, ...
  "items": ["ITEM_NONE", "ITEM_NONE"],
  "genderRatio": 0.125, "eggCycles": 20, "friendship": 70,
  "growthRate": "MEDIUM_SLOW",
  "eggGroups": ["EGG_GROUP_MONSTER", "EGG_GROUP_GRASS"],
  "abilities": [...], "greatMarshRate": 0, "color": 0, "flip": 0,
  "tms": [...], "hms": [...]
}
```

- `items`: wild held items (common, rare).
- `genderRatio`: fraction female (`0.0` all male, `1.0` all female); any value
  above 1 (the file uses `2.0`) means genderless. See `GENDER_RATIO` in
  `include/constants/pokemon.h`.
- `tms` / `hms`: lists of the machines the species can learn.
- Template: `personal.json.txt`; build rule: `files/poketool/personal/meson.build`.

## Evolutions

File: `files/poketool/personal/evo.json`, array `evoTable`:

```json
{ "baseSpecies": "SPECIES_BULBASAUR",
  "evos": [ { "method": "EVO_LEVEL", "param": 16, "target": "SPECIES_IVYSAUR" } ] }
```

Methods are the `EVO_*` constants in `include/constants/pokemon.h`. The
`param` meaning depends on the method (level, item, move, species, ...).

The baby/base species used for eggs is **not** here; it's the binary
`files/poketool/personal/pms.narc` (see "Not editable yet").

## Moves

| What | Where | Editable? |
|---|---|---|
| Level-up learnset | `files/poketool/personal/level_up_learnsets.json` | yes |
| Egg moves | `files/poketool/personal/egg_moves.json` | yes |
| TM/HM compatibility | `personal.json` `tms`/`hms` | yes |
| Move tutors | `files/fielddata/wazaoshie/waza_oshie.json` | yes |
| Move data itself (power, type, ...) | `files/poketool/waza/battle_moves.json`, see [moves.md](moves.md) | yes |

### Level-up learnsets

`files/poketool/personal/level_up_learnsets.json`, one list per species, like
pokeemerald's `LEVEL_UP_MOVE(level, move)` lines:

```json
"SPECIES_BULBASAUR": [
    { "level": 1, "move": "MOVE_TACKLE" },
    { "level": 3, "move": "MOVE_GROWL" },
    ...
]
```

- Keys are `SPECIES_*` constants (`include/constants/species.h`), including the
  alternate forms that have their own learnset (`SPECIES_DEOXYS_ATK`,
  `SPECIES_ROTOM_HEAT`, ...). A species left out learns nothing.
- Moves are `MOVE_*` constants (`include/constants/moves.h`); levels 1-100.
- **At most 21 moves** per species: the game reads a learnset into a 22-entry
  buffer (`MAX_LEARNED_MOVES`). The Move Relearner's buffer is a little smaller
  (`LEVEL_UP_LEARNSET_MAX`, 19 moves plus the end marker and padding); retail
  already goes past it for the species with 20+ moves.
- Keep levels in order: when a Pokémon levels up or is generated, the game stops
  at the first move above its level. (Retail Banette has one out of order.)
- Built into `wotbl.narc` by `tools/pokedata/pokedata.py`.

### Egg moves

`files/poketool/personal/egg_moves.json`, like pokeemerald's `egg_moves(...)`:

```json
"SPECIES_BULBASAUR": [
    "MOVE_LIGHT_SCREEN",
    "MOVE_SKULL_BASH",
    ...
]
```

- Key: the species that hatches (the baby). At most **16 moves** (`MAX_EGG_MOVES`).
- **The table is full.** The game only searches the first 2045 entries of the
  list for a species (`LoadEggMoves`, `src/get_egg.c`), and retail uses exactly
  that many (each species costs one entry plus one per move). To add moves,
  remove others first, or raise that limit in C (the build tells you which
  species fell off the end).
- Built into `kowaza_list.narc` by `tools/pokedata/pokedata.py`.

Both files are checked at build time (unknown names, too many moves, bad levels)
with an error that names the species. `python3 tools/pokedata/test_pokedata.py`
checks that the unmodified files build the retail archives.

## Pokédex data

- Height, weight, body style, sprite scale/offset for the dex, sort orders:
  `files/application/zukanlist/zkn_data/zukan_data.json`.
- Text, in `files/msgdata/msg/` (`en_US` strings, one entry per species):

| Bank | Content |
|---|---|
| `msg_0237.json` | species names |
| `msg_0238.json` | names with article |
| `msg_0816.json` | category ("Seed Pokémon") |
| `msg_0803.json` / `msg_0804.json` | dex entry, HeartGold / SoulSilver |
| `msg_0814.json` | height string |
| `msg_0812.json` | weight string |

The height/weight strings are display text only; the values the game uses are
in `zukan_data.json`. Change both.

- Johto dex order: `files/poketool/johtozukan.narc` (binary) and
  `include/constants/johto_dex.h`.

## Graphics

- Front/back sprites: `files/poketool/pokegra/pokegra/NNNN/{male,female}/{front,back}.png`
  (NNNN = species number). Keep the palette and dimensions of the original.
- Alternate forms: `files/poketool/pokegra/otherpoke/<name>/`, ordered by `otherpoke.txt`.
- Icons: `files/poketool/icongra/poke_icon/`. Which of the icon palettes a species uses
  is the C table `sPokemonPalNoBySpeciesAndForm` in `src/pokemon_icon_idx.c`.
- Footprints: `files/poketool/pokefoot/pokefoot/`.
- Overworld follower settings: `files/fielddata/tsurepoke/tp_param.csv`; follower
  model tables are in `src/follow_mon.c`.
- Sprite height offsets (`pokegra/height*.narc`) and animation data (`files/a/0/9/0`,
  `files/a/1/8/0`) are binary.

## Not editable yet (binary)

`pms.narc`
(base species for eggs), `performance.narc` (Pokéathlon stats),
`johtozukan.narc`, `height*.narc`, cries in the sound archive (`sound/`, see [music.md](music.md)).

## Species facts hard-coded in C

Changing these behaviors means editing C:

- Baby species for eggs with incense etc.: `GetEggSpecies` in `src/pokemon.c`
- Mythical lists: `sMythicalMonsList` (`src/pokemon.c`), `sNationalMythicals` /
  `sJohtoMythicals` (`src/pokedex.c`)
- Form sprite selection and Pokéathlon index table: `src/pokemon.c`
- Move tutor learnset index: `GetMoveTutorLearnsetIndex` in `src/field/scrcmd_move_tutor.c`

## Adding a new species

Not supported yet. A new species has to go after Arceus (493), which shifts
`SPECIES_EGG`, `SPECIES_BAD_EGG` and every form number. That breaks every
archive indexed by species, plus:

- `NUM_DEX_FLAG_WORDS` in `include/pokedex.h` (changes the **save layout**)
- species ranges hard-coded in `files/poketool/pokegra/pokegra/meson.build`,
  `tools/scripts/make_pokegra.py`, `poke_icon/meson.build`, `evo.json.txt`
- `MAX_SPECIES`/`NATIONAL_DEX_COUNT` checks in about 15 C files (`follow_mon.c`,
  `pokedex.c`, `pokemon_icon_idx.c`, Pokéwalker, footprints, Hall of Fame, ...)
- every text bank above, the easy-chat word list (`src/easy_chat_menu.c`), and a cry

Replacing an existing species (same number, new data) works today, except for the
binary items listed above.
