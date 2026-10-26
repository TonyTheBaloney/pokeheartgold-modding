<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# The bag

> AI-generated; not affiliated with pret. See AI.md at the repository root.

How the bag is stored in the save (pockets and item slots), how other code opens the
bag screen and reads what the player picked, and how the screen itself works: pockets,
item pages, the item menu, tossing, selling, moving. Three other guides cover the
neighbouring parts and are not repeated here:

- [items.md](items.md): `items.json`, which pocket an item goes in, icons, descriptions.
- [party-menu-and-item-use.md](party-menu-and-item-use.md): what happens after "Use" or
  "Give" (field use functions, the party menu).
- [ui.md](ui.md): applications, BG layers, windows, sprites, touch input in general.

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `gBagPockets[]`, `struct BagPocket` in SaveBlock1 | `Bag` ([include/bag_types_def.h](../../include/bag_types_def.h)): one `ItemSlot` array per pocket, saved as the `SAVE_BAG` chunk |
| `AddBagItem`, `RemoveBagItem`, `CheckBagHasItem`, `CheckBagHasSpace` | `Bag_AddItem`, `Bag_TakeItem`, `Bag_HasItem`, `Bag_HasSpaceForItem` ([src/bag.c](../../src/bag.c)) |
| `ItemId_GetPocket` | `GetItemAttr(itemId, ITEMATTR_FIELD_POCKET, heapID)` |
| `gSaveBlock1Ptr->registeredItem` (Select) | `Bag.registeredItems[2]`: Y and the two touch-screen buttons |
| `GoToBagMenu(ITEMMENULOCATION_*, pocket, callback)` | `Bag_CreateView` + `BagView_Init(..., mode, ...)` + launch the application; the mode is a bare number |
| `gBagPosition` (cursor per pocket) | `BagCursor` (`fieldSystem->bagCursor`), in RAM only |
| `sItemMenuActions` + `sContextMenuItems_*` lists | `gItemActionFuncs` + `BagApp_PrepareContextMenu` |
| `gSpecialVar_ItemId` + exit callback | `BagView.itemId` + `BagView.selectedAction`, read by the caller |
| `SortBerriesOrTMHMs` | `Bag_AddItem` sorts the TM/HM and Berry pockets itself |
| a scrolling list menu | pages of 6 touch buttons; no `ListMenu` |
| the battle bag is the same menu | a separate screen, [src/battle/battle_bag_menu.c](../../src/battle/battle_bag_menu.c) |

## 1. Bag data

### Pockets

| Id | Constant | `Bag` field | Slots | Max stack | Sorted on add |
|---|---|---|---|---|---|
| 0 | `POCKET_ITEMS` | `items` | `NUM_BAG_ITEMS` 165 | 999 | no |
| 1 | `POCKET_MEDICINE` | `medicine` | `NUM_BAG_MEDICINE` 40 | 999 | no |
| 2 | `POCKET_BALLS` | `balls` | `NUM_BAG_BALLS` 24 | 999 | no |
| 3 | `POCKET_TMHMS` | `TMsHMs` | `NUM_BAG_TMS_HMS` 101 | 99 | by item id |
| 4 | `POCKET_BERRIES` | `berries` | `NUM_BAG_BERRIES` 64 | 999 | by item id |
| 5 | `POCKET_MAIL` | `mail` | `NUM_BAG_MAIL` 12 | 999 | no |
| 6 | `POCKET_BATTLE_ITEMS` | `battleItems` | `NUM_BAG_BATTLE_ITEMS` 30 | 999 | no |
| 7 | `POCKET_KEY_ITEMS` | `keyItems` | `NUM_BAG_KEY_ITEMS` 50 | 999 | no |

The ids, `POCKETS_COUNT` (8) and the sizes are in
[include/constants/items.h](../../include/constants/items.h); the limits themselves are
listed in [game-limits.md](game-limits.md#money-coins-and-the-bag). The id is also the
order of the pocket tabs on screen (§3).

The `Bag` struct ([bag_types_def.h:36](../../include/bag_types_def.h#L36)) lists the
arrays in another order, which is the save layout: `items`, `keyItems`, `TMsHMs`, `mail`,
`medicine`, `berries`, `balls`, `battleItems`, then `u16 registeredItems[2]`.

An `ItemSlot` ([include/item.h](../../include/item.h)) is `u16 id; u16 quantity;`. 486
slots plus the two registered ids make the 1,948-byte `SAVE_BAG` chunk
([save-data.md](save-data.md)). `Save_Bag_Get(saveData)` returns it.

Which pocket an item goes in is its `fieldPocket` in `items.json` ([items.md](items.md)).
`Bag_GetItemPocket` ([bag.c:72](../../src/bag.c#L72)) reads it with `GetItemAttr` and
switches to the matching array.

### Functions

| Function | Does |
|---|---|
| `Bag_AddItem(bag, id, qty, heapID)` | adds to the item's stack, or to the first empty slot. Fails (FALSE, nothing added) if the stack would pass 999 (99 for TMs/HMs) or there is no empty slot. Then sorts the TM/HM and Berry pockets |
| `Bag_HasSpaceForItem` | the same test without adding |
| `Bag_TakeItem(bag, id, qty, heapID)` | fails if fewer than `qty`; empties the slot at 0 and moves later slots up (`PocketCompaction`) |
| `Bag_HasItem`, `Bag_GetQuantity` | look up the item in its pocket |
| `Pocket_TakeItem`, `Pocket_GetQuantity` | the same on a bare `ItemSlot` array and count (the bag screen uses these on the pocket it shows) |
| `Bag_PocketNotEmpty(bag, pocket)` | used by the `BagPocketHasItems` script command |
| `Bag_GetPocketSlotN(bag, pocket, n)` | slot `n` of a pocket, NULL past the end (the battle bag walks pockets with it) |
| `Bag_TryRegisterItem`, `Bag_UnregisterItem`, `Bag_GetRegisteredItem1/2` | the two registered items |
| `MoveItemSlotInList(slots, from, to, pocket, heapID)` | moves one slot within a pocket ([item.c:137](../../src/item.c#L137)); the bag's MOVE |

Each item has at most one slot: there are no split stacks. There is no "sort" command;
apart from the automatic sort above, slots stay in the order they were added until the
player moves them.

### Registered items

`registeredItems[0]` is used by Y and the first touch-screen button,
`registeredItems[1]` by the second (`UseRegisteredItemButtonInField`,
[field_use_item.c:756](../../src/field_use_item.c#L756)). `Bag_TryRegisterItem` fills the
first free one and fails when both are taken ("You can only register up to two items",
`msg_0010_00103`). Unregistering slot 1 moves slot 2 down. Whether an item can be
registered is its `selectable` key.

### The cursor

`BagCursor` ([include/bag_cursor.h](../../include/bag_cursor.h)) remembers the last pocket
and, per pocket, the page (`scroll`) and the slot on it (`position`); `field` for this
screen, `battle` for the battle bag. The field system allocates one
(`fieldSystem->bagCursor`, in [src/overlay_124.c](../../src/overlay_124.c)); it is not
saved. Both halves store positions as `u8`.

## 2. Opening the bag

### The view (arguments and results)

The caller builds a `BagView` ([bag_types_def.h:74](../../include/bag_types_def.h#L74)),
passes it as the application's arguments, and reads it after the screen closes:

| Field | In / out | Meaning |
|---|---|---|
| `pockets[8]` | in | per pocket: `slots` (points into the save's `Bag`, NULL = pocket not shown), `pocketId`; the screen keeps `scroll`, `position`, `itemCount` here |
| `mode` | in | why it was opened (table below) |
| `cursor` | in | a `BagCursor`, or NULL to start on the first shown pocket at the top |
| `checkUseData` | in | for the "Use" check functions ([party-menu-and-item-use.md §1](party-menu-and-item-use.md#1-using-an-item-from-the-bag-in-the-field)) |
| `isCycling`, `mapLoadType` | in | change the first item-menu entry (§3) |
| `menuInputStateMgr` | in / out | whether the player last used keys or touch |
| `partySlot` | in / out | carried through for the start menu (which Pokémon to come back to) |
| `pocketIndex` | out | the pocket being shown (set from `cursor` on entry) |
| `itemId` | out | the item chosen (`BagView_GetItemId`) |
| `selectedAction` | out | what the player did (`BagView_GetReturnCode`) |
| `sellCount` | out | sale counter for the mart (`BagView_GetSellCount`) |

`Bag_CreateView(bag, pockets, heapID)` ([bag.c:304](../../src/bag.c#L304)) takes a list of
pocket ids ended by `POCKET_BAG_VIEW_END` (0xFF) and fills `pockets[]`;
`BagView_Init(view, saveData, mode, cursor, menuInputStateMgr)` sets the rest. The field bag
([launch_application.c:192](../../src/launch_application.c#L192)):

```c
BagView *bagView = Bag_CreateView(Save_Bag_Get(fieldSystem->saveData), sAllPockets, HEAP_ID_FIELD2);
BagView_Init(bagView, fieldSystem->saveData, 0, fieldSystem->bagCursor, &fieldSystem->menuInputState);
BagView_SetMapLoadType(bagView, fieldSystem->mapLoadType);
if (PlayerAvatar_GetState(fieldSystem->playerAvatar) == PLAYER_STATE_CYCLING) {
    BagView_SetOnBike(bagView);
}
BagView_SetCheckUseData(bagView, taskman);
Bag_LaunchApp(fieldSystem, bagView);
```

The order of the pocket list does not matter: `BagView_SetItem`
([bag_view.c:50](../../src/bag_view.c#L50)) stores each pocket at `pockets[pocketId]` and
ignores its `position` argument (the source comments this as a bug). So the list only
says **which** pockets are shown, and `pocketIndex` is always a pocket id.

### Modes

`mode` is a plain number; there is no enum.

| Mode | Opened by | Pockets | What the screen does |
|---|---|---|---|
| 0 | start menu "Bag" (`Bag_LaunchApp_AllPockets`) | all 8 | normal: item menu with USE, GIVE, TOSS... |
| 1 | the party menu's "Item → Give" ([start_menu.c:915](../../src/start_menu.c#L915)); the PC's item mode (`PCBox_StartBagApp`, [pc_box_ui.c:762](../../src/application/pc_box/pc_box_ui.c#L762)) | all; the PC leaves out Mail (`gPCBoxBagPockets`) | pick an item to hold; no item menu |
| 2 | a mart's "Sell" (`Task_Mart_OpenSellMenu`, [shop_menu.c:1518](../../src/overlay_03/shop_menu.c#L1518)) | all 8 | pick an item, quantity, sell |
| 3 | `BagSelectItem` / `BagSelectItemNoResult` script commands (`Bag_LaunchApp_WithPocket`) | Items, or Berries | see below |
| 4, 5 | nobody | | Diamond/Pearl/Platinum leftovers: only draw a Poffin box (`BagApp_DrawPoffinCountMsgBox_DPPt`) |
| 6 | the Berry Pots (`BerryPots_MainSeq_StartBag`, [berry_pots.c:154](../../src/berry_pots.c#L154)) | Items (mulch) or Berries | item menu has only USE (for berries and mulch) and CANCEL |

Mode 3 waits in `BAG_STATE_DEBUG_SUB_SCREEN_LAYOUT`, whose handler only reacts to
`PAD_BUTTON_DEBUG` and never leaves the state: read as code, that bag can't be used or
closed (not tested in game). No retail script uses those commands.

### Return codes

The screen writes `selectedAction`; each caller reads only the codes it expects. The start
menu's handler is `Task_StartMenu_HandleReturn`
([start_menu.c:1023](../../src/start_menu.c#L1023)).

| `selectedAction` | Set by | Start menu does |
|---|---|---|
| 0 | USE (mode 0), after the check passed and the bag didn't handle it itself | calls the item's `menu` function ([party-menu-and-item-use.md §1](party-menu-and-item-use.md#the-full-sequence)) |
| 1 | `BagApp_ItemAction_Action9` (no item gets it in retail) | `StartMenu_ShowBerryTag` |
| 2 | GIVE (mode 0) | party menu with `PARTY_MENU_CONTEXT_9` |
| 3 | `BagApp_ItemContextMenu_Confirm` (no item gets it in retail) | back to the field |
| 4 | an item picked in mode 1 (also B, with `itemId` = `ITEM_NONE`); USE in mode 6 | reopens the party menu to give the item to the Pokémon picked before (`PARTY_MENU_CONTEXT_10`), or composes mail; `ITEM_NONE` just reopens it. The Berry Pots read `itemId` |
| 5 | CANCEL / B | back to the field |

The mart reads only `sellCount` (`Task_Bag_SellMenu`, [src/mart_bag_task.c](../../src/mart_bag_task.c));
the PC reads only `itemId`.

**The battle bag is not this screen.** In battle, `BattleBagMenu`
([src/battle/battle_bag_menu.c](../../src/battle/battle_bag_menu.c), overlay `OVY_8`) copies
items from every pocket into five battle pages by their `battlePocket` flags
(`BattleBagMenu_SortItemsIntoPockets`, [battle_bag_menu.c:1115](../../src/battle/battle_bag_menu.c#L1115)).
It shares only the `Bag` data and `BagCursor.battle`. See
[party-menu-and-item-use.md §4](party-menu-and-item-use.md#4-using-an-item-in-battle).

## 3. The screen

The application is `Bag_Init` / `Bag_Main` / `Bag_Exit` in
[src/application/bag/bag_app.c](../../src/application/bag/bag_app.c), in overlay `OVY_15`
with [bag_app_display.c](../../src/application/bag/bag_app_display.c) and the data in
[asm/bag_app_data.s](../../asm/bag_app_data.s), with its own heap `HEAP_ID_6` (0x42000
bytes). The field launches it with `sOverlayTemplate_Bag` (`Bag_LaunchApp`); the PC uses
`gOverlayTemplate_Bag` from the data file and loads `OVY_15` itself. Its data is `BagApp`
([include/application/bag/bag_app.h](../../include/application/bag/bag_app.h)), whose
comments say what each window and sprite index is.

### Layout

- **Top screen**: a 3D model of the bag (one per player gender) that opens the chosen
  pocket, and the description window `windows[0]`. For TMs/HMs, `windows[1]` and the type
  and category sprites show the move.
- **Bottom screen**: eight pocket tabs along the top, six item buttons (two columns,
  three rows), page arrows and the page counter at the bottom left, CANCEL at the bottom
  right.

Everything is a "button" numbered by `cursorButton`. The same numbers index the D-pad table
`gBagAppButtonNavTable` (up, down, left, right per button), the touch rectangles
`sTouchHitboxes_Main` and the cursor positions `gBagAppCursorPositions`:

| `cursorButton` | Button |
|---|---|
| 0-7 | pocket tabs, by pocket id |
| 8-13 | item slots on the page (slot = `scroll + button - 8`) |
| 14, 15 | previous / next page (`BAG_BUTTON_PREV_PAGE`, `_NEXT_PAGE`) |
| 16 | CANCEL (`BAG_BUTTON_CANCEL`) |
| 17-20 | item menu entries (only as cursor positions) |

### States

`Bag_Main` ([bag_app.c:379](../../src/application/bag/bag_app.c#L379)) switches on
`BAG_STATE_*` (the enum at [bag_app.c:140](../../src/application/bag/bag_app.c#L140)); each
handler returns the next state. After the fade-in, the mode picks the first state:

| Group | States | Entered from |
|---|---|---|
| browse | `BAG_STATE_INPUT` (mode 0, 6), `_HOLD_ITEM_SELECT_INPUT` (1), `_SELL_SELECT_INPUT` (2) | the fade-in, and the end of every action |
| item menu | `_OPEN_ITEM_MENU` → `_ITEM_MENU_INPUT` → `_RUN_ITEM_ACTION` or `_CLOSE_ITEM_MENU` | A or a tap on an item in modes 0 and 6 |
| use | `_WAIT_ITEM_MESSAGE`, `_RUN_USE_ITEM_TASK` | USE |
| toss | `_TRASH_QUANTITY_INPUT` → `_SHOW_TRASH_CONFIRM` → `_WAIT_TRASH_CONFIRM_MESSAGE` → `_TRASH_YES_NO` → `_WAIT_TRASH_RESULT_MESSAGE` → `_FINISH_TRASH` (`_CANCEL_TRASH`) | TRASH |
| sell | `_START_SELL` → `_SETUP_SELL_QUANTITY` → `_SELL_QUANTITY_INPUT` → `_SHOW_SELL_PRICE` → `_WAIT_SELL_PRICE_MESSAGE` → `_SELL_YES_NO` → `_COMPLETE_SALE` → `_WAIT_SALE_MESSAGE` | an item in mode 2 |
| move | `_MOVE_ITEM_INPUT` → `_DROP_MOVED_ITEM` / `_END_MOVE_ITEM` | MOVE |
| other | `_NEXT_PAGE`, `_PREV_PAGE`, `_WAIT_REGISTER_FAIL_MESSAGE`, `_WAIT_CANT_HOLD_MESSAGE`, `_BUTTON_FEEDBACK` (flashes a button sprite, then goes to the stored state), `_FADE_OUT`, `_WAIT_FADE_OUT` (exit) | |

`BAG_STATE_POCKET_SWITCH` and the `*_DPPt` pocket-switch functions are Diamond/Pearl/Platinum
code that nothing reaches in HGSS.

### Switching pockets

A tap on a tab, L/R, or left/right while the cursor is on the tab row ends in
`BagApp_HandleCursorAction` ([bag_app.c:1120](../../src/application/bag/bag_app.c#L1120))
with button 0-7. Tabs of pockets not in the view are skipped
(`BagApp_PocketIdToBagViewPosition`, `BagApp_GetPocketNeighbor`). Switching sets
`pocketIndex`, rebuilds the name list, redraws the page, loads the pocket's colors
(`BagApp_LoadObjPaletteByPocket`, `BagApp_LoadBgPaletteByPocket`: one palette per pocket),
switches the 3D model to that pocket's animations and turns the camera to
`gCameraTweenKeys[gender][pocket + 1]`.

### The item list

`BagApp_SetItemNameStringsFromCurPocket` ([bag_app.c:768](../../src/application/bag/bag_app.c#L768))
reads the shown pocket into `itemNames[]` and `itemIds[]` (165 entries each, the largest
pocket) until the first empty slot, and sets `itemCount`. In the TM/HM pocket the names are
the move names (`msg_0750`). A page is six slots; `scroll` is the first slot of the page,
a multiple of 6. The six name windows come in two banks that alternate
(`BagApp_RedrawItemNameWindows`), so the new page is drawn before the old one is cleared.

What is printed under the name depends on the pocket
(`BagApp_PrintItemNameAndMaybeQuantityOnWindow`, [bag_app_display.c:428](../../src/application/bag/bag_app_display.c#L428)):

| Pocket | Second line |
|---|---|
| TMs & HMs | the TM/HM number; the quantity only for `ITEM_TM01`-`ITEM_TM92` |
| Key Items | no quantity; the registered-button mark if the item is registered |
| all others | `x` + quantity, 3 digits (`msg_0010_00087`) |

The icons are sprites 1-6. `BagApp_ReplaceItemIconResObjs` swaps in each item's icon and
palette from `NARC_itemtool_itemdata_item_icon` (`GetItemIndexMapping`).

The description is printed in `windows[0]` on the top screen whenever the cursor moves
(`BagApp_UpdateDescriptionOnTopScreen`): the item's description (`GetItemDescIntoString`,
bank `msg_0221`, into a 130-character `String`), or, on a tab, the pocket's description
(`msg_0010_00120` + pocket id).

### The item menu

Picking an item in mode 0 or 6 runs `BagApp_PrepareContextMenu`
([bag_app.c:1508](../../src/application/bag/bag_app.c#L1508)). It fills five entries,
`choices.actions[5]`, with indexes into `gItemActionFuncs`
([bag_app_data.s:518](../../asm/bag_app_data.s#L518)) and `menuStrings[]`
(`BagApp_LoadContextMenuStrings`, [bag_app_display.c:83](../../src/application/bag/bag_app_display.c#L83)).
0xFF leaves an entry empty. The entries are fixed buttons: 0 top left, 1 top right,
2 bottom left, 3 bottom right, 4 CANCEL.

| Action | Label (`msg_0010_`) | Function | Offered (mode 0) |
|---|---|---|---|
| 0 | USE (`00000`) | `BagApp_ItemContextMenu_Use` | entry 0, if `fieldUseFunc` isn't `ITEM_FIELD_USE_NONE` |
| 1 | WALK (`00006`) | same | entry 0, Bicycle while cycling |
| 2 | CHECK (`00016`) | same | entry 0, Mail pocket |
| 3 | blank (`00098`) | same | entry 0, Berries if `Leftover_CanPlantBerry` (always FALSE) |
| 4 | blank (`00099`) | same | entry 0, `ITEM_POFFIN_CASE` |
| 5 | TRASH (`00001`) | `BagApp_ItemContextMenu_Trash` | entry 1, not `prevent_toss`, not TMs/HMs |
| 6 / 7 | REGISTER (`00002`) / DESELECT (`00018`) | `_Register` / `_Deselect` | entry 1 (replaces TRASH), if `selectable` |
| 8 | GIVE (`00003`) | `BagApp_ItemContextMenu_Give` | entry 2, not `prevent_toss`, not `ITEM_FAST_BALL`-`ITEM_PARK_BALL` |
| 9 | blank (`00004`) | `BagApp_ItemAction_Action9` | never |
| 10 | CONFIRM (`00005`) | `BagApp_ItemContextMenu_Confirm` | never |
| 11 | CANCEL (`00008`) | NULL | entry 4, always |
| 12 | MOVE (`00075`) | `BagApp_ItemContextMenu_Move` | entry 3, not TMs/HMs or Berries (they are kept sorted), not mode 6 |
| 13 | SELL (`00086`) | NULL | never (the label of the sell button) |
| 14 | USE (`00000`) | `BagApp_ItemContextMenu_UseInBerryPots` | entry 0 in mode 6, berries and mulch (`IsBerryOrMulch`) |
| 15 | STOP (`00128`) | `BagApp_ItemContextMenu_Use` | entry 0, GB Sounds while they play |

"Blank" labels are `garbage` placeholders (spaces) in the English text. In the Union Room
and Colosseum (`mapLoadType` 2, 3) entry 0 is only CHECK for mail. The button sprites for
entries 0-3 are shown when the entry isn't 0xFF (`BagApp_DrawContextMenuButtonSprites`). An
entry runs only if its `itemActions[]` pointer isn't NULL; the function returns the next
state. What USE does next (the check, in-bag uses like Repels, then return code 0) is in
[party-menu-and-item-use.md §1](party-menu-and-item-use.md#the-full-sequence).

### Toss, sell, move

- **Toss** (`BagApp_ItemContextMenu_Trash`, [bag_app.c:1903](../../src/application/bag/bag_app.c#L1903)):
  with one item it goes straight to "Is it OK to throw away...". Otherwise a quantity
  picker: three digits, touch buttons for ±100/±10/±1 (the unneeded ones hidden by
  `BagApp_GetNumberWidthType`), or the D-pad (`HandleNumberSelectInput`). Yes takes the
  items with `Pocket_TakeItem`.
- **Sell** (`BagAppMainTask_HandleSelectedItemForSale`, [bag_app.c:2473](../../src/application/bag/bag_app.c#L2473)):
  the price is `ITEMATTR_PRICE >> 1`. Items with `prevent_toss` or price 0 get "Oh, no. I
  can't buy that." The quantity has two digits and is capped at 99. `BagAppMainTask_CompleteSale`
  adds the money and takes the items. `sellCount` goes up by one for each single item sold
  and is set to 2 when several are sold at once.
- **Move**: the item follows the cursor across pages; dropping it calls
  `MoveItemSlotInList` (`BagAppMainTask_ApplyMoveItem`, [bag_app.c:1463](../../src/application/bag/bag_app.c#L1463)).
- **Give in mode 1** refuses `prevent_toss` items and `ITEM_FAST_BALL`-`ITEM_PARK_BALL`
  ("can't be held", `msg_0010_00047`).

### Graphics and text

| What | Where |
|---|---|
| backgrounds, tabs, buttons, cursor, 3D bag models and animations | `NARC_a_0_1_5` = `files/graphic/bag/bag_graphics/bag_graphics_NNNNN.*` (binary members; [graphics.md](graphics.md)). Member numbers in the code are these file numbers: `0x2B` is `bag_graphics_00043.NSCR`, the models are 55 and 74 (`BagApp_Load3dAssets`) |
| item icons | `files/itemtool/itemdata/item_icon/` ([items.md](items.md#icons)) |
| menu labels, messages, pocket descriptions | `files/msgdata/msg/msg_0010.json` |
| item names / descriptions | `msg_0222` / `msg_0221`, from `items.json` |
| pocket names ("...in the ITEMS pocket") | `msg_0226`, used by `BufferPocketName` outside the bag. `msg_0225` is loaded into `unusedStrings` and never printed |

## 4. How-tos

### Add an entry to the item menu

Example: a SPRAY entry for the SquirtBottle that closes the bag with a new return code,
handled by the start menu. A key item has no GIVE, so entry 2 is free. These edits
compile (checked with the game's compiler; not linked or run).

1. **The label**: append to `files/msgdata/msg/msg_0010.json` (at the end, so no number
   moves; [text-and-messages.md](text-and-messages.md#the-json-format)):

   ```json
   {
     "id": "msg_0010_00129",
     "en_US": "SPRAY"
   }
   ```
2. **The strings array**: in `BagApp`, `String *menuStrings[16];` becomes `[17]`. In
   `BagApp_LoadContextMenuStrings` add
   `app->menuStrings[16] = NewString_ReadMsgData(app->msgData, msg_0010_00129);` and make the
   loop in `BagApp_UnloadContextMenuStrings` run to `NELEMS(app->menuStrings)` (it has a
   literal 16).
3. **The function table**: in `asm/bag_app_data.s`, add `.extern BagApp_ItemContextMenu_Spray`
   with the other `.extern`s and `.word BagApp_ItemContextMenu_Spray` after the last entry
   of `gItemActionFuncs` (index 16).
4. **The function** in `bag_app.c` (declared with the other `BagApp_ItemContextMenu_*`),
   modelled on `BagApp_ItemContextMenu_Give`:

   ```c
   int BagApp_ItemContextMenu_Spray(BagApp *app) {
       BagApp_RemoveContextMenuWindowsAndRedrawTopScreenUI(app);
       BagApp_SetCancelButtonDrawFlag(app, FALSE);
       BagApp_HideCursorSprite(app);
       BeginAppScreenFade(1, HEAP_ID_6);
       app->bagView->selectedAction = 6; // new return code, read by the caller
       return BAG_STATE_WAIT_FADE_OUT;
   }
   ```
5. **Offer it**: in `BagApp_PrepareContextMenu`, inside `if (app->bagView->mode == 0)`,
   after the REGISTER block:

   ```c
   if (app->bagView->itemId == ITEM_SQUIRTBOTTLE) {
       choices.actions[2] = 16; // gItemActionFuncs[16], menuStrings[16]
   }
   ```
6. **Handle the return code**: in `Task_StartMenu_HandleReturn` add a `case 6:` before
   `case 3:`. `BagView_GetItemId(bagView)` is the item. To return to the field, do what
   the default case does (`FieldSystem_LoadFieldOverlay(fieldSystem);
   startMenu->state = START_MENU_STATE_RETURN;`); to start something, see how case 0
   runs a `menu` function ([party-menu-and-item-use.md §1](party-menu-and-item-use.md#what-the-menu-functions-do)).

An action that stays in the bag returns `BAG_STATE_INPUT` after redrawing (copy
`BagApp_ItemContextMenu_Deselect`), or prints with `BagApp_PrintMessage` and waits in a
state of its own. Only four entries plus CANCEL exist; a fifth needs a new window
(`dynWindows[13-16]`), a sprite, a touch rectangle (`sTouchHitboxes_ItemMenu`), a row in
`gBagAppItemMenuNavTable` and a cursor position.

### Change a pocket's capacity

1. `NUM_BAG_*` in `include/constants/items.h`. `bag.c`, `sPocketCounts` (`item.c`) and the
   `Bag` struct follow.
2. **`gPocketCapacities` and `gListPocketCapacities`** in
   [asm/bag_app_data.s:235](../../asm/bag_app_data.s#L235) are raw bytes (165, 40, 24, 101,
   64, 12, 30, 50) and don't follow. The screen reads names and draws pages up to these, so
   a bigger pocket shows only the old count. They are `u8`, and so are
   `BagViewPocket.itemCount` and `BagCursor` positions: stay at 255 or below.
3. Above 165 slots, also enlarge `BagApp.itemNames[165]` and `itemIds[165]`.
4. The battle bag copies items into `pocketItems[5][36]`
   ([battle_bag_menu.c:77](../../src/battle/battle_bag_menu.c#L77)) without a bounds check.
   More than 36 items of one battle page (for example a larger Medicine pocket full of
   HP restores) overflows it; raise 36 too.
5. **The save**: `SAVE_BAG` changes size and every later pocket moves, so old saves don't
   load ([save-compatibility.md §6](save-compatibility.md#6-when-the-layout-has-to-change)).

### Add, remove, rename or reorder a pocket

Renaming is text: the pocket description `msg_0010_00120`-`00127` (first line is the
name) and `msg_0226`. The tab itself is a picture in the archive (sprites 9-16); which
member draws which tab hasn't been traced.

Adding, removing or reordering is a large job. Everything below assumes 8 pockets in id
order:

- **Save and data**: the `Bag` struct, `POCKETS_COUNT`, the switches in `bag.c` (four of
  them), `sPocketCounts`, `gPocketCapacities`, `gListPocketCapacities`, `items.json`
  `fieldPocket` names (checked by `tools/pokedata/items.py`).
- **Views**: `BagView.pockets[8]`, `BagCursorField.scroll[8]` / `position[8]`, the pocket
  lists `sAllPockets` (launch_application.c), `sPockets` (start_menu.c),
  `sMartSellBagPockets` (shop_menu.c, written as 0-7), `gPCBoxBagPockets`
  (`asm/overlay_14_state_dispatch_rodata_67.s`, raw bytes without 5 = Mail).
- **The screen**, all with `8` or `< 8` / `<= 7` literals: loops in `bag_app.c` and
  `bag_app_display.c`, `BagApp_GetPocketNeighbor`, `BagApp_SetPocketIconsDrawFlag`
  (asserts `pocketId < 8`), `BagApp_LoadObjPaletteByPocket` / `BagApp_LoadBgPaletteByPocket`
  (one palette row per pocket in members 48 and 41), buttons 0-7 in
  `BagApp_HandleCursorAction`, the 8 tab rectangles of `sTouchHitboxes_Main` (32 pixels
  each across the 256-pixel screen: no room for a ninth), `gBagAppButtonNavTable` and
  `gBagAppCursorPositions` (every button number above 7 shifts), the tab sprites 9-16 in
  `gBagSpriteTemplates` and `BagApp.sprites[39]`.
- **The 3D model**: two animations per pocket per gender (`pocketAnims[8]`, members from
  `0x39` / `0x4C`) and the camera keys `gCameraTweenKeys[2][9]`. A new pocket needs new
  NSBCA/NSBTP animations, or reuse of an existing pocket's.
- **Text**: `msg_0010_00120 + pocket` assumes 8 descriptions in a row; `msg_0226`.
- **Elsewhere**: `FollowMonSituation_ConvertItemPocket`
  ([follow_mon_interaction.c:794](../../src/field/follow_mon_interaction.c#L794)), the
  `GetItemPocket` / `BufferPocketName` script commands, and the battle bag's walk over
  `POCKETS_COUNT` pockets.

Reordering only the tabs is not cheaper: the order on screen is the pocket id (the pocket
list's order is ignored, §2), so it means renumbering the ids and moving the per-pocket
graphics, palettes, animations and descriptions with them.

### Quantity and text

- **Quantity**: edit `BagApp_PrintItemNameAndMaybeQuantityOnWindow` (§3); key items
  already hide it. For other items, test before `PrintItemQuantityOnWindow`, for example
  `GetItemAttr(pocket->slots[index].id, ITEMATTR_PREVENT_TOSS, HEAP_ID_6)`. The toss and
  sell pickers show their own count.
- **Descriptions**: `"description"` in `items.json` ([items.md](items.md)). It is read into
  a 130-character `String` and printed in a window 32 tiles wide and 6 tall; keep to three
  lines.
- **Labels and messages**: `msg_0010.json`, ids as in the tables above. Labels are
  centred in their button (`BagApp_PrintContextMenuStringOnWindowCentered`) and nothing
  handles one wider than the button.

## 5. Pitfalls

- `mode` and `selectedAction` are bare numbers in several files; grep for
  `BagView_Init(` and `BagView_GetReturnCode(` before giving a number a new meaning.
- The capacity tables in `bag_app_data.s` are copies of the constants, and `pocketIndex` is
  always a pocket id (§2).
- The bag screen edits the save's pockets directly (`Pocket_TakeItem` on `pockets[].slots`)
  as soon as a toss or sale is confirmed; nothing is copied back on exit.
- The registered-item ids are not cleared when the item leaves the bag. Retail only lets
  key items be registered, and those can't be tossed or sold; a `selectable` item that can
  be tossed would stay registered.
- Mode 1 refuses Apricorn Balls, the Sport Ball and the Park Ball as held items, and mode 0
  never offers GIVE for them (`ItemIdIsNotJohtoBall`).
- Berries can't be planted from the bag: `Leftover_CanPlantBerry` returns FALSE; planting
  happens in the Berry Pots (mode 6).

## Where to look

| What | File |
|---|---|
| `Bag`, `BagView`, `BagViewPocket`, `ItemCheckUseData` | [include/bag_types_def.h](../../include/bag_types_def.h) |
| add / take / sort / register, `Bag_CreateView`, `BagCursor` functions | [src/bag.c](../../src/bag.c) |
| `BagView_*` setters and getters, key-item messages, use-error messages | [src/bag_view.c](../../src/bag_view.c) |
| pocket ids and sizes | [include/constants/items.h](../../include/constants/items.h) |
| the screen: states, input, item menu, use, toss, sell, 3D; `BagApp` in [bag_app.h](../../include/application/bag/bag_app.h) | [src/application/bag/bag_app.c](../../src/application/bag/bag_app.c) |
| windows, item list, labels, sprites | [src/application/bag/bag_app_display.c](../../src/application/bag/bag_app_display.c) |
| action table, capacities, hitboxes, navigation, sprite templates | [asm/bag_app_data.s](../../asm/bag_app_data.s) |
| launching from the field, the script select | [src/launch_application.c](../../src/launch_application.c) |
| what happens with the return code | [src/start_menu.c](../../src/start_menu.c) (`Task_StartMenu_HandleReturn`) |
| selling | [src/overlay_03/shop_menu.c](../../src/overlay_03/shop_menu.c), [src/mart_bag_task.c](../../src/mart_bag_task.c) |
| Berry Pots, PC | [src/berry_pots.c](../../src/berry_pots.c), [src/application/pc_box/pc_box_ui.c](../../src/application/pc_box/pc_box_ui.c) |
| battle bag | [src/battle/battle_bag_menu.c](../../src/battle/battle_bag_menu.c) |
| `MoveItemSlotInList`, `sPocketCounts`, `ItemIdIsNotJohtoBall` | [src/item.c](../../src/item.c) |
| text | [files/msgdata/msg/msg_0010.json](../../files/msgdata/msg/msg_0010.json) |
