<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-27 -->

# Pokémon forms

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers alternate forms: what a form is, which tables are read by form
(stats, learnsets, sprites, icons, Pokéathlon, followers, Pokédex), what changes a
Pokémon's form in the retail game, and how to change the existing forms or add a new
one. Adding a whole new species is [adding-a-species.md](adding-a-species.md).

The recipe in [section 5](#5-adding-a-form) adds a test form, Charizard form 1
(`SPECIES_CHARIZARD_X`), with its own stats, types, learnset, sprites and icon. It
switches to that form while holding Charcoal. HeartGold and SoulSilver both built with
it. **It has not been played**: see [Not verified](#not-verified).

If you know pokeemerald: Gen 3 has no form field (Unown's letter comes from the
personality, Castform's form only exists in battle). Here every Pokémon stores a form
number, and the game looks up a form through hard-coded `switch (species)` blocks, not
a table.

## 1. What a form is

`MON_DATA_FORM` is a 5-bit field of the box data (`u8 form : 5` in
[include/pokemon_types_def.h](../../include/pokemon_types_def.h)), so forms are 0-31
per species. Form 0 is the normal one. The numbers are the `AlternateForms` enum in
[include/constants/pokemon.h](../../include/constants/pokemon.h) (`ROTOM_HEAT`,
`GIRATINA_ORIGIN`...); `SHAYMIN_LAND`/`SHAYMIN_SKY` are `#define`s above it because
assembly uses them.

Some things that follow from it being a field of the Pokémon:

- **Evolution keeps it.** Evolving only rewrites the species
  ([src/evolution_scene.c](../../src/evolution_scene.c)), so a Sandy Cloak Burmy becomes a
  Sandy Cloak Wormadam. Make sure a form number means something for the evolution too,
  or `SanitizeMonForm` (below) turns it back into 0 for display.
- **Eggs take the mother's form** (`SetBreedEggStats` in [src/get_egg.c](../../src/get_egg.c);
  with Ditto, Ditto's form 0). See [breeding.md](breeding.md).
- **Battles copy it** into `BattleMon.form` ([include/battle/battle.h](../../include/battle/battle.h)),
  loaded from the party Pokémon at the start of the battle. Changes in battle are only
  copied back for Giratina and Shaymin ([section 4](#in-battle)).

## 2. The retail forms

| Species | Forms | Own stats and learnset | Changed by |
|---|---|---|---|
| Unown | 28 (`UNOWN_A` ... `UNOWN_QUESTION_MARK`) | no | set when the Pokémon is made: wild Unown get a letter unlocked by the Ruins of Alph puzzles (`EncounterGen_ChooseUnownForm`, [src/field/encounter_check.c](../../src/field/encounter_check.c)) |
| Pichu | 2 (Spiky-eared) | no | only the Ilex Forest gift (`givespikyearpichu`); it can't evolve (`src/pokemon.c`, `GetMonEvolution`) |
| Castform | 4 | no | battle only: Forecast and the weather |
| Cherrim | 2 | no | battle only: sun |
| Deoxys | 4 | yes (`SPECIES_DEOXYS_ATK`, `_DEF`, `_SPD`) | the Route 3 meteorites: `setpartydeoxysform(n)` in [data/maps/Route3/scripts.pory](../../data/maps/Route3/scripts.pory) |
| Burmy | 3 | no | after a battle it took part in, by the battle's terrain (`BattleSystem_TryChangeForm`, [src/battle/battle_system.c](../../src/battle/battle_system.c)) |
| Wormadam | 3 | yes (`SPECIES_WORMADAM_SANDY`, `_TRASH`) | never; it keeps Burmy's |
| Shellos, Gastrodon | 2 (West, East) | no | never in HGSS; East Sea ones only come from other games |
| Giratina | 2 | yes (`SPECIES_GIRATINA_ORIGIN`) | holding the Griseous Orb |
| Shaymin | 2 | yes (`SPECIES_SHAYMIN_SKY`) | the Gracidea; back to Land Forme at night, when frozen, and in the PC, Day Care and trades |
| Rotom | 6 | yes (`SPECIES_ROTOM_HEAT` ... `_MOW`) | the Silph Co. Rotom room: `updaterotomform` in [data/maps/Saffron_SilphCoRotomRoom/scripts.pory](../../data/maps/Saffron_SilphCoRotomRoom/scripts.pory) |
| Arceus | 18 (form = type number) | no | its held Plate (only with Multitype) |
| Egg | 2 | | form 1 is the Manaphy Egg's picture; picked from the species, not stored |

"Own stats and learnset" means the form has its own entry after the eggs in the species
list (496-507), described next. The others share their species' data and only look
different. Arceus' types come from Multitype in battle, not from its data.

## 3. How a form is looked up

### Stats, types, abilities, TMs, learnset: `ResolveMonForm`

`ResolveMonForm(species, form)` ([src/pokemon.c](../../src/pokemon.c)) turns a species
and form into a **resolved species**: the species itself, or one of the form entries
after the eggs:

```c
#define SPECIES_EGG             494
#define SPECIES_BAD_EGG         495
#define SPECIES_DEOXYS_ATK      496
...
#define SPECIES_ROTOM_MOW       507

#define NUM_SPECIES SPECIES_ROTOM_MOW
```

Everything that goes through it gets per-form data from the entry at that number:

| Data | File | Entry for a form |
|---|---|---|
| base stats, types, abilities, EV yield, gender ratio, TM/HM list (`GetMonBaseStat_HandleAlternateForm`, `GetTMHMCompatBySpeciesAndForm`) | `files/poketool/personal/personal.json` | position 496... (`"species": "DEOXYS_ATK"`) |
| level-up learnset (`LoadLevelUpLearnset_HandleAlternateForm`: level-up, new Pokémon's moves, Move Relearner) | `files/poketool/personal/level_up_learnsets.json` | key `SPECIES_DEOXYS_ATK` |

A form change only takes effect in stats once they are recalculated
(`CalcMonLevelAndStats`), and the ability with `UpdateMonAbility`/`UpdateBoxMonAbility`;
the retail form changers do both.

Two other move lists have their own rules:

- **Tutor moves**: `files/fielddata/wazaoshie/waza_oshie.json` has an entry for each
  form after Arceus, but the game picks it with its own switch,
  `GetMoveTutorLearnsetIndex` in [src/field/scrcmd_move_tutor.c](../../src/field/scrcmd_move_tutor.c).
- **Egg moves** are by species only (`LoadEggMoves`); forms can't have their own.

`evo.json` and `pms.narc` (egg species) have entries for 496-507 too, but evolution
and breeding use the species, never the resolved form.

### Battle sprites: `otherpoke.narc`

`GetMonSpriteCharAndPlttNarcIdsEx` ([src/pokemon.c](../../src/pokemon.c)) sends every
species with forms (all forms, form 0 included) to `otherpoke.narc` instead of the normal
`pokegra.narc`, with a formula per species:

```c
    case SPECIES_ROTOM: // normal, fan, mow, wash, heat, frost
        pokepicTemplate->narcID = NARC_poketool_pokegra_otherpoke;
        pokepicTemplate->charDataID = (u16)(whichFacing / 2 + 0x8A + form * 2);
        pokepicTemplate->palDataID = (u16)(shiny + 0xEC + form * 2);
```

(The comment's order is wrong: the files are normal, heat, wash, frost, fan, mow, as
`ROTOM_HEAT`... say.) `whichFacing / 2` is 0 for the back and 1 for the front, so each
form has two pictures, back then front, and two palettes, normal then shiny.

The pictures are `files/poketool/pokegra/otherpoke/<species>/<form>/{front,back}.png`
(160×80, 4-bit, two frames, like the normal sprites; [pokemon.md](pokemon.md#graphics)).
Each species folder's `meson.build` gives each picture its member number:

```meson
otherpoke_index_ncgr += {
    '0138' : files('normal/back.png'),
    '0139' : files('normal/front.png'),
    '0140' : files('oven/back.png'),
    ...
}

otherpoke_index_nclr += {
    '236' : files('normal/front.png'),     # normal palette
    '237' : files('normal/back.png'),      # shiny palette
    ...
}
```

The palettes come from the PNGs, like the normal sprites: `front.png`'s palette is the
normal one and `back.png`'s the shiny one. The archive's layout:

| Members | Content |
|---|---|
| 0-157 | pictures: Deoxys 0, Unown 8, Castform 64, Burmy 72, Wormadam 78, Shellos 84, Gastrodon 88, Cherrim 92, Arceus 96, eggs 132, Shaymin 134, Rotom 138, Giratina 150, Pichu 154 |
| 158-255 | palettes, in the same species order |
| 256-258 | the Substitute doll |
| 259, 260 | the shadow |

Castform, Cherrim, Shellos and Gastrodon use different formulas (one palette pair for
all forms, or `whichFacing + form`), so read the species' case before editing its files.
Forms have no female pictures: `otherpoke` ignores gender.

`SanitizeMonForm` runs first and turns a form above the species' `*_FORM_MAX - 1` into 0,
and every species not in it into form 0. A form number the game doesn't know shows the
normal picture.

There is a second copy of the function, `DP_GetMonSpriteCharAndPlttNarcIdsEx`, with
older palette numbers; only the dress-up (photo) screen uses it.

### Sprite height: `height_o.narc`

The picture's vertical offset in battle. `GetMonPicHeightBySpeciesGenderForm` reads
`height.narc` (four members per species) for species without forms and `height_o.narc`
(160 members, a formula per species like the pictures) for the others.

### Icons and their palettes

In [src/pokemon_icon_idx.c](../../src/pokemon_icon_idx.c):

| | Form 0 | Other forms |
|---|---|---|
| icon file (`files/poketool/icongra/poke_icon/poke_icon_000005NN.png`) | species + 7 | `GetMonIconNaixEx`: Deoxys 503, Unown 507, Burmy 534, Wormadam 536, Shellos 538, Gastrodon 539, Giratina 540, Shaymin 541, Rotom 542 (+ form - 1); Castform 547 and Cherrim 550 in `GetBattleMonIconNaixEx` (battle only) |
| palette (0-2) | `sPokemonPalNoBySpeciesAndForm[species]` | entry 496 + ... by the same pattern, `GetMonIconPaletteEx` / `GetBattleMonIconPaletteEx` |

Party and PC icons get the form from `BoxMonGetForm`, which **only** returns it for the
species listed there (Unown, Deoxys, Shellos, Gastrodon, Burmy, Wormadam, Giratina,
Shaymin, Rotom); any other species shows form 0's icon.

Mail keeps its own list of form icons (`sFormOverrides` in [src/mail.c](../../src/mail.c):
Giratina, Shaymin, Rotom); anything else is drawn in its normal form on mail.

### Other per-form tables

| What | Where | How a form is found |
|---|---|---|
| Pokéathlon stats | `sPokeathlonPerformanceArcIdxs[species] + form` in `src/pokemon.c`, and the course's copy `gPokeathlonPerformanceFileIds` (`asm/pokeathlon_course_data.s`, read by `PokeathlonCourse_GetPerformanceFileId`) | consecutive members of `performance.narc`, one per form, for species with forms (Pichu, Unown, Deoxys, Burmy, Wormadam, Shellos, Gastrodon, Rotom, Giratina, Shaymin, Arceus; [pokeathlon.md](pokeathlon.md)) |
| following Pokémon model | `sModelIndexLUT` + form in [src/follow_mon.c](../../src/follow_mon.c), if the form is at most `sFormMaxLUT[species - 1]`; a species with a female model (`sFemaleFlagLUT`) ignores the form | consecutive `FOLLOWER_MON_*` models; the same for its `tp_param.csv` row and the Hall of Fame model. A form above the count uses form 0's model ([following-pokemon.md](following-pokemon.md)) |
| cry | `IsShayminSkyCry` in [src/sound_playback.c](../../src/sound_playback.c) | only Shaymin Sky (cry bank 494) has its own; every other form uses the species' cry |
| battle animation, cry delay, shadow | `files/a/1/8/0` | by species only; forms share them |
| Pokédex: forms seen | [src/pokedex.c](../../src/pokedex.c), save fields `shellosFormOrder`... `pichuFormOrder` in [include/pokedex.h](../../include/pokedex.h) | per species, in the order seen (Unown, Shellos, Gastrodon, Burmy, Wormadam, Deoxys, Rotom, Shaymin, Giratina, Pichu). The Pokédex shows the first form seen and has a form viewer (`pokedex_screen_setup.c`) |
| Pokédex height and weight text | `SetDexBanksByGiratinaForm` ([src/dex_mon_measures.c](../../src/dex_mon_measures.c)) | Giratina Origin reads `msg_0813`/`msg_0815` instead of `msg_0812`/`msg_0814`; no other form has its own |
| form names | `msg_0802.json` 114-166, chosen by `PokedexApp_GetFormNameMsg` ([src/application/pokedex/pokedex_windows.c](../../src/application/pokedex/pokedex_windows.c)) | Pokédex form viewer only. No script command prints a form name |
| Pokéwalker picture | `PokewalkerApp_GetPictureFile` ([src/application/pokewalker/pokewalker_ui.c](../../src/application/pokewalker/pokewalker_ui.c)) | a switch like the battle sprites |

## 4. What changes a form

### Held items: Griseous Orb, Plates

`BoxMon_UpdateGiratinaForm` (Griseous Orb → Origin, else Altered) and
`BoxMon_UpdateArceusForm` (Plate → its type) in [src/pokemon.c](../../src/pokemon.c) run
whenever the held item changes outside battle:

- the party menu: giving (`PartyMenu_GiveItemToMon_HandleGriseousOrb`), swapping
  (`PartyMenu_SwapMonHeldItem`), taking an item or mail
  ([src/party_menu.c](../../src/party_menu.c), [src/party_menu_list_items.c](../../src/party_menu_list_items.c));
- the PC: `PCBox_UpdateArceusGiratinaForm` ([src/application/pc_box/pc_box.c](../../src/application/pc_box/pc_box.c)),
  after every item move in `pc_box_states.c`.

The party versions (`Mon_UpdateGiratinaForm`) also recalculate the stats; the Arceus one
doesn't need to, as Arceus' forms share one data entry.

### Using an item: Gracidea

`PartyMenu_HandleUseItemOnMon` ([src/party_menu.c](../../src/party_menu.c)) accepts the
Gracidea when `Mon_CanUseGracidea` is true: Shaymin, Land Forme, not fainted, not frozen,
met in a fateful encounter (an event Shaymin), between 4:00 and 19:59. The change itself
is done during the animation (`PartyMenu_AnimateIconFormChange`,
[src/overlay_94.c](../../src/overlay_94.c)), which calls `Mon_UpdateShayminForm`.

### Resets: Shaymin, and others when they leave

| When | What | Where |
|---|---|---|
| the clock passes 20:00 (or 4:00) | every Shaymin in the party → Land (`Party_TryResetShaymin`) | `FieldSystem_HandleMinutesPassed`, [src/field_time_events.c](../../src/field_time_events.c) |
| the save is loaded with a changed clock | the same | [src/overlay_36.c](../../src/overlay_36.c) |
| moved into the PC, or into the Day Care | Shaymin → Land | `PCBox_RevertShayminFormOnMove`, [src/get_egg.c](../../src/get_egg.c) |
| Day Care deposit | Giratina by its item, Rotom → normal, Shaymin → Land (`daycaresanitizemon`) | `ScrCmd_DaycareSanitizeMon`, [src/scrcmd_daycare.c](../../src/scrcmd_daycare.c) |
| wireless trade, other link features | Shaymin → Land; Giratina, Rotom, Shaymin sanitized | [src/wireless_trade_select_mon.c](../../src/wireless_trade_select_mon.c), `ScrCmd_CommSanitizeParty` |
| GTS | Rotom, Giratina and Shaymin forms and Spiky-eared Pichu can't be offered | `GtsSelectMon_GetFormRestriction` |

When a Shaymin following you has reverted, `std_revert_shaymin` plays the overworld
change (`ShayminRevertToLandForm`, `src/field/event_cutscene_shaymin.c`).

### Scripts

| Command | What it does |
|---|---|
| `givemon(species, level, item, form, ability, var)` | gives a Pokémon with that form ([gift-pokemon-and-trades.md](gift-pokemon-and-trades.md#1-givemon)) |
| `setpartydeoxysform(form)` | every Deoxys in the party, with stats recalculated and the Pokédex updated |
| `updaterotomform(slot, moveSlot, 0, form)` | Rotom in that slot; swaps its form move (Overheat, Hydro Pump, Blizzard, Air Slash, Leaf Storm) into `moveSlot` if all four are full, and gives Thunder Shock if it is left without moves (`Mon_UpdateRotomForm`) |
| `setmonform(slot, form)` | writes the form, **nothing else**: stats and ability stay those of the old form until something recalculates them |
| `getpartymonform(slot, var)` | reads it (`getpartymonform2` the same) |
| `getpartymonunownletter`, `countpartyburmyforms`, `getownedrotomforms`, `counttranformedrotomsinparty` | species-specific checks |

`setmonform` is the only general one. To use it for a form with its own stats, add the
missing calls to `ScrCmd_SetMonForm` ([src/field/scrcmd_pokemon_misc.c](../../src/field/scrcmd_pokemon_misc.c)):

```c
    SetMonData(mon, MON_DATA_FORM, &form);
    UpdateMonAbility(mon);
    CalcMonLevelAndStats(mon);
```

No retail script uses `setmonform`, so this changes nothing in the game.

### Wild and trainer Pokémon

- **Wild**: the encounter tables have no form; wild Pokémon are form 0, except Unown.
- **Trainers**: optional `"form"` per Pokémon in `trainers.json`, packed into the top 6
  bits of the species ([trainers.md](trainers.md)). No retail trainer uses it.
- **Battle Frontier** sets carry a form; **Pal Park** sets Unown's letter from the
  personality and Deoxys' form from the GBA game.

`givemon` (`GiveMon`, [src/script_pokemon_util.c](../../src/script_pokemon_util.c)) and
trainer parties (`CreateNPCTrainerParty`, [src/trainer_data.c](../../src/trainer_data.c))
create the Pokémon as form 0 and only then write the form. Its stats, ability and
level-up moves are form 0's until something recalculates them. Retail never gives a form
with its own stats this way. For one that does, add after the `SetMonData(mon, MON_DATA_FORM, &form);`
(in `GiveMon` before the ability is set, in `trainer_data.c` in each of the four party
types):

```c
        UpdateMonAbility(mon);
        CalcMonLevelAndStats(mon);
```

The moves stay form 0's; give a trainer's Pokémon its moves in `trainers.json`.

### In battle

`Battler_CheckWeatherFormChange` ([src/battle/battle_util.c](../../src/battle/battle_util.c))
runs on switch-in and when the field changes. It changes `BattleMon.form` (and the
types) and runs subscript 262 (`FormChange`):

| Species | Rule |
|---|---|
| Castform | Forecast and no Cloud Nine/Air Lock: Sunny, Rainy, Snowy, else Normal |
| Cherrim | sun: Sunshine, else Overcast |
| Arceus | its held item changed (Trick...): new type from the Plate |
| Giratina | Origin without the Griseous Orb, outside the Distortion World: back to Altered (subscript 296) |

Shaymin Sky that gets frozen turns into Land Forme (subscript 293, `CheckShayminForm`).
After the battle, only forms changed with `BATTLE_STATUS2_FORM_CHANGE` or
`BATTLE_STATUS2_RECALC_MON_STATS` are copied back to the party (`BattleController_EmitUpdatePartyMon`):
Shaymin and Giratina. Castform, Cherrim and Arceus are form 0 (or their Plate's form)
again in the party. Burmy's new cloak is written straight to the party at the end
(`BattleSystem_TryChangeForm`; not in battles without experience).

## 5. Adding a form

The example gives Charizard a form 1, `SPECIES_CHARIZARD_X`: Fire/Dragon, 130 Attack and
Special Attack, its own learnset. It switches to that form while holding Charcoal, the way
Giratina does with the Griseous Orb. Replace the names, numbers and trigger with yours.

For a form of a species that already has forms (a seventh Rotom), the same steps apply,
but the per-species formulas in sections 3 and 4 would run into the next species'
files: handle the new form number separately, as below, rather than extending the
formula.

**Checklist**

| Step | Files |
|---|---|
| [1. Constants](#51-constants) | `species.h`, `pokemon.h` |
| [2. Data](#52-stats-learnset-tutor-moves) | `personal.json`, `level_up_learnsets.json`, `waza_oshie.json`, `pms.narc` |
| [3. C lookups](#53-the-c-lookups) | `ResolveMonForm`, `SanitizeMonForm`, `GetMoveTutorLearnsetIndex` |
| [4. Battle sprites](#54-battle-sprites) | `otherpoke/charizard/`, `height_o.narc`, `src/pokemon.c` |
| [5. Icon](#55-icon) | `poke_icon_00000551.png`, `src/pokemon_icon_idx.c` |
| [6. Pokéathlon](#56-pokéathlon) | `performance.narc`, `src/pokemon.c`, `pokeathlon_course_flow.c` |
| [7. The trigger](#57-the-trigger) | `src/pokemon.c`, `pc_box.c` |

If you also added species ([adding-a-species.md](adding-a-species.md)), they took the same
"next free" numbers used here (icon 551, palette entry 544, Pokéathlon member 554, cry
bank 494...): use the next ones after them.

### 5.1 Constants

In [include/constants/species.h](../../include/constants/species.h), a new resolved
species after the last form, and `NUM_SPECIES` with it:

```c
#define SPECIES_ROTOM_MOW       507
#define SPECIES_CHARIZARD_X     508

#define NUM_SPECIES SPECIES_CHARIZARD_X
```

Nothing moves: form entries go at the end. Only a form with its own stats or learnset
needs this number. A form that only looks different (like Unown) skips it, the data in
5.2, and the `ResolveMonForm` and tutor cases in 5.3; it still needs the form numbers
below and `SanitizeMonForm`.

**Rebuild `evo.narc`**: its size follows `NUM_SPECIES`, but the build only watches
`evo.json`. Run `touch files/poketool/personal/evo.json`.

In [include/constants/pokemon.h](../../include/constants/pokemon.h), the form numbers, at
the end of `AlternateForms`:

```c
    CHARIZARD_NORMAL = 0,
    CHARIZARD_X = 1,
    CHARIZARD_FORM_MAX = 2,
```

### 5.2 Stats, learnset, tutor moves

All three lists get the new entry **at the end**, after `ROTOM_MOW`:

- `files/poketool/personal/personal.json`: a copy of Charizard's entry with
  `"species": "CHARIZARD_X"` and the new stats, types, abilities and `tms`/`hms`
  ([pokemon.md](pokemon.md#base-stats-types-abilities-items-tmhm)). The position is what
  counts.
- `files/poketool/personal/level_up_learnsets.json`: `"SPECIES_CHARIZARD_X": [...]`
  (by name; at most 21 moves).
- `files/fielddata/wazaoshie/waza_oshie.json`: `{"mon": "SPECIES_CHARIZARD_X", "moves": [...]}`
  at the end of `tutor`. The game checks the file's size against `NUM_SPECIES`, so this
  entry is required ([move-tutors.md](move-tutors.md)).
- `files/poketool/personal/pms.narc` (a raw `u16` list, [adding-a-species.md](adding-a-species.md#4-egg-species-pmsnarc)):
  append one value. The game never reads it for a form (eggs use the species); the
  retail form entries hold their own number:

  ```sh
  python3 -c "
  import struct; p = 'files/poketool/personal/pms.narc'
  open(p, 'ab').write(struct.pack('<H', 508))"
  ```

### 5.3 The C lookups

In [src/pokemon.c](../../src/pokemon.c), `ResolveMonForm`, so stats and learnset use the
new entry:

```c
    case SPECIES_CHARIZARD:
        if (form != CHARIZARD_NORMAL && form <= CHARIZARD_FORM_MAX - 1) {
            return SPECIES_CHARIZARD_X + form - CHARIZARD_X;
        }
        break;
```

and `SanitizeMonForm`, so sprites, icons and heights accept form 1:

```c
    case SPECIES_CHARIZARD:
        if (form > CHARIZARD_FORM_MAX - 1) {
            form = 0;
        }
        break;
```

In [src/field/scrcmd_move_tutor.c](../../src/field/scrcmd_move_tutor.c),
`GetMoveTutorLearnsetIndex` (the `- 2` skips the two eggs, which have no tutor entry):

```c
    case SPECIES_CHARIZARD:
        if (form == CHARIZARD_X) {
            index = SPECIES_CHARIZARD_X - 2;
        }
        break;
```

### 5.4 Battle sprites

**The pictures.** Make `files/poketool/pokegra/otherpoke/charizard/x/` with `front.png`,
`back.png` and their `.key` files: start from a copy of
`files/poketool/pokegra/pokegra/0006/male/` and draw over it. Then
`files/poketool/pokegra/otherpoke/charizard/meson.build`, with the next free members
(after the shadow, 260):

```meson
otherpoke_index_ncgr += {
    '261' : files('x/back.png'),
    '262' : files('x/front.png'),
}

otherpoke_index_nclr += {
    '263' : files('x/front.png'),
    '264' : files('x/back.png'),
}
```

and `subdir('charizard')` in `files/poketool/pokegra/otherpoke/meson.build`.

**Write the numbers without a leading zero.** The archive is built from files named by
these keys, sorted as text: `'0261'` sorts before `'158'` and lands at member 158, moving
every palette after it. (The retail keys below 158 have four digits, all the others
three, so they sort correctly.) If you get it wrong, delete
`build/<game>/files/poketool/pokegra/otherpoke.narc.p/` and `otherpoke.narc` after fixing
it: the build packs every file in that folder, old ones included.

Charizard's form 0 stays in `pokegra.narc`. Only form 1 goes to `otherpoke`, so add it
before the `switch` in `GetMonSpriteCharAndPlttNarcIdsEx`:

```c
    form = SanitizeMonForm(species, form);
    if (species == SPECIES_CHARIZARD && form != CHARIZARD_NORMAL) {
        pokepicTemplate->narcID = NARC_poketool_pokegra_otherpoke;
        pokepicTemplate->charDataID = (u16)(whichFacing / 2 + 261 + (form - 1) * 2);
        pokepicTemplate->palDataID = (u16)(shiny + 263 + (form - 1) * 2);
        return;
    }
    switch (species) {
```

The same in `DP_GetMonSpriteCharAndPlttNarcIdsEx` if the dress-up screen should show it.

**The height.** `height_o.narc` has 160 members; append two, the back and front height.
Charizard's male ones are members 25 and 27 of `height.narc` (`species * 4 + 1` and
`species * 4 + 3`). With `nitroarc` ([adding-a-species.md](adding-a-species.md#0-before-you-start)):
unpack both, copy `height.narc.d/00025.bin` to `height_o.narc.d/00160.bin` and `00027.bin`
to `00161.bin`, pack `height_o.narc`. Then in `GetMonPicHeightBySpeciesGenderForm`, after
its `SanitizeMonForm`:

```c
    if (species == SPECIES_CHARIZARD && form != CHARIZARD_NORMAL) {
        ReadWholeNarcMemberByIdPair(&ret, NARC_poketool_pokegra_height_o, 160 + whichFacing / 2 + (form - 1) * 2);
        return ret;
    }
```

### 5.5 Icon

Add `files/poketool/icongra/poke_icon/poke_icon_00000551.png` (32×64, two frames; start
from Charizard's, `poke_icon_00000013.png`) and list it at the end of that folder's
`meson.build`. In [src/pokemon_icon_idx.c](../../src/pokemon_icon_idx.c):

1. `GetMonIconNaixEx`, after the Rotom branch:

   ```c
        } else if (species == SPECIES_CHARIZARD) {
            return form + 551 - 1;
        }
   ```

2. `BoxMonGetForm`: add `case SPECIES_CHARIZARD:` to the list that returns
   `MON_DATA_FORM`. Without it, party and PC icons stay form 0.
3. Append one entry, the palette (0, 1 or 2), to `sPokemonPalNoBySpeciesAndForm`
   (it becomes entry 544) and in `GetMonIconPaletteEx`:

   ```c
        } else if (species == SPECIES_CHARIZARD) {
            species = 544 + form - 1;
        }
   ```

### 5.6 Pokéathlon

Charizard has one `performance.narc` member, so `[species] + form` would read Squirtle's.
Append a member (unpack, copy Charizard's `00005.bin` to `00554.bin`, edit its 20 bytes as
in [pokeathlon.md](pokeathlon.md#9-how-to-change-a-species-stats), pack), and send the
form to it in both readers. In `src/pokemon.c` (the function that reads
`sPokeathlonPerformanceArcIdxs`):

```c
    if (species == SPECIES_CHARIZARD && form == CHARIZARD_X) {
        ReadWholeNarcMemberByIdPair(&data, NARC_poketool_personal_performance, 554);
    } else {
        ReadWholeNarcMemberByIdPair(&data, NARC_poketool_personal_performance, sPokeathlonPerformanceArcIdxs[species] + form);
    }
```

and `PokeathlonCourse_GetPerformanceFileId` in
[src/pokeathlon/pokeathlon_course_flow.c](../../src/pokeathlon/pokeathlon_course_flow.c):

```c
    if (species == SPECIES_CHARIZARD && form == CHARIZARD_X) {
        return 554;
    }
    return form + gPokeathlonPerformanceFileIds[species];
```

### 5.7 The trigger

A held-item form fits where the Griseous Orb is checked: `BoxMon_UpdateGiratinaForm` is
already called on every item change in the party and the PC, and its party version
recalculates the stats. In [src/pokemon.c](../../src/pokemon.c), before its
`return -1;`:

```c
    if (species == SPECIES_CHARIZARD) {
        form = heldItem == ITEM_CHARCOAL ? CHARIZARD_X : CHARIZARD_NORMAL;
        SetBoxMonData(boxMon, MON_DATA_FORM, &form);
        UpdateBoxMonAbility(boxMon);
        return form;
    }
```

and in `PCBox_UpdateArceusGiratinaForm` ([src/application/pc_box/pc_box.c](../../src/application/pc_box/pc_box.c)),
`} else if (species == SPECIES_GIRATINA || species == SPECIES_CHARIZARD) {`. The party
menu's "Griseous Orb" messages check the item, so Charcoal gets the normal ones.

Other triggers:

- **from a script**: `setmonform(slot, 1)`, with the change to `ScrCmd_SetMonForm` in
  [section 4](#scripts);
- **from the start**: `givemon(SPECIES_CHARIZARD, 36, ITEM_NONE, 1, 0, VAR_SPECIAL_RESULT)`,
  or `"form": 1` in `trainers.json`. Both write the form after making the Pokémon, so it
  keeps form 0's stats, ability and level-up moves (see [Wild and trainer Pokémon](#wild-and-trainer-pokémon));
- **in battle**: a case in `Battler_CheckWeatherFormChange`, like Cherrim. It stays in
  battle unless you also set `BATTLE_STATUS2_FORM_CHANGE`, as the Giratina case does.

The held item isn't checked in battle: Charizard X that loses its Charcoal to Knock Off
or Trick stays Charizard X until the battle ends. Day Care, trades and the GTS don't
know the form either (see [Resets](#resets-shaymin-and-others-when-they-leave)).

### 5.8 What it gets without changes

- **Following Pokémon**: Charizard has no follower forms (`sFormMaxLUT` 0), so form 1
  uses its normal model. A model of its own means a new `FOLLOWER_MON_*` right after
  Charizard's, which renumbers every later follower, sprite id, texture and `tp_param`
  row; or one at the end and code in `FollowMon_GetSpriteID`, as
  [adding-a-species.md](adding-a-species.md#a-follower-model-of-its-own) does for a new
  species.
- **Cry, battle animation, shadow**: Charizard's.
- **Pokédex**: shows form 0; it records forms only for the species in its save fields,
  and the save has one spare byte (`dummy`). Recording a new species' forms means
  changing the save layout ([save-data.md](save-data.md)).
- **Pokéwalker, mail**: the normal picture and icon.
- **Evolution**: Charmeleon evolves into form 0; an evolved Charizard gets form 1 when it
  holds Charcoal.

### 5.9 Build

`make release` (and `make release GAME_VERSION=SOULSILVER`); `make` also runs the retail
checksums, which now fail. Check `personal.narc`, `wotbl.narc` and `evo.narc` have 509
members, `otherpoke.narc` 265, `height_o.narc` 162 and `poke_icon.narc` 552.

**Undoing it** leaves old files in `build/`: delete
`build/<game>/files/poketool/pokegra/otherpoke.narc*` and
`build/<game>/files/poketool/icongra/poke_icon/poke_icon.narc*`, and
`touch files/poketool/personal/evo.json`, or the archives keep the removed form (found by
the checksums when the test was reverted).

## 6. Changing the existing forms

- **Stats, types, abilities, TMs** of a form with its own entry: edit `DEOXYS_ATK`...
  `ROTOM_MOW` in `personal.json`. Arceus, Unown, Burmy, Castform and the others share
  their species' entry; to give them their own stats, add resolved species for them as
  in 5.1-5.3.
- **Learnsets**: the `SPECIES_DEOXYS_ATK`... keys in `level_up_learnsets.json`; tutor
  moves the same names in `waza_oshie.json`.
- **Sprites**: the PNGs in `files/poketool/pokegra/otherpoke/<species>/<form>/`, same size
  and palette size.
- **Icons**: the file numbers in [section 3](#icons-and-their-palettes).
- **Rotom's form moves**: `form_moves` in `Mon_UpdateRotomForm`.
- **Gracidea hours, Shaymin's reset time**: `Mon_CanUseGracidea` and `Party_TryResetShaymin`
  ([day-night-and-rtc.md](day-night-and-rtc.md)).
- **Burmy's cloak by terrain**: `BattleSystem_TryChangeForm`; the terrains are in
  [terrain.md](terrain.md).
- **Another item for a form**: the item checks in `BoxMon_UpdateGiratinaForm` and
  `GetArceusTypeByHeldItemEffect`, and the in-battle ones in `Battler_CheckWeatherFormChange`.

## Not verified

The Charizard form was built for HeartGold and SoulSilver, with the archive member
counts above and every `otherpoke.narc` member checked against its source file; the
changes were then reverted. Nothing was played. In particular:

- that the form's stats, types, learnset and tutor moves show up in the summary and in
  battle;
- the sprite, its height, the icon and its palette;
- giving and taking Charcoal in the party and the PC (the party icon may only update
  when the menu is reopened);
- the Pokéathlon stats, and the `setmonform` change.
