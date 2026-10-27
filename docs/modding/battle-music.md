<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Battle music

> AI-generated; not affiliated with pret. See AI.md at the repository root.

How the game picks the music for a battle (by trainer class, wild species, region),
and how to pick it yourself: for one trainer, for a map, or from a script. Adding the
song itself is in [music.md](music.md#adding-a-song). The transition picked from the
same rows is in [battle-visuals.md](battle-visuals.md).

| pokeemerald | here |
|---|---|
| `TRAINER_ENCOUNTER_MUSIC_*` on each trainer (spotted-you music) | `sTrainerEncounterMusicParam`, per class, Johto and Kanto columns (`src/field_bgm.c:27`) |
| `GetBattleBGM` in `src/battle_setup.c` (switch on trainer class) | `sTrainerBattleIntroParams` + `sBattleIntroEffectsAndMusic` (`src/battle_intro_config.c`): class → row → transition **and** music |
| legendary music by species in `GetBattleBGM` | `sWildBattleIntroParams`, by species (`src/battle_intro_config.c:39`) |
| `gBattleTypeFlags`/map checks for special music | the Kanto swap, by map region (`src/battle_intro_config.c:196`) |
| `PlayBGM` of `MUS_VICTORY_*` in battle | `SEQ_GS_WIN1/2/3`, `SEQ_GS_WINBRAIN` (`src/battle/battle_controller_player.c:3577`) |

There is **no script command for battle music**, and no per-trainer or per-map field.
[Section 4](#4-recipes) adds them in a few lines of C.

## 1. When the music is chosen

1. A trainer who spots you plays its **eyes-meet** music: the std script
   (`files/fielddata/script/scr_seq/scr_seq_0953.s:1513`) runs `EncounterMusic`
   (`ScrCmd_EncounterMusic`, `src/scrcmd_battle.c:193`), which looks up the class in
   `sTrainerEncounterMusicParam`. Trainers you talk to (gym leaders) skip this.
2. When the battle starts, every field battle (`trainerbattle`, `wildbattle`, grass,
   Safari, Bug Contest, Trainer House, link) calls `BattleSetup_GetWildBattleMusic`
   once (`src/encounter.c`, `src/overlay_25.c:210`). Despite the name it is used for
   trainers too.
3. The transition task plays that song (`Task_BattleTransition`,
   `src/battle_transition_task.c:34`). It keeps playing for the whole battle.
4. Winning plays a victory song ([section 3](#3-victory-music)).

Because the song is fixed at step 2, a `playbgm` before the battle does nothing: the
transition replaces it.

## 2. How `BattleSetup_GetWildBattleMusic` picks

It turns the battle into a **row number** (`BattleSetup_GetTransitionAndMusicParam`,
`src/battle_intro_config.c:136`), takes the music from that row of
`sBattleIntroEffectsAndMusic` (`:88`), then applies the Kanto swap.

### The rows

Each row is `{ transition, music }`; transition `0xffff` means the normal one for
the map (`EncounterEffect_GetDefaultEffect`).

| Row | Who | Music |
|---|---|---|
| 0-7 | Johto gym leaders (Falkner ... Clair) | `SEQ_GS_VS_GYMREADER` |
| 8-15 | Kanto gym leaders (Brock ... Blue) | `SEQ_GS_VS_GYMREADER_KANTO` |
| 16-19 | Elite Four | `SEQ_GS_VS_GYMREADER` |
| 20 | Champion (Lance) | `SEQ_GS_VS_CHAMP` |
| 21 | Rival, Passerby | `SEQ_GS_VS_RIVAL` |
| 22, 23, 24 | Raikou, Entei, Suicune | `SEQ_GS_VS_RAIKOU`, `_ENTEI`, `_SUICUNE` |
| 25, 26 | Ho-Oh, Lugia | `SEQ_GS_VS_HOUOU`, `SEQ_GS_VS_LUGIA` |
| 27 | Groudon, Kyogre, Rayquaza | `SEQ_GS_VS_KODAI` |
| 28 | Mewtwo, Latios, Latias | `SEQ_GS_VS_NORAPOKE_KANTO` |
| 29 | Rocket Grunts | `SEQ_GS_VS_ROCKET` |
| 30-34 | Petrel, Proton, Archer, Ariana, Giovanni | `SEQ_GS_VS_ROCKET` |
| 35, 36 | Frontier single, link | `SEQ_GS_VS_TRAINER` |
| 37 | trainer double battle | `SEQ_GS_VS_TRAINER` |
| 38 | wild double battle | `SEQ_GS_VS_NORAPOKE` |
| 39 | (nothing returns it) | `SEQ_GS_BA_BRAIN` |
| 40 | (nothing returns it) | `SEQ_GS_VS_GYMREADER` |
| 41 | any other trainer | `SEQ_GS_VS_TRAINER` |
| 42 | any other wild Pokémon | `SEQ_GS_VS_NORAPOKE` |
| 43 | Kimono Girls | `SEQ_GS_VS_TRAINER` (own transition) |
| 44 | Red | `SEQ_GS_VS_CHAMP` |

### Trainer battles

The **class of the first opponent** (`setup->trainer[BATTLER_ENEMY]`) is looked up in
`sTrainerBattleIntroParams` (`:53`); not found gives row 41. Then:

- Rocket rows (29-34), Kimono Girls (43) and Red (44) are kept in every battle type.
- Otherwise a **double battle gives row 37**, a link battle row 36. So a gym leader,
  Lance or the rival in a double battle gets the normal trainer music.
- Frontier battles give 35 (single) or 37 (double).

### Wild battles

Pal Park always gives row 42. Otherwise the **species of the first healthy Pokémon
in the enemy party** is looked up in `sWildBattleIntroParams` (`:39`); not found gives
row 42, and row 42 in a double battle becomes 38. Legendaries keep their music in
doubles.

### The Kanto swap

After the row (`:196`): once the player has the Vermilion fly point
(`FLYPOINT_VERMILION`) **and** the map's `"region"` is `MAP_REGION_KANTO`,

| Row music | becomes |
|---|---|
| `SEQ_GS_VS_NORAPOKE` | `SEQ_GS_VS_NORAPOKE_KANTO` |
| `SEQ_GS_VS_TRAINER` | `SEQ_GS_VS_TRAINER_KANTO` |
| `SEQ_GS_VS_GYMREADER` | never: the check calls `BattleIntroConfig_AlwaysTrue`, so it is dead code. Kanto leaders have their own rows |

So Routes 26-28 and Victory Road, which are Kanto maps, keep the Johto music until
the player has been to Vermilion. The region is per map, in `data/maps/<Map>/map.json`.

### Not through this function

| Battle | Music from |
|---|---|
| Battle Frontier facilities | their own scripts: `Sound_SetSceneAndPlayBGM(5, SEQ_GS_VS_TRAINER, 1)` (`src/frontier/frontier_script_commands_misc.c:146`, `frontier_script_commands_ext.c:687`, `:1389`, `frontier_cmd_hall.c:105`); Frontier Brains `SEQ_GS_BA_BRAIN` (`FrtCmd_BrainIntro`, `frontier_script_commands_ext.c:1551`) |
| VS Recorder replays | `src/vs_recorder_app.c:196` |

## 3. Victory music

| Win | Song | Where |
|---|---|---|
| trainer | `SEQ_GS_WIN1` | `src/battle/battle_controller_player.c:3612` |
| gym leaders, Elite Four, Champion | `SEQ_GS_WIN3` | `:3581-3602`, a `switch` on the opponent's class |
| Frontier Brains | `SEQ_GS_WINBRAIN` | `:3604-3609` |
| last wild Pokémon fainted | `SEQ_GS_WIN2` | `src/battle/battle_command.c:6044` |
| wild Pokémon caught | `SEQ_GS_WIN2` | `src/battle/battle_command.c:6781` |

Red and the rival aren't in the `switch`, so they get `SEQ_GS_WIN1`. A new class
goes in the `switch` to get another victory song.

## 4. Recipes

All of these are in `src/battle_intro_config.c` unless said otherwise. Use any
`SEQ_*`; a new song for battles should use `"player": "PLAYER_BGM"` and a battle bank
(`BANK_BGM_BATTLE1`-`8`) in `sound/sound_data.json` ([music.md](music.md#2-its-entry)).

### 4.1 A trainer class

Add a row to `sTrainerBattleIntroParams` and raise its size (`[32]` → `[33]`). Point
it at an existing row if one has the transition and music you want:

```c
    { TRAINERCLASS_SAGE,             21 }, // rival transition and music
```

For another combination, add a row at the end of `sBattleIntroEffectsAndMusic`
(`[45]` → `[46]`) and use its number:

```c
    { 0xffff, SEQ_GS_VS_RIVAL           }, // 45: normal transition, rival music
```

```c
    { TRAINERCLASS_SAGE,             45 },
```

In double battles the class is ignored ([above](#trainer-battles)). To keep it, add
a check next to the ones for 43 and 44 in `BattleSetup_GetTransitionAndMusicParam`:

```c
        if (param == 45) {
            return param;
        }
```

Eyes-meet music for the class is a row in `sTrainerEncounterMusicParam`
(`src/field_bgm.c:27`): class, music on Johto maps, music on Kanto maps. A class
without a row plays `SEQ_GS_EYE_J_SHOUNEN`.

### 4.2 One trainer

Classes are shared (every Youngster), so for one trainer add a table by trainer id.
In `BattleSetup_GetWildBattleMusic`, after `varsFlags` is set:

```c
// Battle music for single trainers, by trainer id.
static const u16 sTrainerBattleMusic[][2] = {
    { TRAINER_RIVAL_SILVER, SEQ_GS_VS_CHAMP },
};
```

```c
    if ((setup->battleType & BATTLE_TYPE_TRAINER) && !(setup->battleType & (BATTLE_TYPE_FRONTIER | BATTLE_TYPE_LINK))) {
        for (u32 i = 0; i < NELEMS(sTrainerBattleMusic); i++) {
            if (sTrainerBattleMusic[i][0] == setup->trainerId[BATTLER_ENEMY]) {
                return sTrainerBattleMusic[i][1];
            }
        }
    }
```

Add `#include "constants/trainers.h"`. The id is the first trainer of
`trainerbattle` (`setup->trainerId`, set in `SetupAndStartTrainerBattle`,
`src/encounter.c:719`). This works for trainers who spot you too, and in doubles.
The transition stays the class's.

### 4.3 A species

A row in `sWildBattleIntroParams` (size `[11]` → `[12]`), with a row number from the
table or a new row as in 4.1:

```c
    { SPECIES_ARTICUNO, 28 }, // Mewtwo's music and transition
```

It counts for every battle where that species leads the enemy party: grass,
`wildbattle`, fishing. The key is 10 bits, so species up to 1023.

### 4.4 A map

The usual music on one map (a Rocket base, a final dungeon), leaving gym leaders and
legendaries alone. Replace only the two ordinary themes, before the Kanto swap:

```c
typedef struct MapBattleMusic {
    u16 map;
    u16 wild;    // replaces SEQ_GS_VS_NORAPOKE
    u16 trainer; // replaces SEQ_GS_VS_TRAINER
} MapBattleMusic;

static const MapBattleMusic sMapBattleMusic[] = {
    { MAP_TEAM_ROCKET_HEADQUARTERS_B1F, SEQ_GS_VS_ROCKET, SEQ_GS_VS_ROCKET },
};
```

```c
    for (u32 i = 0; i < NELEMS(sMapBattleMusic); i++) {
        if (sMapBattleMusic[i].map == setup->mapNumber) {
            if (music == SEQ_GS_VS_NORAPOKE) {
                return sMapBattleMusic[i].wild;
            }
            if (music == SEQ_GS_VS_TRAINER) {
                return sMapBattleMusic[i].trainer;
            }
        }
    }
```

The map header has no room for a new field (`include/map_header.h`: one spare bit,
`runningAllowed_Unused`), so it is a table. For a whole region, change the Kanto swap
instead: drop the `FLYPOINT_VERMILION` check to have Kanto music on Kanto maps from
the start, or test `MapHeader_GetRegionNo(...) == MAP_REGION_JOHTO` to give Johto
other music.

### 4.5 From a script

A var the script sets before the battle; 0 means "choose as usual". `VAR_UNK_4152`
is free ([unknown-flags-vars.md](unknown-flags-vars.md#free-vars)). In
`include/constants/vars.h`, rename it:

```c
#define VAR_BATTLE_MUSIC                   0x4152
```

In `BattleSetup_GetWildBattleMusic`, right after `varsFlags` is set (so it wins over
everything else):

```c
    u16 scriptMusic = GetScriptVar(varsFlags, VAR_BATTLE_MUSIC);
    if (scriptMusic != 0) {
        return scriptMusic;
    }
```

with `#include "constants/vars.h"` and `#include "sys_vars.h"`. In the script:

```
    setvar(VAR_BATTLE_MUSIC, SEQ_GS_VS_CHAMP)
    trainerbattle(TRAINER_LEADER_FALKNER_FALKNER, 0, 0, 0)
    setvar(VAR_BATTLE_MUSIC, 0)
    checkbattlewon(VAR_SPECIAL_RESULT)
```

Clear it **right after** the battle command, before `checkbattlewon`: the losing
branch ends with `whiteout`, and a var left set gives every later battle, wild ones
too, that music. The var is saved, so it also survives a save made in between. It
works the same with `wildbattle`. It doesn't change the transition.

Then regenerate the free-var list:
`python3 tools/flagusage/flagusage.py --markdown > docs/modding/unknown-flags-vars.md`.

### Order, if you add all three

script var → one trainer → class/species row → map → Kanto swap. That is the order
of the code above; move the blocks to change it.

## 5. GB Sounds

With the GB Sounds item on, `src/sound_gb.c:132-143` replaces the 12 Johto/Kanto battle
themes (wild, trainer, leader, rival, Rocket, beasts, champion) with Game Boy
versions. Songs without a row (Ho-Oh, Lugia, `SEQ_GS_VS_KODAI`, new songs) play
normally.

## Not verified

- Recipes 4.1 (a Sage row 45 with rival music), 4.2 (`TRAINER_RIVAL_SILVER` →
  `SEQ_GS_VS_CHAMP`) and 4.4 (Rocket HQ B1F, plus Route 29 with the Kanto themes)
  were built together into a HeartGold ROM with `make release`. 4.5 was built
  separately with the `vars.h` rename and the script lines above in
  `data/maps/Violet_Gym/scripts.pory`; the generated script has the two `SetVar`s
  around `TrainerBattle`. Both were reverted and all four checksums matched. Nothing
  was played in game.
- That `Task_BattleTransition` replaces a song a script started before the battle is
  read from the code, not heard.
- Whether any field battle reaches rows 35 or 39 (Frontier) wasn't traced; the
  facilities shown above set their music themselves.
