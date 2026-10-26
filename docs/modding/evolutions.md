<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Evolutions and evolution methods

> AI-generated; not affiliated with pret. See AI.md at the repository root.

To change **which** species evolves into what, and how, edit `evo.json`
([pokemon.md](pokemon.md#evolutions)). This guide covers what each method does, when the
game checks them, and how to **add a new method**.

A method is a number. `evo.json` stores it with a parameter and a target species. One C
function, `GetMonEvolution` (`src/pokemon.c`), decides whether a Pokémon evolves. Adding
a method means adding a constant, a `case` in that function, and (sometimes) an effect
after the evolution.

| pokeemerald | here |
|---|---|
| `EVO_*` in `include/constants/pokemon.h` | `enum EvoMethod` in `include/constants/pokemon.h` |
| `gEvolutionTable` in `src/data/pokemon/evolution.h` | `files/poketool/personal/evo.json` (built into `evo.narc`) |
| `GetEvolutionTargetSpecies` (`src/pokemon.c`) | `GetMonEvolution` (`src/pokemon.c`) |
| `EVO_MODE_NORMAL`, `_TRADE`, `_ITEM_USE`, `_ITEM_CHECK` | `EVOCTX_LEVELUP`, `_TRADE`, `_ITEM_USE`, `_ITEM_CHECK` |
| Shedinja in `src/evolution_scene.c` | `EvolutionScene_ApplyEvolutionEffects` (`src/evolution_scene.c`) |

## The data

`files/poketool/personal/evo.json`, one entry per species:

```json
{ "baseSpecies": "SPECIES_EEVEE",
  "evos": [
    { "method": "EVO_STONE", "param": "ITEM_THUNDERSTONE", "target": "SPECIES_JOLTEON" },
    { "method": "EVO_FRIENDSHIP_DAY", "param": 0, "target": "SPECIES_ESPEON" },
    ...
  ] }
```

The template `evo.json.txt` turns each entry into a C struct and compiles it into one file
of `evo.narc` per species:

```c
struct Evolution {   // include/struct_defs/personal_narc_structs.h
    u16 method;
    u16 param;
    u16 target;
};
#define MAX_EVOS_PER_POKE 7
```

- At most **7** evolutions per species. Raising `MAX_EVOS_PER_POKE` changes the file size
  that `LoadMonEvolutionTable` reads. Change it in both headers that define it
  (`include/struct_defs/personal_narc_structs.h` and `include/pokemon_types_def.h`).
- `method`, `param` and `target` are `u16`. `param` can be a number or any constant from
  the headers that `evo.json.txt` includes (`species.h`, `moves.h`, `items.h`,
  `pokemon.h`). To use constants from another header, add its `#include` to the template.
- Unused slots are zero, which is `EVO_NONE`.
- **The first matching entry wins.** `GetMonEvolution` walks the slots in order and stops
  at the first one whose condition holds. Put the most specific entries first.

## When the game checks

`GetMonEvolution(party, mon, context, usedItem, &method)` returns the target species, or
`SPECIES_NONE`. The `context` decides which methods it looks at:

| Context | Called from | Methods looked at | `usedItem` holds |
|---|---|---|---|
| `EVOCTX_LEVELUP` | after a battle (`BattleSystem_CheckEvolution`, `src/battle/battle_system.c`), Rare Candy (`src/party_menu_items.c`) | all level, friendship, held-item, move, party, gender, beauty and location methods | the map's location method (`MapHeader_GetMapEvolutionMethod`) |
| `EVOCTX_TRADE` | link trade (`src/launch_application.c`), GTS (`src/gts/gts_trade.c`) | `EVO_TRADE`, `EVO_TRADE_ITEM` | the held item |
| `EVOCTX_ITEM_USE` | using an item from the bag (`src/party_menu.c`, `src/use_item_on_mon.c`, `src/party_context_menu.c`) | `EVO_STONE`, `EVO_STONE_MALE`, `EVO_STONE_FEMALE` | the item used |
| `EVOCTX_ITEM_CHECK` | nothing calls it | same as `ITEM_USE` | |

Before the `switch`, two checks apply to every context:

- An Everstone (`HOLD_EFFECT_NO_EVOLVE`) blocks everything except `EVOCTX_ITEM_USE`.
  Kadabra ignores it.
- Spiky-eared Pichu (form 1) never evolves.

Things that follow from where it's called:

- **Level-up methods only run when a Pokémon gains a level**, from a battle or a Rare
  Candy. "Has move", friendship and held-item methods are no exception: there is no check
  on walking, on learning a move or on the friendship going up. After a battle, only party
  members that leveled up in that battle are checked (`setup->levelUpFlag`), and only if
  the battle was won, the wild Pokémon was caught, or the player fled.
- An item only reaches `EVOCTX_ITEM_USE` if it has `"partyUseParam": {"evolve": true}` in
  `data/items/items.json`. Stones also use `"fieldUseFunc": "ITEM_FIELD_USE_EVO_STONE"`,
  which opens the party menu in its stone mode ([items.md](items.md),
  [party-menu-and-item-use.md](party-menu-and-item-use.md)).
- `party` is `NULL` for item use and trades, so `EVO_OTHER_PARTY_MON` only works after
  a battle or a Rare Candy.

## The methods

| Method | `param` | Evolves when (context) | After evolving |
|---|---|---|---|
| `EVO_FRIENDSHIP` | unused | friendship ≥ 220 (level-up) | |
| `EVO_FRIENDSHIP_DAY` / `_NIGHT` | unused | friendship ≥ 220, day / night (`IsNighttime`) (level-up) | |
| `EVO_LEVEL` | level | level ≥ `param` (level-up) | |
| `EVO_TRADE` | unused | traded (trade) | |
| `EVO_TRADE_ITEM` | item | traded holding `param` (trade) | held item removed |
| `EVO_STONE` | item | `param` used on it (item use) | |
| `EVO_LEVEL_ATK_GT_DEF` / `_EQ_` / `_LT_` | level | level ≥ `param` and Attack >, =, < Defense (level-up) | |
| `EVO_LEVEL_PID_LO` / `_HI` | level | level ≥ `param` and (upper 16 bits of personality) % 10 is < 5 / ≥ 5 (level-up) | |
| `EVO_LEVEL_NINJASK` | level | level ≥ `param` (level-up) | adds a Shedinja (below) |
| `EVO_LEVEL_SHEDINJA` | level | never on its own: it sets the method but no target | adds a Shedinja |
| `EVO_BEAUTY` | beauty | beauty ≥ `param` (level-up) | |
| `EVO_STONE_MALE` / `_FEMALE` | item | `param` used on a male / female (item use) | |
| `EVO_ITEM_DAY` / `_NIGHT` | item | holding `param`, day / night (level-up) | held item removed |
| `EVO_HAS_MOVE` | move | knows move `param` (level-up) | |
| `EVO_OTHER_PARTY_MON` | species | `param` is in the party (level-up, battle or Rare Candy only) | |
| `EVO_LEVEL_MALE` / `_FEMALE` | level | level ≥ `param`, male / female (level-up) | |
| `EVO_CORONET`, `EVO_ETERNA`, `EVO_ROUTE217` | unused | the map's location method equals this method (level-up) | |

- **The three location methods never trigger in HeartGold/SoulSilver.**
  `MapHeader_GetMapEvolutionMethod` (`src/map_header.c`) always returns `EVO_NONE`; it's a
  leftover from Diamond/Pearl/Platinum. That's why Magnezone, Leafeon and Glaceon can't
  be evolved in these games. [Example 2](#example-2-location-evolutions-magnezone-leafeon-glaceon)
  turns them back on.
- **Shedinja**: Nincada has `EVO_LEVEL_NINJASK` then `EVO_LEVEL_SHEDINJA`, both level 20.
  The first slot evolves it into Ninjask. The Shedinja comes from the evolution scene:
  if the party has a free slot and the bag holds a Poké Ball, it copies the Pokémon as
  Shedinja and takes one Poké Ball. The second slot is only there for completeness.
- The method that matched is passed to the evolution scene (`evolutionCondition`). That's
  how the scene knows to remove the held item or add a Shedinja.

## Adding a method

### 1. The constant

`include/constants/pokemon.h`, at the end of `enum EvoMethod`:

```c
    EVO_ROUTE217,
    EVO_LEVEL_NIGHT, // your new method
} EvoMethod;
```

Add it at the end so the existing values (and `evo.json`) don't change. The enum is inside
`#ifndef PM_ASM`; nothing in assembly uses it.

### 2. The condition

`GetMonEvolution` in `src/pokemon.c`. Add a `case` to the context that should trigger it.
Most methods go under `EVOCTX_LEVELUP`:

```c
            case EVO_LEVEL_NIGHT:
                if (IsNighttime() == 1 && evoTable[i].param <= level) {
                    target = evoTable[i].target;
                    *method_ret = EVO_LEVEL_NIGHT;
                }
                break;
```

Set both `target` and `*method_ret`. The loop stops at the first slot that sets
`target`.

Values already read at the top of the function: `species`, `heldItem`, `pid`, `pid_hi`,
`beauty`, `holdEffect`, and inside `EVOCTX_LEVELUP`, `level` and `friendship`. Anything
else comes from `GetMonData(mon, MON_DATA_..., NULL)` (the list is in
`include/constants/pokemon.h`). `party` may be `NULL` (see the table above); check it before
using it.

For a method triggered by **using an item**, add the check to the `EVOCTX_ITEM_CHECK` /
`EVOCTX_ITEM_USE` loop instead, in the same style as `EVO_STONE_MALE` (it uses `if`
statements, not a `switch`, and sets `*method_ret = 0`). For a **trade** method, add it to
the `EVOCTX_TRADE` `switch`.

### 3. Effects after the evolution (optional)

If the evolution should consume the held item, add your method to the
`EVO_TRADE_ITEM` / `EVO_ITEM_DAY` / `EVO_ITEM_NIGHT` cases of
`EvolutionScene_ApplyEvolutionEffects` (`src/evolution_scene.c`):

```c
    case EVO_TRADE_ITEM:
    case EVO_ITEM_DAY:
    case EVO_ITEM_NIGHT:
    case EVO_LEVEL_ITEM:   // yours
        i = ITEM_NONE;
        SetMonData(data->mon, MON_DATA_HELD_ITEM, &i);
        break;
```

Anything else that should happen once the Pokémon has evolved (take a bag item, give a
second Pokémon, set a flag) goes in a new `case` here. The function has the party, bag,
Pokédex and game stats (`data->party`, `data->bag`, ...). Item-use evolutions always pass
method 0, so they never reach a `case` here; if one needs an effect, set a real method in
the item loop in step 2.

### 4. Use it

In `files/poketool/personal/evo.json`:

```json
{ "baseSpecies": "SPECIES_SNEASEL",
  "evos": [ { "method": "EVO_LEVEL_NIGHT", "param": 30, "target": "SPECIES_WEAVILE" } ] }
```

Keep at most 7 entries per species.

### 5. Build

`make release`. The JSON is compiled as C, so a misspelled method or constant is a
compile error in the `evo.narc` step.

### A method that needs a new trigger

If the condition can't happen at a level-up, a trade or an item use (say, "after walking
256 steps"), a new `case` isn't enough: something has to call `GetMonEvolution` and start
the evolution scene at that moment. The existing callers show how. `src/start_menu.c`
(`PARTY_MENU_ACTION_RETURN_EVO_RARE_CANDY` and the `evoType` handling) starts the scene
from the field, and `src/battle/battle_022378C0.c` does it after a battle with
`EvolutionScene_New(..., method, flags, heapId)`. The flags are in
`include/evolution_scene.h` (`EVO_FLAG_CAN_CANCEL`, `EVO_FLAG_PRINT_WHAT`,
`EVO_FLAG_TRADE`). Often it's simpler to keep the level-up trigger and only check the new
condition there, the way the friendship methods do.

## Example 1: level up at night

The [Adding a method](#adding-a-method) steps above, end to end:

1. `EVO_LEVEL_NIGHT` at the end of `enum EvoMethod`.
2. The `case EVO_LEVEL_NIGHT` from step 2 under `EVOCTX_LEVELUP` in `GetMonEvolution`.
3. No effect after evolving, so nothing in `evolution_scene.c`.
4. `{ "method": "EVO_LEVEL_NIGHT", "param": 30, "target": ... }` in `evo.json`.

A "level up while holding an item, any time of day" method is the same, with the
condition `evoTable[i].param == heldItem` (copy `EVO_ITEM_DAY` without `IsNighttime`)
and the method added to the held-item `case` in step 3.

## Example 2: location evolutions (Magnezone, Leafeon, Glaceon)

No new method needed: `EVO_CORONET`, `EVO_ETERNA` and `EVO_ROUTE217` are already handled
in `GetMonEvolution`. They compare the slot's method with `usedItem`, which for level-up
is the value `MapHeader_GetMapEvolutionMethod` returns for the current map. Make that
function return something for the maps you choose, in `src/map_header.c`:

```c
EvoMethod MapHeader_GetMapEvolutionMethod(u32 mapId) {
    switch (mapId) {
    case MAP_MOUNT_SILVER_CAVE_1F:
        return EVO_CORONET;  // Magneton -> Magnezone
    case MAP_ILEX_FOREST:
        return EVO_ETERNA;   // Eevee -> Leafeon
    case MAP_ICE_PATH_1F:
    case MAP_ICE_PATH_B1F:
    case MAP_ICE_PATH_B2F:
    case MAP_ICE_PATH_B3F:
        return EVO_ROUTE217; // Eevee -> Glaceon
    default:
        return EVO_NONE;
    }
}
```

Map ids are in `include/constants/maps.h`. The battle reads it when the battle is set
up (`setup->evolutionLocation`, `src/battle/battle_setup.c`), and Rare Candy reads it for
the player's current map. Eevee's `evo.json` entry already lists the location methods
before its stones and friendship methods, so they win when they apply.

This is how you add any method that depends on the map: give it its own `EVO_*`, add a
`case` that compares `usedItem == evoTable[i].method` (copy `EVO_CORONET`), and return it
from `MapHeader_GetMapEvolutionMethod`. Only one location method can apply per map.

## Checklist

- [ ] `EVO_*` added at the end of `enum EvoMethod`
- [ ] `case` in the right context of `GetMonEvolution`, setting `target` and `*method_ret`
- [ ] held item consumed / other effect in `EvolutionScene_ApplyEvolutionEffects`, if any
- [ ] used in `evo.json`, at most 7 entries per species, specific entries first
- [ ] for item methods: the item has `"evolve": true` in `data/items/items.json`
- [ ] `make release`, then test in game: level up in battle **and** with a Rare Candy

## Not verified

- These steps were written from the source, not tested in a built ROM.
- Whether in-game NPC trades go through the same `EVOCTX_TRADE` check as link trades.
