<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Battle visuals: transitions, mugshots, Poké Balls

> AI-generated; not affiliated with pret. See AI.md at the repository root.

What you see when a battle starts and when Pokémon come out: the screen transition
(including the gym leader, Elite Four and Rocket "mugshots"), the Poké Ball graphics,
and which ball a trainer's Pokémon come out of. Backgrounds and platforms have their
own guide, [battle-backgrounds.md](battle-backgrounds.md). Trainer sprites are in
[trainer-classes.md](trainer-classes.md#trainer-sprites). Battle music is chosen from
the same table as the transition ([battle-music.md](battle-music.md)).

| pokeemerald | here |
|---|---|
| `B_TRANSITION_*` and `sTasks_*` in `src/battle_transition.c` | 47 encounter effects (ids 0-46), one callback each in `gEncounterEffectFuncs` (`asm/encounter_effect_data.s:92`), spread over overlays 114-120 |
| `GetWildBattleTransition` / `GetTrainerBattleTransition` (level and terrain) | `EncounterEffect_GetDefaultEffect` (`src/field/encounter_effect_util.c:384`): terrain and time of day only, no level check |
| `sTrainerClassTransitions`-style special cases for leaders | `sTrainerBattleIntroParams` → a row of `sBattleIntroEffectsAndMusic` (`src/battle_intro_config.c:53`, `:88`): class → row → transition **and** music |
| `B_TRANSITION_MUGSHOT` + `sMugshotsTrainerPicIDsTable` (uses the trainer's front sprite) | a separate 96×64 picture per leader in the binary archive `files/a/1/0/9`; one params struct per leader |
| `gBallSpriteSheets` / `gBallParticleSpritesheets` (`src/pokeball.c`) | `gBallSpriteResources` (PNG in `graphics/battle_sprites/balls/`), `gBallAnimBurstParticles` / `gBallAnimSealParticles` (`asm/battle_anim_data.s`), particles in binary `files/a/0/9/5` |
| `gTrainerBallTable` / `.ball` in `trainers.h` (per trainer class) | **nothing**: every NPC trainer's Pokémon is in a Poké Ball. [Section 5](#5-which-ball-a-trainers-pokémon-come-out-of) adds a per-class and a per-trainer ball |

## 1. How a transition is picked

Every field battle (`trainerbattle`, `wildbattle`, grass, fishing, Safari, Bug
Contest, Trainer House) calls `BattleSetup_GetWildTransitionEffect`
(`src/battle_intro_config.c:186`) and `BattleSetup_GetWildBattleMusic` together
(`src/encounter.c`, `src/overlay_25.c:209`). Both names say "wild"; both are used for
trainers too. `Task_BattleTransition` (`src/battle_transition_task.c`) loads the
effect's overlay, runs it and starts the music.

1. The battle becomes a **row number** (`BattleSetup_GetTransitionAndMusicParam`,
   `:136`): by the first opponent's trainer class, or by the species of the first
   wild Pokémon. The rules (doubles, Frontier, link, Pal Park) and the row list are in
   [battle-music.md §2](battle-music.md#2-how-battlesetup_getwildbattlemusic-picks).
2. The row's `transition` is the effect id. `0xffff` means "the normal one":
   `EncounterEffect_GetDefaultEffect`.

No script command chooses a transition ([recipe 4.2](#42-from-a-script) adds one).

### The normal transition

`EncounterEffect_GetDefaultEffect` (`src/field/encounter_effect_util.c:384`):

| Terrain | Wild | Trainer |
|---|---|---|
| `TERRAIN_WATER` | 2 (waves) | 8 |
| `TERRAIN_CAVE` | 4 (diagonals) | 10 |
| anything else (grass, plain, sand, building, snow...) | 0 (rows of squares) | 6 |

and **+1 at night** (`RTC_TIMEOFDAY_NITE` or `LATE`). Only the flash colour changes
with the +1 (white by day, black by night; `encounter_effect_wild.c:679`).

The terrain is the tile you stand on, else the map's battle background
([battle-backgrounds.md](battle-backgrounds.md#the-platforms-terrain)); surfing and
fishing give water. Maps with a cave background are always night in battle
(`src/battle/battle_setup.c:212-220`), so in caves you get 5 or 11.

There is **no level comparison** (pokeemerald picks a different transition when your
lead is stronger). Terrains `TERRAIN_WILL` ... `TERRAIN_GIRATINA` (12-22) aren't in the
`switch`, so `effect` is uninitialized there; retail never reaches it because those
battles use fixed rows.

### Every effect

| Id | What | Callback (file) | Overlay | Used by (row) |
|---|---|---|---|---|
| 0-5 | wild: rows / waves / diagonals, day and night | `EncounterEffect_Wild*` (`encounter_effect_wild.c`) | 120 | normal wild battle |
| 6-11 | trainer: spin apart, spin zoom, ball drop, fade spin, ball fall, rising ball | `EncounterEffect_Trainer*` (`encounter_effect_trainer.c`) | 119 | normal trainer battle |
| 12-27 | **mugshot**, gym leaders Falkner ... Clair, Brock ... Blue | `EncounterEffect_Leader*` (`encounter_effect_leaders.c`) | 115 | rows 0-15 |
| 28 | mugshot, rival | `EncounterEffect_Rival` | 115 | row 21 (Rival, Passerby) |
| 29-32 | Elite Four: you and them slide in | `EncounterEffect_EliteFour*` | 115 | rows 16-19 |
| 33 | Champion (Lance), same as 29-32 | `EncounterEffect_Champion` | 115 | row 20 |
| 34 | camera pan (Groudon, Kyogre, Rayquaza, Mewtwo, Latios, Latias) | `EncounterEffect_Legendary` (`overlay116_scene.c`) | 116 | rows 27, 28 |
| 35, 36 | Ho-Oh, Lugia | `EncounterEffect_HoOh`, `_Lugia` | 116 | rows 25, 26 |
| 37 | Frontier or link single | `EncounterEffect_FrontierOrLinkSingle` (`encounter_effect_frontier_link.c`) | 114 | rows 35, 36, 39 |
| 38 | double battle | `EncounterEffect_Double` | 114 | rows 37, 38, 40 |
| 39 | Rocket Grunts: six "R"s fly in | `EncounterEffect_TeamRocket` (`encounter_effect_rocket.c`) | 117 | row 29 |
| 40-44 | mugshot, Petrel, Proton, Archer, Ariana, Giovanni | `EncounterEffect_Executive*`, `_RocketBoss` | 117 | rows 30-34 |
| 45 | Kimono Girls: two halves slide in | `EncounterEffect_KimonoGirl` (`encounter_effect_kimono_girl.c`) | 118 | row 43 |
| 46 | Red: squares in random order, two flashes | `EncounterEffect_PkmnTrainerRed` (in `encounter_effect_wild.c`) | 120 | row 44 |

The raikou/entei/suicune rows (22-24) use the normal transition. The overlay is picked
by id ranges written out in `EncounterEffect_LoadOverlay` and `_UnloadOverlay`
(`src/field/encounter_effect.c:69`, `:101`); any id not listed loads overlay 114. All
seven overlays share one load address, so only one is in memory at a time.

`gEncounterEffectFuncs[effect]` is called with **no bounds check**
(`encounter_effect.c:63`): an id past the table end jumps to garbage.

## 2. The mugshots

Every effect opens the same archive, `files/a/1/0/9` (`EncounterEffect_Start`,
`encounter_effect.c:143`). It is a **prebuilt binary NARC** with 242 members and no
names; nothing under `graphics/` builds it. The Frontier Brain intros use it too
(`src/frontier/frontier_brain_intro.c:189`, members 169-204).

### Gym leaders and the rival (12-28)

`LeadersEffect_RunGymLeaderIntro` (`src/field/encounter_effect_leaders.c:276`). The
screen flashes, a zigzag wipe opens a scrolling band on BG3, the leader's picture
slides in from the right as a dark silhouette (palette blended 14/16 to black,
`:305`), four "scale" sprites pop in, the picture lights up and the name appears.

Each callback passes its own `GymLeaderIntroParams` (Falkner's at `:194`); there is no
table by effect id:

```c
static const GymLeaderIntroParams sEncounterLeaderErikaIntroParams = {
    .endX = FX32_CONST(214),                    // where the picture stops sliding
    .trainerId = TRAINER_LEADER_ERIKA_ERIKA,    // whose name is printed
    .trainerClass = TRAINERCLASS_LEADER_ERIKA,  // only checked for TRAINERCLASS_RIVAL
    .unk_0A = 1,                                // never read
    .spriteMembers = { 107, 108, 109, 110 },    // palette, character, cell, animation
    .bgMembers = { 30, 29, 31 },                // band: palette, character, screen
};
```

The comment on the struct (`include/field/encounter_effect_leaders.h:24`) says
"character, palette, cell, animation". That is wrong: the order is **palette first**
(`EncounterEffect_LoadSpriteResources`, `encounter_effect_util.c:94`). The same wrong
comment is at `encounter_effect_rocket.c:50`.

| Trainer | Picture (pal, char, cell, anim) | Band (pal, char, screen) |
|---|---|---|
| Falkner / Brock | 63-66 / 95-98 | 21, 20, 22 |
| Bugsy / Misty | 67-70 / 99-102 | 24, 23, 25 |
| Whitney / Lt. Surge | 71-74 / 103-106 | 27, 26, 28 |
| Morty / Erika | 75-78 / 107-110 | 30, 29, 31 |
| Jasmine / Janine | 79-82 / 111-114 | 33, 32, 34 |
| Chuck / Sabrina | 83-86 / 115-118 | 36, 35, 37 |
| Pryce / Blaine | 87-90 / 119-122 | 39, 38, 40 |
| Clair / Blue | 91-94 / 123-126 | 42, 41, 43 |
| Rival | 127-130 | 45, 44, 46 |

Shared by all: 16 (the name's BG palette), 59-62 (the scale sprites). Each picture is
a 96×64, 16-colour sprite with one palette.

**The name is text, not part of the picture.** It is `msg_0189` entry 0 (just
`{STRVAR_1 3, 0, 0}`), filled with `BufferTrainerName(params->trainerId)`
(`encounter_effect_leaders_util.c:78`). It is the name of the **trainer id in the
params**, not of the trainer you are fighting: a rematch trainer, or another class
pointed at Falkner's row, still shows "FALKNER". For `TRAINERCLASS_RIVAL` the rival's
saved name is used. Passerby (the early "Boy" rival) shares the rival's row, so it
shows the rival's name too.

### Elite Four and Champion (29-33)

`LeadersEffect_RunEliteFourIntro` (`encounter_effect_leaders.c:577`), params at
`:73-111`. Your sprite (members 207-210 male, 211-214 female) and theirs (Will 131-134,
Koga 135-138, Bruno 139-142, Karen 143-146, Lance 147-150) slide in from both sides.
The field `nameplateMember` (47, 51, 52, 53, 54) is **not a nameplate**: it is the
palette for the shared streak sprite 48-50. The name is printed as text, as above.
Particles are SPA members 151, 152.

### Rocket (39-44)

Executives and Giovanni: `RocketEffect_RunExecutiveIntro` (`encounter_effect_rocket.c`),
pictures Petrel 222-225, Proton 226-229, Archer 230-233, Ariana 234-237, Giovanni
238-241 (`:82-105`); backgrounds 215-218, 221. Names as text. Grunts (39) use one "R"
sprite (palette 3, char 156, cell 158, anim 157).

## 3. Changing a mugshot picture

The members are uncompressed and convert both ways without loss (tested on Falkner:
tiles, palette and the repacked archive came back byte-identical). The steps are the
ones in [graphics.md §4](graphics.md#4-changing-a-binary-archive), with these numbers:

```bash
T=$PWD/build/heartgold.us/tools
GFX=$T/nitrogfx/nitrogfx
ARC=$T/nitroarc/nitroarc
W=/tmp/mugshot                       # anywhere outside the repository
mkdir -p $W && cp files/a/1/0/9 $W/109.narc
$ARC -xf $W/109.narc                 # -> $W/109.narc.d/00000.NCLR ... 00241.NANR

cd $W                                # Falkner: palette 63, tiles 64, cells 65
cp 109.narc.d/00063.NCLR f.NCLR
cp 109.narc.d/00064.NCGR f.NCGR
cp 109.narc.d/00065.NCER f.NCER
$GFX f.NCER f.json
$GFX f.NCLR f.pal
$GFX f.NCGR f.png -palette f.NCLR -cell f.json -object     # 96x64, 4-bit indexed

# ... edit f.png (keep it indexed, 16 colours) and/or f.pal ...

$GFX f.png f.NCGR -cell f.json -clobbersize -version101 -mappingtype 32
$GFX f.pal f.NCLR -bitdepth 4
cp f.NCGR 109.narc.d/00064.NCGR
cp f.NCLR 109.narc.d/00063.NCLR
(cd 109.narc.d && $ARC -cf $W/109.narc .)
cp $W/109.narc ~/path/to/pokeheartgold-modding/files/a/1/0/9
```

Then `make release`. Keep the picture inside the same 96×64 cell layout; for another
shape, edit `f.json` too ([graphics.md §8](graphics.md#8-cells-and-animations)).
`python3 tools/narcgfx/narcgfx.py flags files/a/1/0/9 --nitrogfx $GFX` lists the flags
for every member (bands are NCGR/NSCR pairs with their own flags). To turn the whole
archive into a PNG folder built by `meson`, follow
[graphics-sources.md §8](graphics-sources.md#8-converting-another-archive).

Remember the palette is loaded twice, the second time darkened for the silhouette:
colour 0 is transparent, and very dark colours will vanish into the silhouette.

## 4. Recipes

### 4.1 Another existing transition for a class

Point the class at another row in `sTrainerBattleIntroParams`, or add a row
to `sBattleIntroEffectsAndMusic` with the effect id and music you want: see
[battle-music.md §4.1](battle-music.md#41-a-trainer-class), which also shows how to
keep it in double battles. A mugshot borrowed this way shows the original trainer's
name and picture.

### 4.2 From a script

A var the script sets before the battle. Effect 0 is a real effect, so store **id + 1**
and keep 0 for "as usual". `VAR_UNK_4153` is free
([unknown-flags-vars.md](unknown-flags-vars.md#free-vars); battle-music.md's recipe
uses 4152). In `include/constants/vars.h`:

```c
#define VAR_BATTLE_TRANSITION              0x4153
```

In `BattleStartGetTransition` (`src/battle_intro_config.c:171`), first thing:

```c
    u16 scriptTransition = GetScriptVar(Save_VarsFlags_Get(setup->saveData), VAR_BATTLE_TRANSITION);
    if (scriptTransition != 0) {
        return scriptTransition - 1;
    }
```

with `#include "constants/vars.h"` and `#include "sys_vars.h"`. In the script:

```
    setvar(VAR_BATTLE_TRANSITION, 33 + 1)    // Lance's
    trainerbattle(TRAINER_ELDER_LI, 0, 0, 0)
    setvar(VAR_BATTLE_TRANSITION, 0)
    checkbattlewon(VAR_SPECIAL_RESULT)
```

Clear it right after the battle command, before `checkbattlewon`, for the same reason
as the music var. Only use ids that exist (0-46, or yours): there is no bounds check.

### 4.3 A new mugshot

Example: Elder Li at the top of Sprout Tower gets a gym-leader style mugshot. The new
effect id is **47**, the next index in `gEncounterEffectFuncs`.

1. **Graphics.** Append four members to `a/1/0/9` (palette, tiles, cells, animation:
   `00242.NCLR`, `00243.NCGR`, `00244.NCER`, `00245.NANR`), made as in
   [section 3](#3-changing-a-mugshot-picture). The easiest start is copies of a
   leader's four members, then redraw the PNG. Never insert in the middle: code reads
   members by number. Reuse one of the nine bands, or add three more members for one.
   `spriteMembers` and `bgMembers` are `u8`, so **members 242-255 (14) are all that fit**
   before those fields need widening.
2. **The callback**, in `src/field/encounter_effect_leaders.c`, before
   `EncounterEffect_Rival`:

   ```c
   static const GymLeaderIntroParams sEncounterElderLiIntroParams = {
       .endX = FX32_CONST(214),
       .trainerId = TRAINER_ELDER_LI,
       .trainerClass = TRAINERCLASS_ELDER,
       .unk_0A = 1,
       .spriteMembers = { 242, 243, 244, 245 }, // palette, character, cell, animation
       .bgMembers = { 36, 35, 37 },             // Chuck's band: palette, character, screen
   };

   void EncounterEffect_ElderLi(SysTask *task, EncounterEffectTask *effect) {
       if (LeadersEffect_RunGymLeaderIntro(effect, HEAP_ID_FIELD1, &sEncounterElderLiIntroParams) == TRUE) {
           EncounterEffect_Finish(effect, task);
       }
   }
   ```

   and declare it at the end of `include/field/encounter_effect.h`:

   ```c
   void EncounterEffect_ElderLi(SysTask *task, EncounterEffectTask *effect);
   ```

3. **The table**, `asm/encounter_effect_data.s`: add `.public EncounterEffect_ElderLi`
   to the `.public` list at the top (the assembler fails with "Unknown identifier"
   otherwise), and a line at the end of `gEncounterEffectFuncs`:

   ```
   	.word EncounterEffect_PkmnTrainerRed
   	.word EncounterEffect_ElderLi
   ```

4. **The overlay.** In **both** `EncounterEffect_LoadOverlay` and
   `EncounterEffect_UnloadOverlay` (`src/field/encounter_effect.c`):

   ```c
       if ((effect >= 12 && effect <= 33) || effect == 47) {
   ```

   Without this, 47 loads overlay 114, which doesn't contain the leader code, and the
   game jumps into whatever is at that address.
5. **The row and the class**, `src/battle_intro_config.c`: raise
   `sBattleIntroEffectsAndMusic[45]` to `[46]` and add

   ```c
       { 47,     SEQ_GS_VS_TRAINER         }, // 45: Elder Li
   ```

   then raise `sTrainerBattleIntroParams[32]` to `[33]` and add

   ```c
       { TRAINERCLASS_ELDER,            45 },
   ```

   `param` is 6 bits (rows up to 63), the class key 10 bits. In double battles the row
   is replaced by 37 unless you add `if (param == 45) return param;` next to the checks
   for 43 and 44 in `BattleSetup_GetTransitionAndMusicParam`.

The class is a key, so every Elder gets this mugshot with Li's name. For one trainer
only, check `setup->trainerId[BATTLER_ENEMY]` in `BattleSetup_GetWildTransitionEffect`
(as [battle-music.md §4.2](battle-music.md#42-one-trainer) does for music) and return
47 directly.

An Elite Four style intro is the same with an `EliteFourIntroParams` and
`LeadersEffect_RunEliteFourIntro` (its four opponent members are consecutive from
`opponentMember`).

## 5. Which ball a trainer's Pokémon come out of

**Always a Poké Ball.** `CreateMon` sets `ITEM_POKE_BALL` (`src/pokemon.c:218-220`) and
`CreateNPCTrainerParty` (`src/trainer_data.c:274`) never changes it. There is no class
table and no field in `trainers.json`. Frontier Pokémon (`FrontierMon_ToPokemon`,
`src/frontier/frontier_trainers.c:186`) and Trainer House Pokémon
(`src/overlay_25.c:299`) don't set one either.

The battle reads every battler's ball the same way (`BattleSystem_GetMonBall`,
`src/battle/battle_system.c:243`, stored in `battleMons[].ball`): the send-out and
recall sprite, the flash colour on the Pokémon, the open particles, and the ball the
trainer holds at the start. So setting `MON_DATA_POKEBALL` on the party is all it
takes. Nothing outside battle shows an opponent's ball.

The per-Pokémon `"capsule"` in `trainers.json` is the **Ball Capsule** (seals), not the
ball: it replaces the open particles with the seal effect and keeps the ball. Only one
retail Pokémon uses one (Beauty Charlotte's Bellossom). `SetTrMonCapsule`
(`src/pokemon.c:4234`) reads capsule `capsule - 1` from the capsule data and always
stores id 1.

**Item id or ball id.** `SetMonData(MON_DATA_POKEBALL)` takes an **item** id
(`src/pokemon.c:1301`): `ITEM_MASTER_BALL` ... `ITEM_CHERISH_BALL` (1-16) and
`ITEM_FAST_BALL` ... `ITEM_SPORT_BALL` (492-499). Anything else, Park Ball included,
asserts and is ignored. `GetMonData` returns a **ball** id (`BALL_*`,
`include/constants/balls.h`); they are equal for 1-16 only. `ItemToBallId` /
`BallToItemId` (`src/item.c:451`, `:461`) convert.

### 5.1 By trainer class

In `src/trainer_data.c`, a function before `CreateNPCTrainerParty`:

```c
// The ball a trainer class's Pokémon come out of (an item id).
static u16 TrainerClass_GetBall(u32 trainerClass) {
    switch (trainerClass) {
    case TRAINERCLASS_RIVAL:
        return ITEM_ULTRA_BALL;
    case TRAINERCLASS_TEAM_ROCKET:
    case TRAINERCLASS_TEAM_ROCKET_F:
        return ITEM_DUSK_BALL;
    case TRAINERCLASS_FISHERMAN:
        return ITEM_LURE_BALL;
    default:
        return ITEM_POKE_BALL;
    }
}
```

and at the end of `CreateNPCTrainerParty`, after the `switch`, before
`Heap_Free(data);` (`:435`):

```c
    u16 ball = TrainerClass_GetBall(enemies->trainer[partyIndex].data.trainerClass);
    for (i = 0; i < Party_GetCount(enemies->party[partyIndex]); i++) {
        SetMonData(Party_GetMonByIndex(enemies->party[partyIndex], i), MON_DATA_POKEBALL, &ball);
    }
```

with `#include "constants/items.h"`. This covers trainers who spot you, `trainerbattle`,
and multi-battle partners (each trainer slot goes through `CreateNPCTrainerParty`,
`src/trainer_data.c:31-43`). It doesn't change personalities or the RNG (the seed is restored after).

### 5.2 By trainer

`TrainerData` has an unused byte, `unk_2` (`include/trainer_data.h:91`), which the
build always writes as `0` (`files/poketool/trainer/trdata.json.txt`). Use it for a
`BALL_*` id; a byte can't hold the Apricorn item ids, but it holds every ball id.

In `files/poketool/trainer/trdata.json.txt`, add `#include "constants/balls.h"` and
replace the `0,` after `{{ trainer.class }},`:

```
		{{ trainer.class }},
		{% if existsIn(trainer, "ball") %}{{ trainer.ball }}{% else %}0{% endif %},
```

In `trainers.json`, on the trainer (not on a Pokémon):

```json
      "type": "TRTYPE_MON_ITEM_MOVES",
      "class": "TRAINERCLASS_LEADER_FALKNER",
      "ball": "BALL_HEAVY",
```

and in `CreateNPCTrainerParty`, between the two lines of 5.1 (so the trainer wins
over the class):

```c
    if (enemies->trainer[partyIndex].data.unk_2 != BALL_NONE) {
        ball = BallToItemId(enemies->trainer[partyIndex].data.unk_2);
    }
```

with `#include "constants/balls.h"` and `#include "item.h"`. Trainer House sets
`unk_2` to 0 (`src/overlay_25.c:340`), so it isn't affected.

A ball per **Pokémon** needs a new `u16` in all four `TRPOKE_*` structs
(`include/trainer_data.h`) and a matching `.short` in `trpoke.json.txt` for every
Pokémon. The struct and the template must change together, or every party is read
at the wrong stride.

## 6. Poké Ball graphics

| Where | Graphics | Picked by | Editable? |
|---|---|---|---|
| battle: thrown, sent-out, recalled ball | `graphics/battle_sprites/balls/<ball>/` (`tiles.png`, `palette.pal`, cells, animation): members 83-109, 259-339 of `a/0/0/8` | `gBallSpriteResources[row]` = {char, palette, cell, anim} (`asm/battle_anim_data.s:1307`) | **yes**, PNG ([graphics-sources.md §6](graphics-sources.md#6-graphicsbattle_sprites-a008)) |
| battle: particles when the ball opens | SPA members 1-25 (no capsule) and 27-51 (bursts) of `files/a/0/9/5` | `gBallAnimSealParticles` (`:1259`), `gBallAnimBurstParticles` (`:1278`) | no, binary particles |
| battle: colour the Pokémon flashes as it appears | 25 RGB555 colours | `gBallColors[ball]` (`asm/battle_controller_opponent_data.s:28`) | raw bytes |
| summary screen, "caught in" | NCGR members 25-48 (balls 1-24), palettes 49-61 of `files/a/1/6/2` | tiles `ball + 24`, palette `sPokemonSummaryBallPalettes[ball] + 49` (`src/pokemon_summary.c:372`, `:2449`) | no, binary |
| wireless trade, choosing a Pokémon | same archive | `sWirelessTradeSelectMonBallPalettes` (`asm/wireless_trade_select_mon_data.s`) | no |
| bag | item icon in `data/items/items.json` | the item | yes, PNG ([items.md](items.md)) |
| following Pokémon, item balls on the map, trade, Pokéwalker | one generic ball for every type | | |

In battle, `BallAnim_GetBallTableIndex` (`src/battle/battle_anim_ball.c:197`) turns ball
1-24 into row `ball - 1`; anything else uses row 3, the Poké Ball. Rows 24-26 are Park
Ball, Safari rock and bait, reached through the special values `0x400`-`0x402`
(`battle_controller_opponent.c:3901-3922`). A Park Ball id (25) itself draws as a Poké
Ball.

**Redrawing a ball** in battle is a PNG edit in `graphics/battle_sprites/balls/<ball>/`
and `make release`. Its summary icon is in the binary `a/1/6/2`, changed as in
[graphics.md §4](graphics.md#4-changing-a-binary-archive).

### Adding a ball

A new ball (`BALL_DREAM` = 26, say) touches, beyond the item itself
([items.md](items.md)) and its catch rate
([party-menu-and-item-use.md](party-menu-and-item-use.md#4-using-an-item-in-battle)):

| What | Where |
|---|---|
| the id | `include/constants/balls.h` |
| item ↔ ball | `ItemToBallId`, `BallToItemId` (`src/item.c:451`, `:461`): both test two ranges |
| storing it | the range check in `SetMonData` (`src/pokemon.c:1301`); the DP field gets `BALL_POKE`, as for Apricorn balls. The summary keeps it in 6 bits (max 63) |
| battle sprite row | `BallAnim_GetBallTableIndex`; a new row in `gBallSpriteResources`, `gBallAnimSealParticles`, `gBallAnimBurstParticles` (all three are read by row); the sprite as new members at the end of `a/0/0/8` ([graphics-sources.md §7](graphics-sources.md#7-editing)) |
| flash colour | entries up to the new id in `gBallColors` (25 entries, 0-24; the next table follows, so a larger id reads garbage) |
| summary icon | a new NCGR member in `a/1/6/2` (member 49 is a palette, so `ball + 24` must be remapped for balls past 24) and an entry in `sPokemonSummaryBallPalettes` |

The rows in `asm/battle_anim_data.s` are raw `.byte` data whose labels fall in the
middle of a row (the table starts at the label before); read them as `u32` groups.
Particles can reuse an existing ball's members.

## 7. Where to look

| What | File |
|---|---|
| class/species → row → effect id | `src/battle_intro_config.c` |
| default effect | `src/field/encounter_effect_util.c:384` |
| effect table, overlay ranges | `asm/encounter_effect_data.s:92`, `src/field/encounter_effect.c:69` |
| mugshot code | `src/field/encounter_effect_leaders.c`, `encounter_effect_rocket.c` |
| mugshot graphics | `files/a/1/0/9` (binary) |
| ball tables | `asm/battle_anim_data.s:1259-1337`, `src/battle/battle_anim_ball.c` |
| trainer party creation | `src/trainer_data.c:274` |

## Not verified

- Recipes 4.2 (the var in `BattleStartGetTransition`), 4.3 (Elder Li, effect 47, with
  Falkner's four members copied to 242-245 and Chuck's band) and 5.1 + 5.2 (the class
  switch above, `"ball": "BALL_HEAVY"` on Falkner) were built together into a HeartGold
  ROM with `make release`. `EncounterEffect_ElderLi` linked into overlay 115, and
  Falkner's `trdata` entry came out with byte 2 = 0x14 (`BALL_HEAVY`). Everything was
  then reverted and `make` passed all four checksums. **Nothing was played in game**,
  so the new mugshot and balls were never seen on screen.
- The mugshot round trip (export Falkner's palette and tiles, convert back, repack
  `a/1/0/9`) gave byte-identical files; a redrawn picture wasn't tested in game.
- What the trainer effects 6-11 and the Frontier/double effects look like frame by
  frame was not checked; the names come from the code.
- "Adding a ball" is a list of what reads ball ids, not a tested recipe. The Park Ball
  (`ITEM_PARK_BALL` is rejected by `SetMonData`) wasn't traced through Pal Park.
- Which animation the wireless trade screen's ball (`ball + 7`) uses wasn't found.
