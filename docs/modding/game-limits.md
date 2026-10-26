<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# Game limits and rules in C

> AI-generated; not affiliated with pret. See AI.md at the repository root.

Numbers the game's rules depend on, and where they're defined. Most were bare
literals in `src/`; they now use these names (same values, ROM unchanged), so
changing one place changes every use. Some are also limits of save data or file
formats: raising those needs more than editing the constant.

| Constant | Value | Header | Meaning |
|---|---|---|---|
| `MAX_LEVEL` | 100 | `constants/pokemon.h` | level cap (caps by badge count: [experience.md](experience.md#8-recipe-level-caps-by-badge-count)) |
| `MAX_MON_MOVES` | 4 | `constants/pokemon.h` | move slots (save format) |
| `PARTY_SIZE` | 6 | `constants/global.h` | party slots (save format) |
| `MAX_PER_STAT_IVS` / `MAX_IV_MASK` | 31 / 0x1F | `constants/pokemon.h` | IV cap / one IV in the packed IV word |
| `USE_RANDOM_IVS` | 32 | `constants/pokemon.h` | `CreateMon(..., fixedIV)`: roll random IVs |
| `MAX_EV_PER_STAT` / `MAX_EV_SUM` | 255 / 510 | `constants/pokemon.h` | EV caps |
| `FRIENDSHIP_MAX`, `FRIENDSHIP_TIER_MID_MIN`, `FRIENDSHIP_TIER_HI_MIN` | 255, 100, 200 | `constants/pokemon.h` | friendship cap and tiers (vitamins, Return/Frustration, follower moods) |
| `NATURE_NUM` | 25 | `constants/pokemon.h` | natures (personality % 25) |
| `MIN_STAT_STAGE`, `DEFAULT_STAT_STAGE`, `MAX_STAT_STAGE` | 0, 6, 12 | `constants/pokemon.h` | battle stat stages (-6..+6) |
| `MAX_EVOS_PER_POKE` | 7 | `pokemon_types_def.h` | evolutions per species |
| `MAX_LEARNED_MOVES` | 22 | `constants/pokemon.h` | level-up learnset buffer (21 moves + end) |
| `MAX_EGG_MOVES` | 16 | `constants/daycare.h` | egg moves per species |
| `EGG_MOVES_TABLE_SIZE` | 2045 | `constants/daycare.h` | egg move table entries searched (`egg_moves.json` is full) |
| `EGG_HATCH_LEVEL`, `EGG_HATCH_FRIENDSHIP` | 1, 120 | `constants/daycare.h` | hatched mon's level and friendship |
| `EGG_CYCLE_STEPS`, `EGG_CYCLE_STEPS_SPECIAL_DAY` | 255, 230 | `constants/daycare.h` | steps per egg cycle (special dates in `sEggCycleSpecialDates`) |
| `DAYCARE_BREED_CHECK_STEPS` | 255 | `constants/daycare.h` | steps between egg rolls (chance: `PARENTS_*_COMPATIBILITY`) |
| `DAYCARE_PRICE_PER_LEVEL` | 100 | `constants/daycare.h` | daycare fee per level gained (+1) |
| `MASUDA_METHOD_REROLLS` | 4 | `constants/daycare.h` | extra shiny rolls for foreign parents |
| `EGG_NATURE_PID_ATTEMPTS` | 2400 | `constants/daycare.h` | Everstone nature-matching attempts |
| `NUM_BOXES`, `MONS_PER_BOX` | 18, 30 | PC storage headers | PC size (save format) |
| `BATTLER_MAX` | 4 | `constants/battle.h` | battlers in a double battle |

## Money, coins and the bag

| Constant | Value | Header | Meaning |
|---|---|---|---|
| `MAX_MONEY` | 999999 | `player_data.h` | wallet cap (`PlayerProfile.money`, `u32`) |
| `MOMS_BALANCE_MAX` | 999999 | `save_pokegear.h` | Mom's savings cap (`bankBalance`, `u32`) |
| `MAX_COINS` | 50000 | `coins.h` | Coin Case cap (`PLAYERDATA.coins`, `u16`) |
| `BAG_SLOT_QUANTITY_MAX` | 999 | `constants/items.h` | stack size, every pocket except TMs/HMs |
| `BAG_TMHM_QUANTITY_MAX` | 99 | `constants/items.h` | stack size in the TM/HM pocket |
| `NUM_BAG_ITEMS` | 165 | `constants/items.h` | Items pocket slots |
| `NUM_BAG_MEDICINE` | 40 | `constants/items.h` | Medicine pocket slots |
| `NUM_BAG_BALLS` | 24 | `constants/items.h` | Poké Balls pocket slots |
| `NUM_BAG_TMS_HMS` | 101 | `constants/items.h` | TMs & HMs pocket slots |
| `NUM_BAG_BERRIES` | 64 | `constants/items.h` | Berries pocket slots |
| `NUM_BAG_MAIL` | 12 | `constants/items.h` | Mail pocket slots |
| `NUM_BAG_BATTLE_ITEMS` | 30 | `constants/items.h` | Battle Items pocket slots |
| `NUM_BAG_KEY_ITEMS` | 50 | `constants/items.h` | Key Items pocket slots |

**Money.** `PlayerProfile_SetMoney` / `PlayerProfile_AddMoney`
([player_data.c:166](../../src/player_data.c#L166)) clamp to `MAX_MONEY`;
`PlayerProfile_SubMoney` floors at 0. Script `AddMoney` / `SubMoneyImmediate` /
`HasEnoughMoneyImmediate` take a `u32`; the `...Var` forms read a 16-bit var, so
they can't pass more than 65535. Mom's bank (`ScrCmd_BankTransaction`,
[scrcmd_c.c:5060](../../src/scrcmd_c.c#L5060)) limits a deposit or withdrawal so
neither side passes `MAX_MONEY`, and `BankOrWalletIsFull` compares against it.

**Coins.** `Coins_Add` ([coins.c:13](../../src/coins.c#L13)) refuses only when
the case is already at `MAX_COINS`, then clamps. The total is a `u16`, so an add
that goes past 65535 wraps before the clamp (49000 + 20000 gives 3464). Check
first with `CheckGiveCoins` (`Coins_CanAdd`) when a script gives a large amount;
`GiveCoins` / `TakeCoins` take a 16-bit value.

**Bag.** Each item gets one slot, and the stack cap is checked when adding
(`Pocket_GetItemSlotForAdd`, [bag.c:110](../../src/bag.c#L110)): if the new
total would pass the cap, or there's no stack and no empty slot, `Bag_AddItem`
and `Bag_HasSpaceForItem` return FALSE and nothing is added (no partial add).
Which pocket an item goes in comes from its item data (`ITEMATTR_FIELD_POCKET`); the
pocket sizes are listed again in `sPocketCounts` ([item.c:20](../../src/item.c#L20))
and the switches in `bag.c`, all using the names above. Shops cap one purchase
at 99 and at what the player can afford (`shop_menu.c:746`) and then call
`Bag_HasSpaceForItem`.

**Changing them.**

- Pocket sizes and the `Bag` struct (`bag_types_def.h`) are saved, so changing a
  `NUM_BAG_*` value changes the save layout (see
  [save-compatibility.md](save-compatibility.md)).
- Storage widths: `ItemSlot.quantity` is a `u16` (stack up to 65535), coins a
  `u16`, money and Mom's savings a `u32`. Staying inside those keeps the save
  layout.
- Display widths: the money box prints 6 digits
  ([script_menu.c:702](../../src/field/script_menu.c#L702)), the coin/points box
  5, and the Bag app quantities 3 (`bag_app.c`, `bag_app_display.c`). Raise a cap
  past those and widen the matching `BufferIntegerAsString` call (and check the
  window fits).
- Copies still written as literals: `999999` for Mom's savings in
  `battle_setup.c:245` (prize money stops going to Mom when her balance is
  full), `50000` in Voltorb Flip (`voltorb_flip.c:598`, `:1360`, `:1365-1366`; its
  "You've gathered 50,000 Coins" message is text), and the shop's 99. Change
  those with the constant.

## Other literals

Still literals (candidates for names): badge counts (16/8), Unown forms (28),
obedience level caps by badge, Battle Frontier caps (9999) and level modes
(50/100, sentinels 120/121), max PP Ups (3), apricorn cap (99). The accuracy
table `sHitChanceTable[13]` (`src/battle/battle_controller_player.c`) has one row
per stat stage, so changing the stage range means editing it too.
