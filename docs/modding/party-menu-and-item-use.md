<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# The party menu and using items

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers what happens when an item is used and where each kind of effect is
coded: from the bag in the field, on a Pokémon through the party menu, from the bag in
battle, and as a held item. [items.md](items.md) covers the item data these read
(`items.json`: `fieldUseFunc`, `partyUseParam`, `holdEffect`...). This guide is the code
behind it.

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `ItemId_GetFieldFunc` → `ItemUseOutOfBattle_*` | `fieldUseFunc` → a row of `sItemFieldUseFuncs` with three functions (§1) |
| `ItemUseCB_Medicine`, `ExecuteTableBasedItemEffect` | the party menu picks an animation, then `UseItemOnPokemon` applies the effects (§3) |
| `CB2_PartyMenu`, `gPartyMenu.menuType` | the party menu application, opened with a **context** (§2) |
| `ItemId_GetBattleFunc`, `ItemUseInBattle_*` | the battle bag page, `BattleSystem_RecoverStatus` (§4) |
| `ItemBattleEffects(ITEMEFFECT_*)` | a set of held-item functions in `battle_util.c`, each called at its point in the turn (§5) |

The main point: **the same item data is applied by three separate pieces of code.**

- `UseItemOnPokemon` ([src/use_item_on_mon.c](../../src/use_item_on_mon.c)) applies it in
  the field.
- `BattleSystem_RecoverStatus` ([src/battle/battle_system.c](../../src/battle/battle_system.c))
  applies it in battle.
- The battle engine's held-item functions apply `holdEffect`.

A new effect has to be added to each one that should do it.

## 1. Using an item from the bag in the field

`fieldUseFunc` picks a row of `sItemFieldUseFuncs` in
[src/field_use_item.c](../../src/field_use_item.c). A row has three functions, any of which
can be `NULL`:

| Slot | Type | Called | Job |
|---|---|---|---|
| `check` | `ItemCheckUseFunc` | when "Use" is chosen, in the bag (`BagApp_ItemContextMenu_Use`), and when the registered (Y) item is used | returns `ITEMUSEERROR_OKAY` (0) or an error, which the bag prints (`GetItemUseErrorMessage`, mostly "Oak's words echoed...") |
| `menu` | `ItemMenuUseFunc` | after the bag closes, by the start menu (`Task_StartMenu_HandleReturn`, [src/start_menu.c](../../src/start_menu.c)) | the actual use from the bag: open the party menu, start a field task, launch an app |
| `field` | `ItemFieldUseFunc` | when the item is registered to Y and used from the overworld (`UseRegisteredItemButtonInField`) | the same use without the bag. Returns `TRUE` if it started something |

The check gets an `ItemCheckUseData` (map, player state, facing tile, whether a follower or
the Rocket disguise is active) filled by `ItemCheckUseData_Init`. The check functions use
it to refuse a Bicycle indoors or a rod away from water.

### The full sequence

1. The player picks "Use". The bag runs `check`. On an error it prints the message and
   stays open.
2. `BagApp_UseItem` ([src/application/bag/bag_app.c](../../src/application/bag/bag_app.c))
   handles a few items **inside the bag**, before it closes:

   | Items | Handled by |
   |---|---|
   | TMs and HMs | `BagApp_UseTMHM` runs first; then the `TMHM` menu function opens the party menu |
   | Point Card, Seal Case, Fashion Case, Coin Case | `TryFormatRegisteredKeyItemUseMessage` ([src/bag_view.c](../../src/bag_view.c)) prints their message |
   | Repel, Super Repel, Max Repel, Black Flute, White Flute, GB Sounds | `BagApp_TryUseItemInPlace`. A Repel's step count is its `holdEffectParam` |

3. Otherwise the bag closes with return code 0, and the start menu calls the row's `menu`
   function with the item and the party slot.

So `ITEM_FIELD_USE_GENERIC` (Repels, flutes, cases) has no `menu` function. Its effect is
the in-bag handling in step 2, which **tests item ids**. A new Repel-like item needs its id
added to `BagApp_TryUseItemInPlace` as well as `fieldUseFunc`.

### What the menu functions do

| `fieldUseFunc` | `menu` function does |
|---|---|
| `HEALING` | opens the party menu with `PARTY_MENU_CONTEXT_USE_ITEM` (§3) |
| `EVO_STONE` | the party menu with `PARTY_MENU_CONTEXT_EVO_STONE` (and the Water Stone puzzle in the Ruins of Alph) |
| `TMHM` | the party menu with `PARTY_MENU_CONTEXT_TM_HM` |
| `MAIL` | the mail compose screen (`UseMail_LaunchApp_Compose`) |
| `BERRY` | the same as `HEALING` (`ItemMenuUseFunc_Berry` calls it). Berries can't be planted in the field: `Leftover_CanPlantBerry` always says no; they go in the Berry Pots |
| `BICYCLE`, rods, `ESCAPE_ROPE`, `HONEY` | start a field task (mount the bike, cast the rod, warp out) |
| `PAL_PAD`, `APRICORN_BOX`, `BERRY_POTS`, `UNOWN_REPORT`, `DOWSING_MCHN`, `VS_RECORDER`, `GRACIDEA` | launch their application |

The menu functions are called from the start menu's field task, so they launch things the
same way as any field code ([engine.md §4](engine.md#4-field-tasks),
[ui.md](ui.md#launching-an-application)). They store the next step in the start menu's
`exitTaskFunc` (`StartMenu_SetExitTaskFunc`), which runs when the launched screen closes.

### Adding a new kind of field use

1. A constant `ITEM_FIELD_USE_X` in `include/constants/items.h`, before the count.
2. A row in `sItemFieldUseFuncs`, at that index.
3. The functions: `check` if it can't be used everywhere, `menu` for using it from the
   bag, `field` if it can be registered (`"selectable": true` in `items.json`).
4. `"fieldUseFunc": "ITEM_FIELD_USE_X"` on the item.

`ItemCheckUseFunc_Dummy` (always refuses) is what the Sinnoh leftovers use. Copy
`ItemMenuUseFunc_HealingItem` for "pick a Pokémon".

## 2. The party menu

The party menu is an application, `gOverlayTemplate_PartyMenu` in
[src/party_menu.c](../../src/party_menu.c). It is in static ARM9 (no overlay), with its own
0x30000-byte heap (`HEAP_ID_PARTY_MENU`). Whoever opens it fills a `PartyMenuArgs`
([include/party_menu.h](../../include/party_menu.h)):

| Field | In / out | Meaning |
|---|---|---|
| `party`, `bag`, `mailbox`, `options`, `fieldSystem` | in | where to read and write |
| `context` | in | **why it was opened**: decides the prompt, which Pokémon can be picked, what picking one does |
| `itemId` | in | the item being used or given |
| `partySlot` | in / out | the starting cursor; the Pokémon picked |
| `fieldMoveCheckData` | in | for the field-move entries in the context menu |
| `minMonsToSelect`, `maxMonsToSelect`, `maxLevel` | in | for "choose N Pokémon" contexts (link battles, the Battle Frontier) |
| `selectedAction` | out | **what the player chose**: `PARTY_MENU_ACTION_RETURN_*` |
| `selectedMoveIdx`, `species`, `evoMethod` | out | the move picked (PP items, TMs); what to evolve into |

Some contexts:

| Context | Opened by |
|---|---|
| `PARTY_MENU_CONTEXT_0` | the start menu's "Pokémon" (`PartyMenu_LaunchApp_Field`) |
| `PARTY_MENU_CONTEXT_USE_ITEM` | a healing item from the bag |
| `PARTY_MENU_CONTEXT_TM_HM`, `_EVO_STONE` | TMs, evolution stones |
| `PARTY_MENU_CONTEXT_9` | "Give" from the bag |
| `PARTY_MENU_CONTEXT_REPLACE_MOVE_TMHM`, `_REPLACE_MOVE_LEVELUP` | choosing a move to forget |
| `PARTY_MENU_CONTEXT_INGAME_TRADE`, `_SPIN_TRADE`, `_BATTLE_HALL`, `_UNION_ROOM_BATTLE_SELECT`, `_ATTACH_CAPSULE` | the screens they are named after |

Many are still numbers. `grep -rn 'context = PARTY_MENU_CONTEXT_' src` shows who opens each.

### The context menu and the return value

In the plain context, picking a Pokémon opens a context menu (`PartyMonContextMenuItem`:
Summary, Switch, Item, Mail, and one entry per field move the Pokémon knows). Its actions
are in [src/party_menu_list_items.c](../../src/party_menu_list_items.c) and
[src/party_context_menu.c](../../src/party_context_menu.c). Most don't do the work
themselves. They set `args->selectedAction` and close the menu, and the caller acts on it.
For the start menu that is `Task_StartMenu_HandleReturn_Pokemon` in
[src/start_menu.c](../../src/start_menu.c):

| `selectedAction` | The start menu then |
|---|---|
| `PARTY_MENU_ACTION_RETURN_1`, `_4` | opens the summary screen |
| `_5` | opens the summary screen to learn or forget a move |
| `_6` | opens the mail compose screen |
| `_READ_MAIL` | opens the mail |
| `_EVO_ITEM_USE`, `_EVO_RARE_CANDY` | plays the evolution scene (`START_MENU_STATE_EVOLUTION`) |
| `_CUT` ... `_HEADBUTT` | runs the field move's `use` function |

**Field moves.** The entries come from `sFieldMoves` in `party_menu.c` (Cut, Fly, Surf,
Strength, Rock Smash, Waterfall, Rock Climb, Whirlpool, Flash, Teleport, Dig, Sweet Scent,
Chatter, Headbutt, Milk Drink, Softboiled). When one is picked, its `check` function
(`sFieldMoveFuncTable` in [src/field_move.c](../../src/field_move.c)) decides whether it
can be used here. The result is OK, not here, need badge, follower, already surfing or not
now. On OK the menu closes, and the start menu calls the matching `use` function. Milk
Drink and Softboiled stay inside the party menu (`PARTY_MENU_STATE_SOFTBOILED`).

To add a field move, all of these must agree:

- `sFieldMoves`;
- `PartyMonContextMenuItem` and its string;
- a context-menu action that sets `selectedAction`;
- `PartyMenuActionReturn`;
- the start menu's `switch`;
- a `{ use, check }` row in `sFieldMoveFuncTable`.

[tms-and-hms.md](tms-and-hms.md#6-adding-a-field-move) adds one step by step.

**The lists are not in the same order.** Whirlpool comes before Flash in `sFieldMoves` and
`PartyMonContextMenuItem`, but after Chatter in `PartyMenuActionReturn` and
`sFieldMoveFuncTable`. The start menu indexes the function table by
`selectedAction - PARTY_MENU_ACTION_RETURN_FIELD_MOVE_BEGIN`, so that table must follow
`PartyMenuActionReturn`.

## 3. Using an item on a Pokémon (field)

With `PARTY_MENU_CONTEXT_USE_ITEM`, picking a Pokémon runs `PartyMenu_HandleUseItemOnMon`
([src/party_menu.c](../../src/party_menu.c)):

1. **Gracidea** on a Shaymin that can change: the form change scene.
2. **PP Up, PP Max**, or a PP item for **one move**: choose a move first
   (`PartyMenu_SelectMoveForPpRestoreOrPpUp`), then apply.
3. Otherwise **`CanUseItemOnMonInParty`** asks whether the item would do anything:
   - **No:** "It won't have any effect." The item is kept.
   - **Yes:** the item is **removed from the bag first** (`Bag_TakeItem`). Then:
     - an evolution item returns `PARTY_MENU_ACTION_RETURN_EVO_ITEM_USE` and the caller
       evolves the Pokémon;
     - anything else gets an animation and message chosen by
       `PartyMenu_SetItemUseFuncFromBagSelection`
       ([src/party_menu_items.c](../../src/party_menu_items.c)). That callback calls
       **`UseItemOnMonInParty`**, which applies the effects.

### What decides what

Two functions read the same `partyUseParam` flags, for two different jobs:

| Function | File | Decides |
|---|---|---|
| `CanUseItemOnPokemon` | `use_item_on_mon.c` | whether **any** flag would change this Pokémon: a status it has, HP below max, EVs below the cap, a level below 100... |
| `UseItemOnPokemon` | `use_item_on_mon.c` | applies **every** flag that applies; returns whether anything changed |
| `ItemId_GetPartyUseType` | `party_menu_items.c` | which **one** animation and message the party menu shows |

`ItemId_GetPartyUseType` checks in a fixed order and returns the first match:

1. battle stat stages;
2. Sacred Ash (`revive_all`);
3. Rare Candy (`level_up`);
4. exactly one status cure, or all six (Full Heal, or Full Restore if it also restores HP);
5. infatuation;
6. HP restore;
7. each EV, up or down;
8. evolve;
9. PP Up, PP Max, PP restore.

The order has consequences when you combine effects:

- **An item with several effects shows one message.** For example, one that cures
  paralysis and raises Speed EVs gets the paralysis animation and text, but both effects
  are applied.
- **Two status cures that aren't all six** (sleep and paralysis, say) match none of the
  single-status cases. Such an item falls through to a later category, or to none.
- **An item that matches no category gets no callback.** Its type is
  `PARTY_MENU_ITEM_TYPE_OTHER`, so the party menu sets no follow-up for it, and the item is
  taken from the bag first. Give a new item at least one effect from the list above, or add
  a case to `PartyMenu_SetItemUseFuncFromBagSelection`.

**Effects that do nothing in the field.** `cfs_heal`, `inf_heal`, `guard_spec` and the
`*_stages` keys only mean something to a Pokémon in battle (confusion and infatuation
aren't stored on a party Pokémon). `CanUseItemOnPokemon` ignores them. An item with only
those effects is refused outside battle.

**Friendship.** `friendship_mod_lo`, `_med` and `_hi` apply on top of any other effect, by
the Pokémon's current friendship (`DoItemFriendshipMod`). The Luxury Ball and the Soothe
Bell (`HOLD_EFFECT_FRIENDSHIP_UP`) increase a gain. There is a further bonus when the
`location` argument (the current map section) equals the Pokémon's stored
`MON_DATA_EGG_LOCATION`. `CanUseItemOnPokemon` doesn't look at friendship, so an item whose
only effect is friendship is refused.

**Rare Candy** (`level_up`) runs a longer sequence in the party menu
(`PartyMenu_ItemUseFunc_LevelUp`): the level-up, learning moves (with the forget-a-move
prompt), then `PARTY_MENU_ACTION_RETURN_EVO_RARE_CANDY` if the Pokémon can evolve.

## 4. Using an item in battle

The battle bag is in `OVY_8`, with the in-battle party screen
([battle-engine.md §1](battle-engine.md#1-where-the-code-is)). It is the client side: it
runs on the player's DS, and only its result goes to the battle server
([battle-engine.md §3](battle-engine.md#3-the-server-and-the-clients)).

**The page decides what happens, not `battleUseFunc`.** The bag has pages, set by each
item's `battlePocket`, and `BattleBagMenu_TryUseItem`
([src/battle/battle_bag_menu.c](../../src/battle/battle_bag_menu.c)) treats each page
differently:

| Page | What happens |
|---|---|
| HP/PP restore, status restore | the battle party screen opens to choose a Pokémon ([src/battle/battle_party_menu.c](../../src/battle/battle_party_menu.c)). There `BattleSystem_RecoverStatus` applies the item and the bag takes it |
| Battle items (X items, Guard Spec., Poké Doll) | applied to the Pokémon in battle at once with `BattleSystem_RecoverStatus`. If that does nothing and `battleUseFunc` is `ITEM_BATTLE_USE_ESCAPE`, the item is used up to flee (wild battles only). Embargo blocks this page, except Guard Spec. and escape items |
| Poké Balls | refused with two targets, a target that is underground or in the air, or behind a Substitute, or with a full party and PC. Otherwise the server throws it |

`battleUseFunc` is read **only** for `ITEM_BATTLE_USE_ESCAPE`, on the battle-items page.
`_BALL` and `_RESTORE` are not read anywhere; the page alone decides.

Then the client replies to the server with the item, page and target
(`BattleController_EmitSelectedBagItem`). On its turn, the server's `ItemInput` command
([src/battle/battle_controller_player.c](../../src/battle/battle_controller_player.c))
picks a subscript:

| Page | Subscript | Does |
|---|---|---|
| restore pages, battle items | `BATTLE_SUBSCRIPT_BATTLE_ITEM` | nothing (`End`): the effect and its message already happened in the bag |
| battle items, if the item **is** the Poké Doll or Fluffy Tail | `BATTLE_SUBSCRIPT_ESCAPE_ITEM` | flee |
| Poké Balls | `BATTLE_SUBSCRIPT_THROW_POKEBALL` | "X used one Y!", the throw, the catch. The ball is taken from the bag here |

The escape case tests **item ids**. A new escape item with
`battleUseFunc: ITEM_BATTLE_USE_ESCAPE` is used up by the bag, but the server runs the
empty `BATTLE_ITEM` script and the battle goes on. Add its id next to `ITEM_POKE_DOLL` in
`BattleControllerPlayer_ItemInput` too.

**Catch rates per ball** are in `BattleSystem_CalculateBallShakes`
([src/battle/battle_command.c](../../src/battle/battle_command.c)), a `switch` on the ball's
item id. A new ball needs a case there. Its graphics and throw animation are separate, and
this guide doesn't cover them.

### `BattleSystem_RecoverStatus`

[src/battle/battle_system.c](../../src/battle/battle_system.c) is the battle's version of
`UseItemOnPokemon`. It changes the party Pokémon and, if that Pokémon is on the field, its
`BattleMon` too. It handles:

- the status cures, including confusion and infatuation;
- Guard Spec. and the `*_stages` keys (on the battler);
- PP restore;
- HP restore and revive;
- the friendship change.

It does **not** handle EVs, `level_up`, `evolve`, `pp_up` or `pp_max`. Those items have no
battle pocket, and giving one a battle pocket won't make them work.

**Trainers' items** take a different path. The AI chooses an item and a kind (Full Restore,
potion, status, X item, Guard Spec., [trainers.md](trainers.md#items-in-battle)).
`ItemInput` runs the matching subscript (`subscript_0267_PotionItem.s` and so on), which
prints "Trainer used one X!" and then the `UseBagItem` script command. That command calls
`BattleSystem_RecoverStatus` for the trainer's Pokémon.

## 5. Held items

`holdEffect` and `holdEffectParam` are read through two lookups. In battle,
`GetBattlerHeldItemEffect(ctx, battler)` and `GetHeldItemModifier` read the item data,
which the battle loads into memory once (`GetItemVar`). Outside battle the code calls
`GetItemAttr(item, ITEMATTR_HOLD_EFFECT, heapID)`.

`GetBattlerHeldItem` returns `ITEM_NONE` under **Klutz** or **Embargo**, so use the
`GetBattlerHeldItemEffect` path, not `battleMons[b].item`, for effects those should block.

### Where each kind acts in battle

All in `src/battle/` unless noted. The steps are the server's commands
([battle-engine.md §4](battle-engine.md#4-the-turn-controller-commands)).

| Kind | Function (when) | Examples |
|---|---|---|
| damage boosts | `CalcMoveDamage` (`battle_util.c`) and its `sTypeEnhancingItems` table | Charcoal, Mystic Water and the other type items, plates, Choice Band/Specs, Muscle Band, Wise Glasses, Light Ball, Thick Club, DeepSeaTooth/Scale, Soul Dew, Metal Powder, the Adamant/Lustrous/Griseous Orbs |
| damage multipliers after the formula | `DamageCalcDefault` (`battle_command.c`) | Life Orb's boost, Metronome |
| type effectiveness | `BattleSystem_ApplyTypeEffectiveness` | Expert Belt (`HOLD_EFFECT_POWER_UP_SE`), Iron Ball grounding |
| speed and turn order | `CheckSortSpeed` | Quick Claw (`SOMETIMES_PRIORITY`), Custap Berry (`PINCH_PRIORITY`), Choice Scarf, Lagging Tail and Full Incense (`SPEED_DOWN`), Quick Powder |
| accuracy, critical hits | `BattleSystem_CheckMoveHit` (`battle_controller_player.c`), `TryCriticalHit` | BrightPowder and Lax Incense (`ACC_REDUCE`), Wide Lens (`ACCURACY_UP`), Zoom Lens (`CRITRATE_UP_SLOWER`); Scope Lens, Razor Claw, Lucky Punch, Stick |
| type and move type | `Battler_GetType`, `GetDynamicMoveType` | plates (Arceus's type, Judgment's type) |
| Ground immunity, trapping | `CheckFlyingImmunity`, `CantEscape`, `BattlerCanSwitch` | Iron Ball (`SPEED_DOWN_GROUNDED`), Shed Shell (`HOLD_EFFECT_SWITCH`) |
| berries and healing items when HP is low or a status appears | `TryUseHeldItem`, `CheckUseHeldItem` (after a hit: `AfterMoveEffects`, 31; at end of turn: `UpdateMonCondition`) | Sitrus, Oran, status berries, pinch berries, Mental Herb, White Herb |
| end of turn | `CheckItemGradualHPRestore`, `TryHeldItemNegativeEffect` (`UpdateMonCondition`) | Leftovers, Black Sludge; Toxic Orb, Flame Orb, Sticky Barb |
| when hit | `CheckItemEffectOnHit` (31, and the `CheckItemHoldEffectOnHit` script command) | Enigma Berry, Jaboca/Rowap Berry, Sticky Barb passing over |
| after the move | `BattleControllerPlayer_TryAfterMoveItems` (37) | Shell Bell, Life Orb recoil |
| flinch | `TryItemFlinch` (29) | King's Rock, Razor Fang |
| survive a hit | `BtlCmd_CheckHoldOnWith1HP` | Focus Band, Focus Sash |
| locked moves | `BattleControllerPlayer_UpdateMoveHistory`, `StruggleCheck`, `BtlCmd_TryPursuit` | Choice items |
| screens | `BtlCmd_TryReflect`, `BtlCmd_TryLightScreen` | Light Clay |
| escaping a wild battle | `CantEscape`, `BattleTryRun` | Smoke Ball (`HOLD_EFFECT_FLEE`) |
| prize money | `TryAbilityOnEntry` (`battle_util.c`) notes the holder when it comes out | Amulet Coin, Luck Incense (`HOLD_EFFECT_MONEY_UP`) |
| after a KO | `Task_GetExp`, `BtlCmd_CalcExpGain`, `BattleScript_CalcEffortValues` (`battle_command.c`) | Exp. Share, Lucky Egg, Macho Brace and the Power items |

To find every place an existing effect is handled: `grep -rn HOLD_EFFECT_X src`. The
numbers are in `include/constants/items.h` (`HOLD_EFFECT_*`).

### Outside battle

| Effect | Where |
|---|---|
| Everstone (`HOLD_EFFECT_NO_EVOLVE`) | evolution checks in `src/pokemon.c` |
| Soothe Bell (`HOLD_EFFECT_FRIENDSHIP_UP`) | friendship changes in `pokemon.c`, `use_item_on_mon.c`, `scrcmd_party.c` |
| Arceus plates | its type and form, `pokemon.c` |
| Cleanse Tag, Pure Incense | `src/field/encounter_check.c`, **by item id** |
| incense breeding | `src/get_egg.c`, by item id |

**Cleanse Tag and Pure Incense are tested by id**, not by `HOLD_EFFECT_ENCOUNTERS_DOWN`.
Nothing reads that constant. A new item with that hold effect does nothing in the field
until its id is added to `encounter_check.c`.

### Adding a hold effect

1. `#define HOLD_EFFECT_X n` in `include/constants/items.h` (the next free number).
2. `"holdEffect": "HOLD_EFFECT_X"` and `"holdEffectParam"` on the item in `items.json`.
3. Code at the point in the table above where the effect should happen, copying the
   nearest existing item. Read the parameter with `GetHeldItemModifier`.
4. If it needs a message, a subscript ([abilities.md](abilities.md#when-you-need-your-own-message-or-script)
   describes how; held items use the same mechanism).
5. The AI won't know about it unless you add it to `trainer_ai.c`.

## Where to look

| To change | Look in |
|---|---|
| whether an item can be used here | its `check` function in `sItemFieldUseFuncs` (`field_use_item.c`) |
| what "Use" does from the bag | its `menu` function; Repels, flutes and cases in `BagApp_TryUseItemInPlace` and `TryFormatRegisteredKeyItemUseMessage` |
| what using it from Y does | its `field` function; `UseRegisteredItemButtonInField` |
| whether a medicine works on a Pokémon | `CanUseItemOnPokemon` |
| what it does to the Pokémon (field) | `UseItemOnPokemon` |
| the message and animation in the party menu | `ItemId_GetPartyUseType`, `PartyMenu_GetItemUseMessage` (`party_menu_items.c`) |
| what it does in battle | `BattleSystem_RecoverStatus` (`battle/battle_system.c`) |
| which battle bag page it is on, and what that page does | `battlePocket`; `BattleBagMenu_TryUseItem` |
| a ball's catch rate | `BattleSystem_CalculateBallShakes` |
| a held item | §5 |
| a field move in the party menu | `sFieldMoves` (`party_menu.c`), `sFieldMoveFuncTable` (`field_move.c`) |
| what happens after the party menu closes | `Task_StartMenu_HandleReturn_Pokemon` (`start_menu.c`) |
