<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# The Pokédex

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers what the Pokédex stores, how the player gets it, the Johto (regional)
and National modes, changing the Johto order, unlocking the National Dex, and setting or
reading seen/caught from a script. The data shown for each species (height, weight, entry
text, area map, sort lists) is in [pokemon.md](pokemon.md#pokédex-data); adding a species
to the Pokédex is step 6 of [adding-a-species.md](adding-a-species.md#6-pokédex).

| Task | Where |
|---|---|
| Give the Pokédex earlier or later | [§2](#2-getting-the-pokédex) |
| Change which species are in the Johto Pokédex, or their order | [§3](#3-the-johto-order) |
| Unlock the National Dex at another time | [§4](#4-the-national-dex) |
| Mark a species seen or caught from a script | [§5](#5-seen-and-caught) |
| Check how many the player has, or whether one is registered | [§5](#5-seen-and-caught), [§6](#6-counting-and-completion) |

## 1. What is saved

Everything is in the `Pokedex` struct ([include/pokedex.h](../../include/pokedex.h)), save
chunk `SAVE_POKEDEX` (832 bytes; [save-data.md](save-data.md)):

| Field | What it holds |
|---|---|
| `caughtSpecies`, `seenSpecies` | one bit per national number (species 1 is bit 0) |
| `seenGenders[2]` | the gender seen first, and the other gender if it was seen too |
| `spindaPersonality` | the first Spinda seen, for its spot pattern |
| `unownSeenOrder`, `unownCaughtOrder`, `*FormOrder` | forms in the order they were seen (Unown, Shellos, Gastrodon, Burmy, Wormadam, Deoxys, Rotom, Shaymin, Giratina, Pichu) |
| `caughtLanguages` | one byte per species: the languages it was caught in, for the foreign entries |
| `dexEnabled` | the player has the Pokédex (set by `givepokedex`) |
| `nationalDex` | National Mode is unlocked |
| `enabledInternational` | a foreign-language Pokémon was caught; the entry screen offers other languages |
| `canDetectForms` | set by `enablepokedexformdetection`; nothing reads it |

All of it goes through [src/pokedex.c](../../src/pokedex.c). The Johto numbers are **not**
saved: they are read from `files/poketool/johtozukan.narc` each time, so changing them
([§3](#3-the-johto-order)) doesn't affect saves.

"Caught" means both bits are set: `Pokedex_CheckMonCaughtFlag` checks the caught bit
**and** the seen bit. Setting caught through `Pokedex_SetMonCaughtFlag` always sets both.

## 2. Getting the Pokédex

Two separate things make the Pokédex "owned", and the vanilla script sets both
(`Route30_MrPokemonHouse`, after Oak's speech):

```
givepokedex
setflag(FLAG_GOT_POKEDEX)
```

| | Set by | Read by |
|---|---|---|
| `dexEnabled` in the save | `givepokedex` (`ScrCmd_GivePokedex`, [src/scrcmd_17.c](../../src/scrcmd_17.c)) | `checkpokedex(VAR)`, the Trainer Card, the save screen's owned count, the main menu, Connect to Pokémon Ranger (refuses without it) |
| `FLAG_GOT_POKEDEX` (0x6B) | `setflag` | the Start menu entry (`CheckGotPokedex` in [src/sys_flags.c](../../src/sys_flags.c)), a radio commercial |

Use both together. With only the flag the Start menu opens the Pokédex, but the Trainer
Card and the save screen show no count; with only `givepokedex` there's no menu entry.

**Seen and caught are recorded before the player has the Pokédex.** Nothing checks
`dexEnabled` when setting them: the starter, the first rival battle and anything else
before Mr. Pokémon's house are already in the Pokédex when Oak hands it over.

To start the game with it, add the two lines to the New Game `init` script
([new-game.md](new-game.md)).

## 3. The Johto order

Before the National Dex, the Pokédex lists the Johto Pokédex: 256 species in their own
order. The Pokédex, the summary, the PC and the "caught" popup in battle show the Johto
number (`Pokedex_ConvertToCurrentDexNo` in [src/pokedex_util.c](../../src/pokedex_util.c)).

Three things define it, and they must agree:

| What | File | Read by |
|---|---|---|
| The **numbers**: a `u16` per species, its Johto number or 0 | `files/poketool/johtozukan.narc` (one member; binary) | `SpeciesToJohtoDexNo`, `LoadSpeciesToJohtoDexNoLUT` ([src/pokemon.c](../../src/pokemon.c)): the numbers shown, Johto counts, the "regional" catch score (`Encounter_AddBattleScore`) |
| The **list**: species in Johto order | `johto` in the `dex_order` group of `files/application/zukanlist/zkn_data/zukan_data.json` | the Pokédex list and search in Johto mode ([src/application/pokedex/pokedex_search.c](../../src/application/pokedex/pokedex_search.c)) |
| The **count** | `J_NUM_SPECIES` in [include/constants/johto_dex.h](../../include/constants/johto_dex.h) | `Pokedex_JohtoDexIsComplete` |

The Pokédex assumes entry *n* of the list is Johto number *n* + 1, so the list order and the
numbers must match. The easy way to keep them matched is to **edit only the list** and
regenerate the numbers from it.

### Changing it

1. Edit the `johto` list in `zukan_data.json`: reorder, add or remove species. Any
   species from the national list can go in it.
2. Regenerate the numbers. Save this script (outside the repository, for example as
   `johto.py`) and run it from the repository root:

   ```python
   import json, re, struct, sys
   species = {m[0]: int(m[1]) for m in re.findall(r'#define (SPECIES_\w+)\s+(\d+)', open('include/constants/species.h').read())}
   data = json.load(open('files/application/zukanlist/zkn_data/zukan_data.json', encoding='utf-8'))
   lists = {o['id']: o['mons'] for g in data['sorting'] if g['type'] == 'dex_order' for o in g['options']}
   numbers = [0] * (len(lists['national']) + 1)          # species 0 to the last national species
   for n, name in enumerate(lists['johto'], 1):
       numbers[species[name]] = n
   open(sys.argv[1], 'wb').write(struct.pack('<%dH' % len(numbers), *numbers))
   print(len(lists['johto']), 'species in the Johto Pokédex')
   ```

   and pack its output into the archive with `nitroarc`
   ([adding-a-species.md §0](adding-a-species.md#0-before-you-start)):

   ```sh
   NARC=build/heartgold.us/tools/nitroarc/nitroarc
   mkdir -p /tmp/narc && cp files/poketool/johtozukan.narc /tmp/narc/
   $NARC -xf /tmp/narc/johtozukan.narc
   python3 johto.py /tmp/narc/johtozukan.narc.d/00000.bin
   ls /tmp/narc/johtozukan.narc.d | sort > /tmp/narc/order.txt
   $NARC -cf files/poketool/johtozukan.narc -T /tmp/narc/order.txt /tmp/narc/johtozukan.narc.d
   ```

   On the unchanged list this gives back the shipped `johtozukan.narc` byte for byte.
3. Set `J_NUM_SPECIES` to the length of the list (the script prints it).
4. If Mew or Celebi left the list, or another mythical joined it, update
   `sJohtoMythicals` in [src/pokedex.c](../../src/pokedex.c): they don't count towards
   completion.
5. Professor Oak's Johto rating counts to a fixed number: in `GetOakJohtoDexRating`
   ([src/field_misc_util.c](../../src/field_misc_util.c)) change `if (count <= 253)` to
   `if (count <= J_NUM_SPECIES - 3)` and include `constants/johto_dex.h`
   ([adding-a-species.md](adding-a-species.md#in-the-johto-pokédex), step 4). The
   messages for the lower brackets stay at their fixed counts; adjust them if the
   Pokédex is much smaller or larger.

The other sort lists (`alphabetical`, `heaviest`, types, ...) hold every national species
and are filtered by the current list, so they don't need changing.

A species outside the Johto list still gets registered when seen or caught, but doesn't
appear in the Pokédex, and its Johto number is 0, until the National Dex is unlocked.

## 4. The National Dex

`nationalDex` in the save switches the Pokédex to the national list and the national
numbers everywhere. In the vanilla game Oak unlocks it on the S.S. Aqua after the Elite
Four: Lance's room sets `VAR_UNK_411A = 1`, and the frame script in
`SsAquaOlivinePortInterior` runs the scene ([story-progression.md](story-progression.md)):

```
natdexflagaction(1, VAR_SPECIAL_RESULT)    # unlock; the variable is set to 0
enablemassoutbreaks                         # separate: starts swarms
```

`natdexflagaction(2, VAR)` sets `VAR` to 1 if it is unlocked, 0 if not. Any other first
argument is an error. Unlocking also sets a flag in the player profile, which nothing
reads.

To unlock it at another point, put `natdexflagaction(1, VAR_SPECIAL_RESULT)` in that
script (in the New Game `init` script to have it from the start). There's no command to
lock it again.

**What else it changes.** Besides the Pokédex itself, the flag is read by:

| What | Where | With the National Dex |
|---|---|---|
| Numbers in summary, PC, battle popup, Battle Frontier, Pokéwalker... | `natDexEnabled` arguments, `SaveArray_IsNatDexEnabled` | national numbers |
| Bug-Catching Contest | [src/overlay_bug_contest.c](../../src/overlay_bug_contest.c) | the Tuesday/Thursday/Saturday encounter sets; contestants' national Pokémon; a random first prize |
| Pokéathlon Dome shops | `ScrCmd_PokeathlonDailyMart` and the prize exchange, [src/scrcmd_mart.c](../../src/scrcmd_mart.c) | a second set of prices and items |
| Pokéwalker | [src/application/pokewalker/pokewalker_ui.c](../../src/application/pokewalker/pokewalker_ui.c) | courses 9-20 can unlock with watts |
| Safari Zone | Baoba's calls ([src/gear_phone_ring_manager.c](../../src/gear_phone_ring_manager.c)) and `SafariZoneEntranceInterior` scripts | later Safari Zone tests |
| Pokémon Music radio | [src/application/pokegear/radio/shows/pokemon_music.c](../../src/application/pokegear/radio/shows/pokemon_music.c) | the Hoenn (Wednesday) and Sinnoh (Thursday) tunes |
| Main menu | [src/application/main_menu/main_menu.c](../../src/application/main_menu/main_menu.c) | looks for a GBA game in slot 2 (for Pal Park) |
| Oak on the phone, Oak's PC rating | [src/application/pokegear/phone/scripts/phone_scripts_prof_oak.c](../../src/application/pokegear/phone/scripts/phone_scripts_prof_oak.c), `scr_seq_0148.s` | the national rating is offered |
| Cliff Cave, Pokéathlon Friendship Room scripts | `natdexflagaction(2, ...)` in their `scripts.pory` | their own checks |
| Wi-Fi Plaza and Club profiles | `hasNationalDex` | shown to other players |

Unlocking it early opens all of these early too. To unlock the Pokédex mode but keep one
of them on the old schedule, make that check test a story flag instead.

## 5. Seen and caught

### What sets them

| Event | Sets | Code |
|---|---|---|
| An enemy Pokémon is sent out (wild, trainer; not link or Frontier) | seen | `BattleSystem_SetPokedexSeen` ([src/battle/battle_system.c](../../src/battle/battle_system.c)) |
| A wild Pokémon is caught | caught | `BattleSystem_SetPokedexCaught` |
| The player's Burmy is sent out | caught (records its form) | `BattleSystem_SetPokedexSeen` |
| `givemon`, the starter, a trade (NPC, GTS, wireless), a Mystery Gift, an egg hatching | caught | `UpdatePokedexWithReceivedSpecies` ([src/update_dex_received.c](../../src/update_dex_received.c)), which also counts it in the game stats |
| Evolution (and Shedinja appearing) | caught | [src/evolution_scene.c](../../src/evolution_scene.c) |
| Form changes (Giratina, Shaymin, Rotom, Deoxys) | caught, with the new form | the form commands in `scrcmd_c.c`, `scrcmd_pokemon_misc.c`, [src/overlay_94.c](../../src/overlay_94.c) |
| Pokéwalker | seen and caught | [src/application/pokewalker/pokewalker_stroll.c](../../src/application/pokewalker/pokewalker_stroll.c) |
| `setmonseenflag(SPECIES)` | seen | `ScrCmd_SetMonSeenFlag` ([src/scrcmd_c.c](../../src/scrcmd_c.c)) |

`giveegg` doesn't register anything: an egg is registered when it hatches.

Each of these takes a whole Pokémon and also records its gender, form, language and (for
the first Spinda) its spots. Species above `SPECIES_ARCEUS` are refused (`DexSpeciesIsInvalid`;
for new species see [adding-a-species.md §2](adding-a-species.md#2-five-checks-in-c)).

### From a script

**Seen**: `setmonseenflag(SPECIES_LUGIA)`, command 687. The argument can be a variable.
It makes a level 50 Pokémon of that species with a random personality and registers it,
so the gender (and for Unown the letter, for Spinda the spots) recorded is random.

**Caught**: there is no command. `givemon` registers the Pokémon it gives; to register a
species without giving one, add a command. The two below were added to a copy of the
repository and built for HeartGold (not played): one sets caught, the other reads the
state of a species, which no vanilla command does either. Follow
[script-commands.md §6](script-commands.md#6-adding-a-command):

1. In [src/scrcmd_c.c](../../src/scrcmd_c.c), after `ScrCmd_SetMonSeenFlag`:

   ```c
   BOOL ScrCmd_SetMonCaughtFlag(ScriptContext *ctx) {
       u16 species = ScriptGetVar(ctx);
       Pokemon *mon = AllocMonZeroed(HEAP_ID_FIELD3);
       CreateMon(mon, species, 50, USE_RANDOM_IVS, FALSE, 0, OT_ID_PLAYER_ID, 0);
       Pokedex_SetMonCaughtFlag(Save_Pokedex_Get(ctx->fieldSystem->saveData), mon);
       Heap_Free(mon);
       return FALSE;
   }

   BOOL ScrCmd_GetPokedexStatus(ScriptContext *ctx) {
       u16 species = ScriptGetVar(ctx);
       u16 *p_ret = ScriptGetVarPointer(ctx);
       Pokedex *pokedex = Save_Pokedex_Get(ctx->fieldSystem->saveData);
       if (Pokedex_CheckMonCaughtFlag(pokedex, species)) {
           *p_ret = 2;
       } else if (Pokedex_CheckMonSeenFlag(pokedex, species)) {
           *p_ret = 1;
       } else {
           *p_ret = 0;
       }
       return FALSE;
   }
   ```

   and declare both in [include/scrcmd.h](../../include/scrcmd.h).
2. Append `ScrCmd_SetMonCaughtFlag,` and `ScrCmd_GetPokedexStatus,` at the end of
   `gScriptCmdTable` ([src/data/fieldmap/script_cmd_table.h](../../src/data/fieldmap/script_cmd_table.h)).
   They become 853 and 854 if nothing else was added.
3. Add the macros at the end of [asm/macros/script.inc](../../asm/macros/script.inc),
   before `.endif`:

   ```
   	// Marks SPECIES as seen and caught in the Pokédex
   	.macro SetMonCaughtFlag species
   	.short 853
   	.short \species
   	.endm

   	// Sets VAR to 0 (not seen), 1 (seen) or 2 (caught) for SPECIES
   	.macro GetPokedexStatus species, var
   	.short 854
   	.short \species
   	.short \var
   	.endm
   ```

4. Use them:

   ```
   setmoncaughtflag(SPECIES_MEW)
   getpokedexstatus(SPECIES_LUGIA, VAR_SPECIAL_RESULT)
   if (var(VAR_SPECIAL_RESULT) == 2) {
       npcmsg("You've caught Lugia!")
   }
   ```

`SetMonCaughtFlag` calls `Pokedex_SetMonCaughtFlag` directly, so unlike `givemon` it
doesn't add to the "Pokémon caught" game stat or unlock the Jirachi Pokéwalker course; call
`UpdatePokedexWithReceivedSpecies(ctx->fieldSystem->saveData, mon)` instead for that. The
Pokémon it makes has the game's language, so it doesn't unlock the foreign entries.

There's no way to clear a seen or caught bit from a script, and nothing in the game does.

## 6. Counting and completion

| Command | Sets `VAR` to |
|---|---|
| `countjohtodexseen(VAR)`, `countjohtodexowned(VAR)` | seen / caught species that have a Johto number |
| `countnationaldexseen(VAR)`, `countnationaldexowned(VAR)` | seen / caught species 1 to `NATIONAL_DEX_COUNT` |
| `checkjohtodexcomplete(VAR)` | 1 if all `J_NUM_SPECIES` except Mew and Celebi are caught |
| `checknationaldexcomplete(VAR)` | 1 if all national species except the nine in `sNationalMythicals` are caught |
| `getdexevalresult(0 or 1, MSG_VAR, FANFARE_VAR)` | Oak's Johto (0) or national (1) rating: a message id and a fanfare |
| `checkpokedex(VAR)` | 1 if the player has the Pokédex (`dexEnabled`) |

The counts include mythicals; the completion checks and Oak's rating don't. The Trainer
Card and the save screen show the Johto caught count before the National Dex and the
national count after (`Pokedex_CountDexOwned`).

The completion checks are used in `Celadon_Condominiums_3F` (the Pokédex
certificates) and by Oak in `Pallet_TownOaksLab`; Oak's PC rating is the common script
`scr_seq_0148.s`. A "catch N Pokémon" reward is a `countjohtodexowned` and a comparison:

```
countjohtodexowned(VAR_SPECIAL_RESULT)
if (var(VAR_SPECIAL_RESULT) >= 50) {
    ...
}
```

## 7. Save compatibility

The commands in §5 and changes to the Johto order, to `J_NUM_SPECIES` or to when the
National Dex unlocks don't change the save layout. An old save keeps what it had
registered and gets the new Johto numbers. Only new species can grow `SAVE_POKEDEX`
([adding-a-species.md §0](adding-a-species.md#0-before-you-start),
[save-compatibility.md](save-compatibility.md)).
