<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-27 -->

# TMs, HMs and field moves

> AI-generated; not affiliated with pret. See AI.md at the repository root.

How TMs and HMs work, and how to change them: which move a machine teaches, adding
TMs after HM08, reusable TMs, HMs that can be forgotten or removed, and adding a new
field move. Everything here is C, plus `items.json`, `personal.json` and one script
file.

Other guides cover the parts around this one:

- What each HM checks when you use it (party menu, the A prompt, while moving), and
  HMs without a Pokémon that knows the move: [player-movement.md](player-movement.md#6-field-moves-hms).
- Which badge each HM needs: [gyms.md](gyms.md#what-badges-do).
- Which species can learn a machine (`tms` / `hms` in `personal.json`):
  [pokemon.md](pokemon.md).
- The party menu itself and its field-move entries:
  [party-menu-and-item-use.md](party-menu-and-item-use.md#2-the-party-menu).

| pokeemerald | here |
|---|---|
| `ITEM_TM01`...`ITEM_HM08` in one block | the same: ids 328-427 (`include/constants/items.h:681`) |
| `gTMHMMoves` / `ItemIdToBattleMoveId` | `sTMHMMoves` / `TMHMGetMove` (`src/item.c:31`, `:398`) |
| `IsHMMove2` | `MoveIsHM` (`src/item.c:407`) |
| `CanMonLearnTMHM` | `GetMonTMHMCompat` → `GetTMHMCompatBySpeciesAndForm` (`src/pokemon.c:3783`) |
| TM/HM learnsets in `tmhm_learnsets.h` | `tms` / `hms` lists in `files/poketool/personal/personal.json` |
| `sFieldMoveCursorCallbacks` | `sFieldMoveFuncTable` (`src/field_move.c:72`) |

## 1. How TMs and HMs work

### Item ids and the TM/HM index

The 100 machines are items 328-427, in one block:

| Items | Ids | TM/HM index |
|---|---|---|
| `ITEM_TM01`-`ITEM_TM92` | 328-419 | 0-91 |
| `ITEM_HM01`-`ITEM_HM08` | 420-427 | 92-99 |

`ITEM_EXPLORER_KIT` (428) follows at once, so the block can't grow in place. Most
code works with the **TM/HM index** (`item - ITEM_TM01`):

| Function | Where | Does |
|---|---|---|
| `TMHMGetMove(item)` | `src/item.c:398` | the move: `sTMHMMoves[item - ITEM_TM01]`; `MOVE_NONE` outside the block |
| `ItemToTMHMId(item)` | `src/item.c:419` | the index; **0 (TM01) outside the block** |
| `MoveIsHM(move)` | `src/item.c:407` | is `move` one of the last 8 entries of `sTMHMMoves` |
| `ItemIsTMOrHM(item)` | `src/field_misc_util.c:74` | is `item` in the block (script command `ItemIsTMOrHM`) |
| `GetTMHMCompatBySpeciesAndForm(species, form, index)` | `src/pokemon.c:3783` | can the species learn it |

The moves come from `sTMHMMoves` (`src/item.c:31`), one entry per index:

```c
static const u16 sTMHMMoves[] = {
    MOVE_FOCUS_PUNCH,  // TM01
    ...
    MOVE_TRICK_ROOM,   // TM92
    MOVE_CUT,          // HM01
    ...
    MOVE_WHIRLPOOL,    // HM05
    MOVE_ROCK_SMASH,   // HM06
    MOVE_WATERFALL,    // HM07
    MOVE_ROCK_CLIMB,   // HM08
};
```

`items.h` also has aliases by move (`TM_FOCUS_PUNCH`, `HM_CUT`...). HM05's was
Diamond/Pearl's `HM_DEFOG`; it is now `HM_WHIRLPOOL`.

### Who can learn what

Each species' personal record ends with four 32-bit words, `tmhm_1`-`tmhm_4`
(`include/struct_defs/personal_narc_structs.h:35`): bit *n* is TM/HM index *n*.
`personal.json` lists machine numbers instead (`"tms": [1, 6, ...]`, `"hms": [1, 4]`),
and the template `personal.json.txt` (line 49) packs them:

| Word | Bits | Holds |
|---|---|---|
| `tmhm_1` | 0-31 | TM01-TM32 |
| `tmhm_2` | 0-31 | TM33-TM64 |
| `tmhm_3` | 0-27, 28-31 | TM65-TM92, HM01-HM04 |
| `tmhm_4` | 0-3, **4-31 free** | HM05-HM08, then nothing |

So 28 more machines fit without changing the record (indexes 100-127). Forms have
records of their own ([forms.md](forms.md)), with their own lists.

Egg moves read the same bits: a father's move that is a TM or HM the baby could learn
is passed down (`src/get_egg.c:427`).

### Using a TM or HM

1. **Bag**: the TM pocket always goes to `BagApp_UseTMHM` (`src/application/bag/bag_app.c:1742`):
   "Booted up a TM." or "Booted up an HM." (chosen by `MoveIsHM`), "It contained X.
   Teach X to a Pokémon?"
2. **Party menu** (`PARTY_MENU_CONTEXT_TM_HM`): each Pokémon shows ABLE / UNABLE /
   LEARNED from `PartyMenu_CheckCanLearnTMHMMove` (`src/party_menu_items.c:755`), which
   reads the compatibility bit for `ItemToTMHMId(item)`.
3. With 4 moves, the summary screen opens to pick one to forget
   ([section 5](#5-hms-forgetting-them-and-removing-them)).
4. `PartyMenu_LearnMoveToSlot` (`src/party_menu_items.c:899`) writes the move, and
   **takes the item unless the move is an HM**:

   ```c
   if (partyMenu->args->itemId != ITEM_NONE) {
       if (!MoveIsHM(partyMenu->args->moveId)) {
           Bag_TakeItem(partyMenu->args->bag, partyMenu->args->itemId, 1, HEAP_ID_PARTY_MENU);
       }
       MonApplyFriendshipMod(mon, FRIENDSHIP_EVENT_LEARN_TMHM, PartyMenu_GetCurrentMapSec(partyMenu));
       ApplyMonMoodModifier(mon, MON_MOOD_MODIFIER_LEARN_TMHM);
   }
   ```

   So "is this an HM" is decided by the **move**, not the item.

### What `MoveIsHM` controls

| Where | Effect |
|---|---|
| `PartyMenu_LearnMoveToSlot` | an HM isn't used up |
| `BagApp_UseTMHM` | "Booted up an HM" instead of "a TM" |
| summary screen, forget-a-move page (`src/pokemon_summary.c:940`, `:972`) | "HM moves can’t be forgotten now." (`msg_0006`) while a new move is being learned (TM, level-up, evolution, the Move Relearner, the Headbutt tutor) |
| battle level-up (`BattlePartyMenu_IsSelectedMoveHM`, `src/battle/battle_party_menu.c:1755`) | the same, in battle |

The Move Deleter opens the summary screen with no move to learn, so it can delete
HMs ([move-tutors.md](move-tutors.md#5-the-move-deleter)).

### In the bag

| Where | What |
|---|---|
| `BagApp_SetItemNameStringsFromCurPocket` (`bag_app.c:773`) | the TM pocket lists **move names**, not item names |
| `BagApp_PrintTMorHMNumberOnWindow` (`bag_app.c:3420`) | below `ITEM_HM01`: "No." and 2 digits; otherwise the HM icon and the HM number |
| `bag_app_display.c:433` | the quantity is shown only for `ITEM_TM01`-`ITEM_TM92` |
| `BagApp_PrintTMHMDetails`, `BagApp_DrawTMHMMoveDetails` | PP, power, accuracy, type and category of `TMHMGetMove(item)` |
| `bag_app.c:1542` | nothing in the TM pocket can be tossed |
| `bag_app.c:2495` | items with `prevent_toss` or price 0 can't be sold: every HM has both |
| `SortPocket` (`src/bag.c:294`) | the pocket is kept sorted by item id |

The pocket has 101 slots (`NUM_BAG_TMS_HMS`), one more than the 100 machines, and
holds at most 99 of each (`BAG_TMHM_QUANTITY_MAX`).

**Item balls and hidden items** check `ItemIsTMOrHM` and then say "found TM24
Thunderbolt!" (`scr_seq_0141.s:1818`, `scr_seq_0145.s:539`).

**Item data**: in `data/items/items.json`, TMs and HMs use `"fieldPocket":
"POCKET_TMHMS"` and `"fieldUseFunc": "ITEM_FIELD_USE_TMHM"`. Their description is the
move's. The icon is `item_icon_397` (TM) or `item_icon_414` (HM), and the palette
gives the type colour:

| Type | Palette | Type | Palette | Type | Palette |
|---|---|---|---|---|---|
| Normal | `item_icon_402` | Fighting | `item_icon_398` | Flying | `item_icon_413` |
| Poison | `item_icon_403` | Ground | `item_icon_410` | Rock | `item_icon_412` |
| Bug | `item_icon_610` | Ghost | `item_icon_411` | Steel | `item_icon_408` |
| Fire | `item_icon_406` | Water | `item_icon_400` | Grass | `item_icon_405` |
| Electric | `item_icon_409` | Psychic | `item_icon_401` | Ice | `item_icon_404` |
| Dragon | `item_icon_399` | Dark | `item_icon_407` | | |

## 2. Changing what a TM teaches

Example: TM03 teaches Drain Punch instead of Water Pulse.

1. `src/item.c`, `sTMHMMoves`: `MOVE_DRAIN_PUNCH,  // TM03`.
2. `data/items/items.json`, `ITEM_TM03`: the `description` (the move's text) and the
   `palette` for its type (`item_icon_398`, Fighting). The name stays "TM03".
3. `personal.json`: the `tms` lists still say who could learn Water Pulse. Add 3 to
   the species that should learn Drain Punch, and remove it from the rest.

Everything that names the TM by item keeps working: marts (`src/scrcmd_mart.c`),
item balls and scripts that give `ITEM_TM03`. Script text that names the old move
does not change by itself; `grep -rn "ITEM_TM03" data/maps` finds the scripts that
give it.

Old saves keep the item and get the new move.

## 3. Adding TMs after HM08

Ids 428 and up are taken, so new TMs go after the last item, and the code that
checks the TM block must also know the second block. This recipe adds TM93 Drain
Punch, TM94 Aura Sphere and TM95 Earth Power (ids 537-539) and gives them TM/HM
indexes 100-102. It was built; see [section 7](#7-testing-the-recipes).

**1. Ids** (`include/constants/items.h`). After `ITEM_ENIGMA_STONE`:

```c
#define ITEM_ENIGMA_STONE 536
#define ITEM_TM93         537
#define ITEM_TM94         538
#define ITEM_TM95         539
#define ITEMS_COUNT       540
```

and

```c
#define NUM_TMS   95
#define NUM_HMS   8
#define NUM_TMHMS 103
```

**2. Item data** (`data/items/items.json`). Add the three entries at the end, copied
from `ITEM_TM01`, with `"name": "TM93"`, the move's description, a price, the type's
palette and `"gen3": "AGB_ITEM_NONE"`. Run `python3 tools/pokedata/items.py check
data/items/items.json --include include`.

**3. Moves and indexes** (`src/item.c`). Add the moves after HM08:

```c
    MOVE_ROCK_CLIMB,   // HM08
    MOVE_DRAIN_PUNCH,  // TM93
    MOVE_AURA_SPHERE,  // TM94
    MOVE_EARTH_POWER,  // TM95
};
```

and teach the functions the second block. `TMHMIdToItem` is new; declare it in
`include/item.h` after `ItemToTMHMId`:

```c
u16 TMHMGetMove(u16 itemId) {
    if ((itemId < ITEM_TM01 || itemId > ITEM_HM08) && (itemId < ITEM_TM93 || itemId > ITEM_TM95)) {
        return MOVE_NONE;
    }

    return sTMHMMoves[ItemToTMHMId(itemId)];
}

u8 ItemToTMHMId(u16 itemId) {
    if (itemId >= ITEM_TM93 && itemId <= ITEM_TM95) {
        return itemId - ITEM_TM93 + (ITEM_HM08 - ITEM_TM01 + 1);
    }
    if (itemId < ITEM_TM01 || itemId > ITEM_HM08) {
        return 0;
    }

    return itemId - ITEM_TM01;
}

u16 TMHMIdToItem(u8 tmhm) {
    if (tmhm > ITEM_HM08 - ITEM_TM01) {
        return tmhm - (ITEM_HM08 - ITEM_TM01 + 1) + ITEM_TM93;
    }

    return tmhm + ITEM_TM01;
}
```

`MoveIsHM` needs no change.

**4. The other range checks.**

- `ItemIsTMOrHM` (`src/field_misc_util.c:74`), for the item-ball text:

  ```c
  if (item >= ITEM_TM93 && item <= ITEM_TM95) {
      return TRUE;
  }
  ```
- Egg moves (`src/get_egg.c:427`): `TMHMGetMove(j + ITEM_TM01)` becomes
  `TMHMGetMove(TMHMIdToItem(j))`.
- Bag quantity (`src/application/bag/bag_app_display.c:433`): show it for everything
  but HMs:

  ```c
  if (pocket->slots[index].id < ITEM_HM01 || pocket->slots[index].id > ITEM_HM08) {
  ```
- Bag number (`BagApp_PrintTMorHMNumberOnWindow`, `bag_app.c:3420`):

  ```c
  if (itemId < ITEM_HM01 || itemId >= ITEM_TM93) {
      u16 number = itemId < ITEM_HM01 ? itemId - ITEM_TM01 + 1 : itemId - ITEM_TM93 + 93;
  ```

  The number is printed with 2 digits, so TM100 and up also need 3 digits there and
  room for them.

**5. Compatibility** (`files/poketool/personal/personal.json.txt`, line 49). Add
TM93-TM120 to bits 4-31 of the last word:

```
{{ setVarInt("tms", 0) }}{% for i in range(4) %}{% if add(i, 5) in mon.hms %}{{ setBit("tms", i) }}{% endif %}{%endfor %}{% for i in range(28) %}{% if add(i, 93) in mon.tms %}{{ setBit("tms", add(i, 4)) }}{% endif %}{%endfor %}{{ getVarHex("tms") }},
```

Then add `93`, `94`, `95` to the `tms` lists in `personal.json`. More than 28 new
machines needs a fifth word in `BaseStats`, a `BASE_TMHM_5` case in
`GetMonBaseStat_HandleAlternateForm` and `GetTMHMCompatBySpeciesAndForm`, and the
template.

**6. Bag space.** The pocket has 101 slots, so a player can hold only one new TM
before it is full. For three, raise `NUM_BAG_TMS_HMS` to 103 and the bag screen's
copy of it, `gPocketCapacities` in `asm/bag_app_data.s:235` (the 4th byte, `0x65`
→ `0x67`; it is a byte, so at most 255). **This changes the save layout**: 4 bytes
per slot in `SAVE_BAG`, so old saves stop loading
([save-compatibility.md](save-compatibility.md)).

**7. Hand them out**: marts (`src/scrcmd_mart.c`) or `giveitem(ITEM_TM93, 1,
VAR_SPECIAL_RESULT)` in a script.

What you get: the TMs sort by id, so they come **after** the HMs in the bag. To list
them before, give `SortPocket` (`src/bag.c:294`) a key that puts HM ids last, and
use it only for the TM pocket (berries share the function).

## 4. Reusable TMs

Remove the `Bag_TakeItem` call in `PartyMenu_LearnMoveToSlot`
(`src/party_menu_items.c:899`):

```c
    if (partyMenu->args->itemId != ITEM_NONE) {
        MonApplyFriendshipMod(mon, FRIENDSHIP_EVENT_LEARN_TMHM, PartyMenu_GetCurrentMapSec(partyMenu));
        ApplyMonMoodModifier(mon, MON_MOOD_MODIFIER_LEARN_TMHM);
    }
```

That is the only place a TM is used up. Optional changes that go with it:

- **Hide "×1"**: delete the `PrintItemQuantityOnWindow` call for the TM pocket in
  `bag_app_display.c:433`, as for HMs.
- **No selling**: set `"prevent_toss": true` on the TMs in `items.json` (the sell
  check is `bag_app.c:2495`).
- **No buying twice**: marts don't know you own one. Take TMs out of mart lists after
  the player has them, or sell them from a script that checks `hasitem` first.

Old saves keep working: nothing is stored differently.

## 5. HMs: forgetting them and removing them

### 5.1 HMs that can be forgotten

Change the three checks that refuse, and leave `MoveIsHM` alone (it also keeps HMs
from being used up):

- `src/pokemon_summary.c:940` and `:972`: drop the `MoveIsHM(...) == TRUE &&` condition,
  or replace the whole `if` condition with `FALSE`.
- `src/battle/battle_party_menu.c:1763`, in `BattlePartyMenu_IsSelectedMoveHM`:
  `return FALSE;`.

`PokemonSummary_PrintCantForgetHMMessage` and `BattlePartyMenu_PrintHMCantBeForgotten`
are then unused.

### 5.2 Removing HMs

There is no single switch. Pick the parts you want:

| Goal | Change |
|---|---|
| HM moves can be forgotten | [5.1](#51-hms-that-can-be-forgotten) |
| obstacles work without a Pokémon that knows the move | [player-movement.md](player-movement.md#hms-without-a-pokémon-that-knows-the-move) (`_HMUserOrLead`, or a key item) |
| no badge needed | the `CheckBadge` lines in `scr_seq_0146.s` and the `PlayerProfile_TestBadgeFlag` checks in `src/field_move.c` ([gyms.md](gyms.md#what-badges-do)) |
| the HM items aren't given | the scripts below |
| an HM becomes an ordinary machine | below |

**Where the HMs are given:**

| HM | Map script |
|---|---|
| HM01 Cut | `data/maps/IlexForest/scripts.pory` |
| HM02 Fly | `data/maps/Cianwood/scripts.pory` |
| HM03 Surf | `data/maps/Ecruteak_DanceTheater/scripts.pory` |
| HM04 Strength | `data/maps/Route42/scripts.pory` |
| HM05 Whirlpool | `data/maps/TeamRocketHeadquarters_B2F/scripts.pory` |
| HM06 Rock Smash | `data/maps/Route36/scripts.pory` |
| HM07 Waterfall | item ball in `data/maps/IcePath_1F` (`FLAG_HIDE_ITEMBALL_D39R0101_HM07`) |
| HM08 Rock Climb | `data/maps/Pallet_TownOaksLab/scripts.pory` |

**An HM that is no longer an HM.** `MoveIsHM` checks the last 8 entries of
`sTMHMMoves`. To make, for example, Whirlpool an ordinary move, skip it there:

```c
BOOL MoveIsHM(u16 moveId) {
    u8 i;

    if (moveId == MOVE_WHIRLPOOL) {
        return FALSE;
    }
    for (i = 0; i < NUM_HMS; i++) {
        ...
```

HM05 is then used up like a TM (unless TMs are [reusable](#4-reusable-tms)), the
bag says "Booted up a TM", and Whirlpool can be forgotten. The item keeps its HM
icon, its place after the TMs and its 0 price (`items.json`). To make it sellable,
give it a price and `"prevent_toss": false`.

Old saves keep working for all of these. A Pokémon that already knows an HM keeps it;
it just can be forgotten now.

## 6. Adding a field move

A field move needs the party-menu entry, a check, a use function, and scripts.
[party-menu-and-item-use.md](party-menu-and-item-use.md#2-the-party-menu) lists the
tables; this is a full example.

**Example: melting ice with Flamethrower.** An ice block (`SPRITE_ICE`) with the script
`std_field_melt` melts when you press A and a party Pokémon knows Flamethrower, or
when you pick Flamethrower in the party menu while facing it. It was built; see
[section 7](#7-testing-the-recipes).

The ice is recognised by its **script**, not its sprite: `SPRITE_ICE` is also used in
Mahogany Gym and Seafoam Islands, which shouldn't melt.

### 6.1 The party menu

The field moves are three lists that must stay in step:

| List | File | Order |
|---|---|---|
| `sFieldMoves` (the moves) | `src/party_menu.c:205` | as `PartyMonContextMenuItem` |
| `PartyMonContextMenuItem` (`PARTY_MON_CONTEXT_MENU_CUT`...) and the action table `_02101CB8` | `include/party_menu.h:116`, `src/party_menu_list_items.c:57` | Whirlpool before Flash |
| `PartyMenuActionReturn` (`PARTY_MENU_ACTION_RETURN_CUT`...) and `sFieldMoveFuncTable` | `include/party_menu.h:152`, `src/field_move.c:72` | Whirlpool after Chatter |

`sFieldMoveFuncTable` is indexed by `selectedAction - PARTY_MENU_ACTION_RETURN_CUT`.
Milk Drink and Softboiled have return values (14 and 15) but no row: they stay in the
party menu. A new move after them is index 16, so the table needs two empty rows first.

`include/party_menu.h`, after Softboiled in both enums:

```c
    PARTY_MON_CONTEXT_MENU_SOFTBOILED,
    PARTY_MON_CONTEXT_MENU_MELT,
    PARTY_MON_CONTEXT_MENU_MAX,
```
```c
    PARTY_MENU_ACTION_RETURN_SOFTBOILED,
    PARTY_MENU_ACTION_RETURN_MELT,
```

`src/party_menu.c`, `sFieldMoves` (its size comes from the enum):

```c
    MOVE_SOFTBOILED,
    MOVE_FLAMETHROWER,
};
```

`src/party_menu_list_items.c`: a prototype, a row in `_02101CB8`, and the action:

```c
    [PARTY_MON_CONTEXT_MENU_SOFTBOILED] = (u32)PartyMonContextMenuAction_Softboiled,
    [PARTY_MON_CONTEXT_MENU_MELT] = (u32)PartyMonContextMenuAction_Melt,
```
```c
static void PartyMonContextMenuAction_Melt(PartyMenu *partyMenu, int *pState) {
    partyMenu->args->selectedAction = PARTY_MENU_ACTION_RETURN_MELT;
    PartyMenuContextMenuAction_FieldMoveCommon(partyMenu, pState);
}
```

`PartyMenuContextMenuAction_FieldMoveCommon` (`:678`) calls the check and prints the
refusal (not here, need badge, have a follower, already surfing, not now).

`src/start_menu.c:943`, so the start menu calls the use function:

```c
    case PARTY_MENU_ACTION_RETURN_HEADBUTT:
    case PARTY_MENU_ACTION_RETURN_MELT: {
```

A Pokémon knows at most 4 moves, so it has at most 4 field-move entries; their text
is the move name, through `msg_0300_00139`-`00142` (one per entry). No new text is
needed.

### 6.2 The check and the use

`FieldMove_InitCheckData` (`src/field_move.c:121`) runs when the start menu opens and
records what the player faces as bits in `checkData->flag`. The field is a `u16`:
bits 1 and 8-11 are named but never set, 14 and 15 are free.

`include/field_move.h`:

```c
#define FIELD_MOVE_CHECK_HEADBUTT_F  13
#define FIELD_MOVE_CHECK_MELT_F      14
```
```c
    FIELD_MOVE_CHECK_HEADBUTT = (1 << FIELD_MOVE_CHECK_HEADBUTT_F),
    FIELD_MOVE_CHECK_MELT = (1 << FIELD_MOVE_CHECK_MELT_F)
```

`src/field_move.c`, in `FieldMove_InitCheckData`, after the sprite `switch`:

```c
        if (MapObject_GetScriptID(facingObject) == std_field_melt) {
            checkData->flag |= FIELD_MOVE_CHECK_MELT;
        }
```

the table rows:

```c
    { FieldMove_UseHeadbutt,   FieldMove_CheckHeadbutt   },
    { NULL,                    NULL                      }, // Milk Drink
    { NULL,                    NULL                      }, // Softboiled
    { FieldMove_UseMelt,       FieldMove_CheckMelt       },
};
```

and the functions (prototypes at the top), modelled on Cut:

```c
static u32 FieldMove_CheckMelt(const FieldMoveCheckData *checkData) {
    if (checkData->fieldSystem->mapLoadType == MAP_LOAD_TYPE_UNION || checkData->fieldSystem->mapLoadType == MAP_LOAD_TYPE_COLOSSEUM) {
        return FIELD_MOVE_RESPONSE_NOT_HERE;
    }
    if (FieldMove_CheckFlag(checkData, FIELD_MOVE_CHECK_MELT)) {
        return FIELD_MOVE_RESPONSE_OK;
    }

    return FIELD_MOVE_RESPONSE_NOT_HERE;
}

static void FieldMove_UseMelt(FieldMoveUseData *useData, const FieldMoveCheckData *checkData) {
    StartMenuTaskData *startMenu = TaskManager_GetEnvironment(useData->taskManager);
    FieldUseMoveEnvironment *useMoveEnvironment = FieldMove_CreateUseEnvironment(useData, checkData);
    FieldSystem_LoadFieldOverlay(checkData->fieldSystem);
    startMenu->exitTaskFunc = Task_UseMeltInField;
    startMenu->exitTaskEnvironment = useMoveEnvironment;
    startMenu->state = START_MENU_STATE_12;
}

static BOOL Task_UseMeltInField(TaskManager *taskManager) {
    FieldUseMoveEnvironment *environment = TaskManager_GetEnvironment(taskManager);
    FieldSystem *fieldSystem = TaskManager_GetFieldSystem(taskManager);
    StartScriptFromMenu(taskManager, std_menu_melt, environment->facingObject);
    FieldMove_SetArgs(fieldSystem, environment->useData.partySlot, 0, 0, 0);
    FieldMove_DeleteUseEnvironment(environment);
    return FALSE;
}
```

For a badge, add `if (!PlayerProfile_TestBadgeFlag(Save_PlayerData_GetProfile(checkData->fieldSystem->saveData), BADGE_X)) { return FIELD_MOVE_RESPONSE_NEED_BADGE; }`
as in `FieldMove_CheckCut`. `StartScriptFromMenu` makes the facing object the
"last talked" object, and `FieldMove_SetArgs` puts the Pokémon's party slot in
`VAR_SPECIAL_x8000`.

A move that doesn't face anything (like Flash, Teleport or Sweet Scent) checks the
map or the weather instead, and passes `NULL` as the object.

### 6.3 The scripts

The field-move scripts are standard scripts in
`files/fielddata/script/scr_seq/scr_seq_0146.s`: id 10000 + the script's number in the
file (`script_manager.c:43`; the next bank starts at 10100). Retail uses 10000-10018.

`include/constants/std_script.h`:

```c
#define std_menu_headbutt     10018
#define std_field_melt        10019
#define std_menu_melt         10020
```

`scr_seq_0146.s`: two more `ScrDef` lines before `ScrDefEnd`

```
	ScrDef scr_seq_0146_018
	ScrDef scr_seq_0146_019
	ScrDef scr_seq_0146_020
	ScrDefEnd
```

and the scripts, before the final `.balign 4, 0`:

```
scr_seq_0146_019:
	PlaySE SEQ_SE_DP_SELECT
	LockAll
	GetPartySlotWithMove VAR_SPECIAL_RESULT, MOVE_FLAMETHROWER
	Compare VAR_SPECIAL_RESULT, 6
	GoToIfEq _MeltCant
	NPCMsg msg_0211_00035
	TouchscreenMenuHide
	GetMenuChoice VAR_SPECIAL_RESULT
	TouchscreenMenuShow
	Compare VAR_SPECIAL_RESULT, 0
	GoToIfEq _MeltYes
	CloseMsg
	ReleaseAll
	End

_MeltCant:
	NPCMsg msg_0211_00037
	WaitButton
	CloseMsg
	ReleaseAll
	End

_MeltYes:
	GetPartySlotWithMove VAR_SPECIAL_x8000, MOVE_FLAMETHROWER
	GoTo _MeltUse
	End

scr_seq_0146_020:
	LockAll
_MeltUse:
	BufferPartyMonNick 0, VAR_SPECIAL_x8000
	NPCMsg msg_0211_00036
	CloseMsg
	PlayFieldMoveCutIn VAR_SPECIAL_x8000
	HidePerson VAR_SPECIAL_LAST_TALKED
	ReleaseAll
	End
```

`_019` is the A prompt and `_020` the party-menu use; `GetPartySlotWithMove` gives the
first non-egg that knows the move, or 6. `PlayFieldMoveCutIn` shows that Pokémon and
waits. The retail scripts also show the following Pokémon's own animation; see
Cut's `_00AD` to copy it.

The text goes at the end of `files/msgdata/msg/msg_0211.json`:

```json
{
  "id": "msg_0211_00035",
  "en_US": ["This ice looks like it could melt!\n", "Would you like to use Flamethrower? {YESNO 0}"]
},
{
  "id": "msg_0211_00036",
  "en_US": "{STRVAR_1 0, 0, 0} used Flamethrower!\r"
},
{
  "id": "msg_0211_00037",
  "en_US": ["It’s a block of ice. A Fire-type move\n", "might melt it."]
}
```

(msg_0211_00017-00019 are Diamond/Pearl's Defog texts, unused.)

### 6.4 The obstacle

In the map's `map.json`, an object with `"graphics_id": "SPRITE_ICE"` and `"script":
"std_field_melt"`. `HidePerson` sets the object's `flag`: a normal flag keeps the ice
gone, a `FLAG_MAPTEMP_*` flag brings it back when the map loads again (as Cut trees
do).

### 6.5 Other kinds of field move

| Kind | Copy | Notes |
|---|---|---|
| an object to clear | Cut, Rock Smash | as above |
| a tile in front | Waterfall, Whirlpool, Rock Climb | a `MetatileBehavior_Is...` check in `FieldMove_InitCheckData`, and an A-prompt script from `GetInteractedMetatileScript` (`src/field/field_control.c:577`) |
| an effect on the whole map | Flash | the weather or a map check |
| moving somewhere | Fly, Teleport, Dig | the use function starts an app or a warp task instead of a script |
| something checked on every step | Strength, going down waterfalls | `Field_PlayerAvatar_TryFieldMoveInDirection` ([player-movement.md](player-movement.md#6-field-moves-hms)) |

A move in `sFieldMoves` appears for **every** Pokémon that knows it. To make it an HM,
put it in the HM part of `sTMHMMoves`: that means swapping it with an existing HM, or
an HM09 in its own block as in [section 3](#3-adding-tms-after-hm08), with `MoveIsHM`
checking that block too.

## 7. Testing the recipes

All recipes in sections 3-6 (TM93-TM95 with Machop able to learn TM93 and TM94,
reusable TMs, forgettable HMs, the Melt field move on the Seafoam Islands B3F ice)
were applied together and built with `make heartgold`: no errors or warnings. The
built `personal.narc` gives Machop `tmhm_4 = 0x3A` (HM06, HM08, TM93, TM94). The
changes were then reverted and the build matched the retail ROM again (all 4
checksums OK). **They were not play-tested.**

In a game, check:

| Recipe | Check |
|---|---|
| New TMs | the item ball says "found TM93 Drain Punch!"; the bag shows "No. 93", the quantity, Drain Punch's PP, power, type and category; Machop shows ABLE, others UNABLE; a Machop father passes Drain Punch to an egg |
| Reusable TMs | after teaching, the TM is still in the bag |
| Forgettable HMs | learning a fifth move (TM, level-up in and out of battle) can replace Cut |
| Melt | A at the ice: the yes/no prompt with a Flamethrower user, the "might melt it" text without one; from the party menu while facing the ice: it melts; elsewhere: "can't be used here" |

## Where to look

| What | Where |
|---|---|
| machine ids | `include/constants/items.h:681` |
| machine moves, item → move / index, `MoveIsHM` | `src/item.c:31`, `:398`-`:425` |
| who can learn what | `personal.json` `tms`/`hms`; `personal.json.txt:49`; `src/pokemon.c:3783` |
| teaching and using up | `src/party_menu_items.c:755`-`:915` |
| bag screen | `src/application/bag/bag_app.c:1742`, `:3420`; `bag_app_display.c:433`; `asm/bag_app_data.s:235` |
| forgetting | `src/pokemon_summary.c:940`, `:972`; `src/battle/battle_party_menu.c:1755` |
| field moves: party menu | `src/party_menu.c:205`, `:1616`; `src/party_menu_list_items.c:57`, `:678`; `src/start_menu.c:943` |
| field moves: checks and uses | `src/field_move.c` |
| field-move scripts and text | `scr_seq_0146.s`, `msg_0211.json`, `include/constants/std_script.h:631` |
