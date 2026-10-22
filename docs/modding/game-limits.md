<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Game limits and rules in C

> AI-generated, local to this fork. Do not upstream.

Numbers the game's rules depend on, and where they're defined. Most were bare
literals in `src/`; they now use these names (same values, ROM unchanged), so
changing one place changes every use. Some are also limits of save data or file
formats: raising those needs more than editing the constant.

| Constant | Value | Header | Meaning |
|---|---|---|---|
| `MAX_LEVEL` | 100 | `constants/pokemon.h` | level cap |
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

Still literals (candidates for names): badge counts (16/8), Unown forms (28),
obedience level caps by badge, Battle Frontier caps (9999) and level modes
(50/100, sentinels 120/121), max PP Ups (3), apricorn cap (99). The accuracy
table `sHitChanceTable[13]` (`src/battle/battle_controller_player.c`) has one row
per stat stage, so changing the stage range means editing it too.
