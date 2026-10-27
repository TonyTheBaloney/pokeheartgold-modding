<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# Items

> AI-generated; not affiliated with pret. See AI.md at the repository root.

Every item is one entry in **`data/items/items.json`**: name, description, price,
pocket, what it does, its icon. The build turns that file into everything the game
reads. Icons are PNG files in `files/itemtool/itemdata/item_icon/`.

| pokeemerald | here |
|---|---|
| `src/data/items.h` (one `[ITEM_X] = { .name, .price, ... }` per item) | `data/items/items.json` (one `"ITEM_X": { "name", "price", ... }` per item) |
| `src/data/text/item_descriptions.h` | `"description"` in the same entry |
| `src/data/item_icon_table.h` | `"icon"`, `"palette"` in the same entry |
| `graphics/items/icons/*.png`, `graphics/items/icon_palettes/*.gbapal` | `files/itemtool/itemdata/item_icon/item_icon_NNN.png` and `.pal` |
| `include/constants/items.h` (`#define ITEM_X n`, `ITEMS_COUNT`) | the same file |
| `src/data/pokemon/item_effects.h` | `"partyUseParam"` in the entry |
| mart scripts (`pokemart` lists) | `src/scrcmd_mart.c` tables |

## Changing an item

Edit its entry and build (`make release`). For example, to make Potions cheaper and
stronger:

```json
"ITEM_POTION": {
    "name": "Potion",
    "description": "A spray-type medicine for wounds.\nIt restores the HP of one Pokémon by\njust 30 points.",
    "price": 200,
    ...
    "partyUseParam": {"hp_restore": true, "hp_restore_param": 30},
    ...
}
```

Check your edits without building:

```sh
python3 tools/pokedata/items.py check data/items/items.json --include include
```

It reports every mistake with the item and key (unknown constants, values out of
range, missing entries, items out of order) and warns about names longer than 12
characters.

## The fields

Keys are the names of the C struct fields (`ItemData` and `ItemPartyParam` in
`include/item.h`), so code and data read the same.

| Key | Meaning |
|---|---|
| `name` | shown everywhere. The longest retail name is 12 characters ("Ylw Apricorn" was shortened to fit); longer names may be cut off |
| `description` | the bag's text; `\n` breaks a line (3 lines of about 40 characters fit) |
| `price` | buying price, 0-65535; shops buy it back for half |
| `holdEffect`, `holdEffectParam` | what the item does when a Pokémon holds it: a `HOLD_EFFECT_*` constant (`include/constants/items.h`) and its number (a percentage, a type boost, a stat...). The effects are coded in the battle engine; search `src/battle` for the constant |
| `fieldPocket` | bag pocket: `POCKET_ITEMS`, `POCKET_MEDICINE`, `POCKET_BALLS`, `POCKET_TMHMS`, `POCKET_BERRIES`, `POCKET_MAIL`, `POCKET_BATTLE_ITEMS`, `POCKET_KEY_ITEMS` |
| `battlePocket` | battle bag pages it appears on, a list of `BTLPOCKET_BALLS_F`, `BTLPOCKET_BATTLE_ITEMS_F`, `BTLPOCKET_HP_RESTORE_F`, `BTLPOCKET_STATUS_RESTORE_F`, `BTLPOCKET_PP_RESTORE_F`; `[]` to keep it out of battle |
| `fieldUseFunc` | what "Use" in the bag does (table below) |
| `battleUseFunc` | `ITEM_BATTLE_USE_NONE`, `_BALL`, `_RESTORE`, `_ESCAPE`. Only `_ESCAPE` is read (on the battle-items page). What an item does in battle is decided by its `battlePocket` page ([party-menu-and-item-use.md §4](party-menu-and-item-use.md#4-using-an-item-in-battle)); keep the retail value |
| `prevent_toss` | can't be tossed or given to hold (key items) |
| `selectable` | can be registered to the Y button |
| `pluckEffect`, `flingEffect`, `flingPower` | what Pluck/Bug Bite do when they eat it, what Fling does with it, and Fling's power. The effect numbers are berry and item effects coded in battle |
| `naturalGiftPower`, `naturalGiftType` | for berries: Natural Gift's power and type. Left out for other items |
| `partyUse`, `partyUseParam` | effects of using it on a Pokémon (below) |
| `partyUseIndex` | only for items without party use: a number the original data keeps in the same bytes, the item's position in its category (balls 0-23 from the Master Ball, mail 0-11 from the Grass Mail, rods 0-2). No code found reads it; keep it as it is |
| `icon`, `palette` | the icon's PNG and palette file names in `files/itemtool/itemdata/item_icon/` (without extension) |
| `gen3` | the item's Gen 3 id (`AGB_ITEM_*`), used to convert items of Pokémon brought over from Gen 3. `AGB_ITEM_NONE` for new items |
| `noData` | only for the unused item ids (and the Explorer Kit): the item shares `ITEM_NONE`'s data and can't set any of the keys above |

Keys left out take their defaults: `false`, `0`, `[]`, `HOLD_EFFECT_NONE`,
`POCKET_ITEMS`, no Natural Gift.

### Field use

| `fieldUseFunc` | Used by |
|---|---|
| `ITEM_FIELD_USE_NONE` | no "Use" in the bag |
| `ITEM_FIELD_USE_HEALING` | medicine, vitamins, Rare Candy: pick a Pokémon, then `partyUseParam` applies |
| `ITEM_FIELD_USE_GENERIC` | Repels, flutes, cases (`ItemFieldUseFunc_Generic` decides by item) |
| `ITEM_FIELD_USE_TMHM` | TMs and HMs |
| `ITEM_FIELD_USE_EVO_STONE` | evolution stones |
| `ITEM_FIELD_USE_BERRY` | berries: used like medicine (`ItemMenuUseFunc_Berry` calls the healing handler); they can't be planted in the field, only in the [Berry Pots](berry-pots.md) |
| `ITEM_FIELD_USE_MAIL` | mail |
| `ITEM_FIELD_USE_ESCAPE_ROPE`, `_BICYCLE`, `_OLD_ROD` / `_GOOD_ROD` / `_SUPER_ROD`, `_HONEY`, `_PAL_PAD`, `_APRICORN_BOX`, `_BERRY_POTS`, `_UNOWN_REPORT`, `_DOWSING_MCHN`, `_GB_SOUNDS`, `_GRACIDEA`, `_VS_RECORDER` | those items |
| `_TOWN_MAP`, `_JOURNAL`, `_POFFIN_CASE`, `_POKE_RADAR`, `_SPRAYDUCK`, `_VS_SEEKER`, `_AZURE_FLUTE` | Sinnoh leftovers: "can't use this now" |

The list is `include/constants/items.h`; what each does is the matching row of
`sItemFieldUseFuncs` in `src/field_use_item.c`. A new kind of use needs a new
constant, a row there and its functions in C.

### Party use

With `"partyUse": true`, using the item on a Pokémon (from the bag, or in battle
from a restore or battle-items page) applies the `partyUseParam` effects. The field and
battle apply them with different code, and the battle skips EVs, Rare Candy, evolution
and PP Up ([party-menu-and-item-use.md](party-menu-and-item-use.md#3-using-an-item-on-a-pokémon-field)):

| Keys | Effect |
|---|---|
| `slp_heal`, `psn_heal`, `brn_heal`, `frz_heal`, `prz_heal`, `cfs_heal`, `inf_heal` | cure sleep, poison, burn, freeze, paralysis, confusion, infatuation |
| `hp_restore` + `hp_restore_param` | restore HP: a number of points, or 255 all (`HP_RESTORE_ALL`), 254 half, 253 a quarter |
| `pp_restore` / `pp_restore_all` + `pp_restore_param` | restore PP of one move / all moves: a number, or 127 to refill (`PP_RESTORE_ALL`) |
| `pp_up`, `pp_max` | PP Up, PP Max |
| `revive`, `revive_all` | revive (with `hp_restore_param` for how much) |
| `level_up`, `evolve` | Rare Candy; evolve |
| `atk_stages` ... `accuracy_stages` (0-15), `critrate_stages` (0-3), `guard_spec` | X items, Dire Hit, Guard Spec. (in battle) |
| `hp_ev_up` ... `spdef_ev_up` + `*_ev_up_param` | vitamins and EV berries: change EVs by the parameter (negative lowers) |
| `friendship_mod_lo` / `_med` / `_hi` + `*_param` | change friendship by the parameter, depending on how high it is |

Without party use these bytes hold one number instead (`ItemData` has them as a
`union`, and `GetItemAttr` then returns that byte for any party attribute):
`partyUseIndex` above. `partyUseParam` needs `"partyUse": true`.

## Adding an item

1. **Give it an id.** In `include/constants/items.h`, after the last item:

   ```c
   #define ITEM_ENIGMA_STONE 536
   #define ITEM_TEST_GEM     537
   ```
   and raise `ITEMS_COUNT` by one (`#define ITEMS_COUNT 538`).
2. **Describe it.** Add its entry to the end of `data/items/items.json` (copying
   a similar item is easiest):

   ```json
   "ITEM_TEST_GEM": {
       "name": "Test Gem",
       "description": "A gem that powers up\nNormal-type moves.",
       "price": 1000,
       "holdEffect": "HOLD_EFFECT_STRENGTHEN_NORMAL",
       "holdEffectParam": 20,
       "fieldPocket": "POCKET_ITEMS",
       "battlePocket": [],
       "fieldUseFunc": "ITEM_FIELD_USE_NONE",
       "battleUseFunc": "ITEM_BATTLE_USE_NONE",
       "flingPower": 10,
       "icon": "item_icon_324",
       "palette": "item_icon_325",
       "gen3": "AGB_ITEM_NONE"
   }
   ```
3. **Check and build**: `items.py check` (it says if the id and the entry don't
   match), then `make release`.
4. **Hand it out**: `giveitem(ITEM_TEST_GEM, 1, VAR_SPECIAL_RESULT)` in a script, a hidden item, or a
   mart (below).

Items must be listed in id order, one entry per id. The game numbers item data,
names and descriptions by id, so the build generates all of them from this order.

Things to know:

- **Item id ranges are code.** Balls (Master to Cherish, Fast to Sport), TMs and HMs
  (`ITEM_TM01`-`ITEM_HM08`, moves in `sTMHMMoves`, `src/item.c`), mail
  (`FIRST_MAIL_IDX`-`LAST_MAIL_IDX`) and berries (from `FIRST_BERRY_IDX`, 64 of
  them) are recognised by their ids. A new ball, TM, mail or berry needs those
  ranges and tables changed too; a new item of another kind doesn't.
- **Bag space.** Each pocket holds a fixed number of different items (`NUM_BAG_ITEMS`
  165, `NUM_BAG_MEDICINE` 40, `NUM_BAG_BALLS` 24, `NUM_BAG_TMS_HMS` 101,
  `NUM_BAG_BERRIES` 64, `NUM_BAG_MAIL` 12, `NUM_BAG_BATTLE_ITEMS` 30,
  `NUM_BAG_KEY_ITEMS` 50, `include/constants/items.h`). These sizes are part of
  the save file ([save-data.md](save-data.md)). The retail game already defines more
  items than some pockets hold (many can't be obtained), so the limit is on what a
  player can carry at once.
- **Saves.** Bags and held items store item ids, so renumbering existing items breaks
  saves; adding new ids at the end doesn't.
- **Not tested in game.** A new item builds into the ROM (tested); the game hasn't
  been run with one.

## Icons

Each item names an icon and a palette: `files/itemtool/itemdata/item_icon/item_icon_NNN.png`
(32 × 32, 16 colors, indexed) and `item_icon_NNN.pal` (JASC palette). Several items
share palettes (all the Poké Ball icons use a few). The PNGs store their palette
too, so they look right in any image editor; the game takes the colors from the
`.pal` file named in `items.json`.

- **Change an icon**: edit its PNG, keeping it indexed with 16 colors (in GIMP:
  Image → Mode → Indexed, then export). Only the color indexes matter; to change
  colors, edit the `.pal` (or point the item to another palette).
- **New icon**: add `item_icon_NNN.png` (and a `.pal` if it needs new colors) with a
  number not in use, add the file names to `files/itemtool/itemdata/item_icon/meson.build`,
  and name them in the item's entry.
- The build converts them (nitrogfx) to the NCGR/NCLR files the game reads; the
  unmodified PNGs give the original files byte for byte.

## Marts

Shop stock is in `src/scrcmd_mart.c`:

- **Regular Poké Mart clerks** (`callstd(std_pokemart)`) sell `sBadgeMartItems`:
  each item with the badge tier from which it's sold (tier 1 with no badges, up to 6
  with 8 or more).
- **Second clerks and department stores** (`setvar(VAR_SPECIAL_x8004, N)` then
  `callstd(std_special_mart)`) sell the list `sSpecialMartItems[N]`: 0 Cherrygrove,
  1 Violet, ..., in the order of that table. Add an item to a list, or add a list
  (and use its index in the clerk's script).

## Under the hood

`tools/pokedata/items.py build` (run by `data/items/meson.build`) writes:

| File | Becomes | Read by |
|---|---|---|
| `item_data.csv` | `itemtool/itemdata/item_data.narc` (csv2bin, `item_data.txt` gives the layout) | `GetItemAttr` |
| `msg_0222.json` | item names | `GetItemNameIntoString` and the bag, marts, Pokéwalker |
| `msg_0221.json` | item descriptions | `GetItemDescIntoString` |
| `item_narc_ids.h` | `sItemNarcIds` in `src/item.c`: data record, icon, palette, Gen 3 id per item | `GetItemIndexMapping`, `LoadItemDataOrGfx` |

Unchanged `items.json` gives the retail files byte for byte; both ROMs pass the
checksum tests. Tests: `python3 tools/pokedata/test_items.py`.

## Not covered yet

- New hold effects, field uses or battle uses are C:
  [party-menu-and-item-use.md](party-menu-and-item-use.md) explains where each kind of
  effect runs and how to add one.
- Berry trees, Apricorns and the Pokéathlon shops (other data).
- Marts as data files (they're C tables).
