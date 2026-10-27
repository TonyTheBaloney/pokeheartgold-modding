<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# Trainer classes and trainer sprites

> AI-generated; not affiliated with pret. See AI.md at the repository root.

A trainer class ("Youngster", "Leader", "Rocket Boss") gives a trainer its title, its
battle sprite, its gender, its prize money and the music that plays when it spots
you. Individual trainers (names, parties, battle text) are covered in
[npcs-and-scripts.md](npcs-and-scripts.md#trainers); this page is about the classes
and their art.

The biggest difference from pokeemerald: **here the class number is also the
picture number.** pokeemerald has `TRAINER_CLASS_*` and `TRAINER_PIC_*` as separate
lists, and each trainer names both. In HeartGold the battle sprite is found by
`class × 5` in one archive, so a new look needs a new class, and two classes can't
share one picture.

| pokeemerald | here |
|---|---|
| `TRAINER_CLASS_*` in `include/constants/trainers.h` | `TRAINERCLASS_*` in `include/constants/trainer_class.h` |
| `TRAINER_PIC_*` | none: the class number picks the picture |
| `gTrainerClassNames` (`src/data/text/trainer_class_names.h`) | `files/msgdata/msg/msg_0730.json` (and `msg_0731.json`, the name with "a"/"an") |
| `gTrainerMoneyTable` (`src/battle_main.c`) | `sPrizeMoneyTbl` (`asm/overlay_12_battle_command.s`) |
| `F_TRAINER_FEMALE` on each trainer | `sTrainerGenders`, per class (`src/trainer_data.c`) |
| `TRAINER_ENCOUNTER_MUSIC_*` on each trainer | `sTrainerEncounterMusicParam`, per class (`src/field_bgm.c`) |
| gym leader / Elite Four battle transitions (`GetTrainerBattleTransition`) | `sTrainerBattleIntroParams` (`src/battle_intro_config.c`): transition and battle music ([battle-visuals.md](battle-visuals.md)) |
| `graphics/trainers/front_pics/<name>.png`, 64×64 | `graphics/trainers/front_pics/<pic>.png`, 80×80 frames ([Trainer sprites](#trainer-sprites)) |
| `graphics/trainers/palettes/<name>.pal` | the same |
| `gTrainerFrontAnimsPtrTable` (one still frame for everyone) | `"anims"` in `data/trainer_graphics/front_pics.json`; 31 classes really move (gym leaders, Elite Four, Red, ...) |
| `graphics/trainers/back_pics/*.png` (64×256, 4 frames) + `gTrainerBackAnimsPtrTable` | `graphics/trainers/back_pics/<pic>.png` (8 or 5 frames) + `back_pics.json`, picked by `TrainerClassToBackpicID` (`src/pokemon.c`) |
| `gTrainerBallTable` (ball per class) | none: always a Poké Ball ([battle-visuals.md](battle-visuals.md#5-which-ball-a-trainers-pokémon-come-out-of)) |
| `gFacilityClassToPicIndex` / `gFacilityClassToTrainerClass` | `src/frontier/frontier_trainers.c`, `src/union_room_avatar.c` |

## What a class is made of

For class number `N`:

| What | Where | Needed for a new class? |
|---|---|---|
| constant | `include/constants/trainer_class.h` | yes |
| name | entry `N` of `msg_0730.json`; `msg_0731.json` adds the article ("a Youngster") | yes, both |
| front sprite | a PNG, a `.pal` and an entry in `front_pics.json` ([below](#trainer-sprites)) | yes |
| gender | entry `N` of `sTrainerGenders` | yes: the array is read by index, a missing entry reads past the end |
| prize money | a row in `sPrizeMoneyTbl` | yes: a class not in the table asserts, then pays the Youngster's rate |
| eyes-meet music | a row in `sTrainerEncounterMusicParam` | no: defaults to `SEQ_GS_EYE_J_SHOUNEN` |
| battle transition and music | a row in `sTrainerBattleIntroParams` | no: defaults to the normal trainer battle |
| back sprite | `TrainerClassToBackpicID`, `back_pics.json` | no: only for classes that fight on *your* side; defaults to Ethan's or Lyra's by gender |
| gym leader cut-in (mugshot) | `src/field/encounter_effect_leaders.c` (its own graphics; [battle-visuals.md](battle-visuals.md#43-a-new-mugshot)) | no |

Gender is `TRAINER_MALE`, `TRAINER_FEMALE` or `TRAINER_DOUBLE`. It decides the
default back sprite and nudges the gender of the trainer's Pokémon (in
`TrMon_OverridePidGender`).

Prize money is `level of the last Pokémon × 4 × the table value` (× 2 again in a
double battle). Retail values go from 0 (the player classes) through 4 (Youngster),
8 (Hiker), 30 (gym leaders, Elite Four), 40 (Blue) and 45 (Rocket Boss) to 50
(Champion).

## Adding a class

The 129 retail classes are numbered 0-128. A new class takes the next free number;
the numbers have to stay contiguous because the sprite archive is indexed by
`class × 5` (the build checks this). The class is stored as a `u8`, and 200-207 are already taken by the
phone contacts, so there is room for 71 more (129-199).

1. **Constant.** After `TRAINERCLASS_PKMN_TRAINER_DAWN_PT` in
   `include/constants/trainer_class.h`:

   ```c
   #define TRAINERCLASS_PKMN_TRAINER_DAWN_PT   128
   #define TRAINERCLASS_SURFER                 129
   ```

2. **Name.** Add an entry at the end of `messages` in
   `files/msgdata/msg/msg_0730.json` and `msg_0731.json`, keeping the id pattern:

   ```json
   {"id": "msg_0730_00129", "en_US": "Surfer"}
   {"id": "msg_0731_00129", "en_US": "a Surfer"}
   ```

3. **Gender.** Add to `sTrainerGenders` in `src/trainer_data.c`. The retail table
   stops at Lucas Pt (127): Dawn Pt has no line, and class 128 reads the byte after the
   table. Add hers first, so the new line lands on 129:

   ```c
   TRAINER_FEMALE, // TRAINERCLASS_PKMN_TRAINER_DAWN_PT
   TRAINER_MALE,   // TRAINERCLASS_SURFER
   ```

4. **Prize money.** In `asm/overlay_12_battle_command.s`, add a row at the end of
   `sPrizeMoneyTbl`, and raise the table size in the `extern` in
   `src/battle/battle_command.c` (`sPrizeMoneyTbl[0x81][2]` becomes `[0x82][2]`):

   ```asm
   	.short TRAINERCLASS_SURFER, 8
   ```

5. **Sprite.** Add `graphics/trainers/front_pics/surfer.png`,
   `graphics/trainers/palettes/surfer.pal`, and an entry at the end of
   `data/trainer_graphics/front_pics.json` ([Trainer sprites](#trainer-sprites)):

   ```json
   "TRAINERCLASS_SURFER": {
     "pic": "surfer",
     "anims": [
       [[0, 4], "loop"]
     ]
   }
   ```

6. **Music** (optional). A row in `sTrainerEncounterMusicParam` in
   `src/field_bgm.c`: class, music in Johto, music in Kanto. For a special battle
   transition or battle theme, a row in `sTrainerBattleIntroParams` in
   `src/battle_intro_config.c` (the array size, `[32]`, goes up by one); see
   [battle-music.md](battle-music.md#41-a-trainer-class).

7. **Use it.** Set `"class": "TRAINERCLASS_SURFER"` on trainers in
   `files/poketool/trainer/trainers.json`. The overworld NPC that starts the battle
   has its own sprite (`SPRITE_*` in the map's `object_events`); that is unrelated
   to the class.

Build with `make release`. The `make` checksum tests fail after any of this; that
is expected for a mod.

To **rename or retune** an existing class, only steps 2-4 and 6 apply, on its
existing entries.

## Trainer sprites

Sprites are PNG files, laid out like pokeemerald's, and the build turns them into the
archives the game reads (`files/a/0/5/8` front, `files/a/0/0/6` back):

| pokeemerald | here |
|---|---|
| `graphics/trainers/front_pics/<name>.png` (64×64) | `graphics/trainers/front_pics/<pic>.png`: every frame, 80×80 each, stacked top to bottom |
| `graphics/trainers/back_pics/<name>.png` (64×256, 4 frames) | `graphics/trainers/back_pics/<pic>.png`, the same way (8 or 5 frames) |
| `graphics/trainers/palettes/<name>.pal` | `graphics/trainers/palettes/<pic>.pal` |
| `src/data/trainer_graphics/front_pic_tables.h`, `front_pic_anims.h` | `data/trainer_graphics/front_pics.json` |
| `src/data/trainer_graphics/back_pic_tables.h`, `back_pic_anims.h` | `data/trainer_graphics/back_pics.json` |

`front_pics.json` has one entry per class, in class order, keyed by the class
constant; `back_pics.json` one per `TRAINER_BACKPIC_*`. A still sprite needs two keys:

```json
"TRAINERCLASS_YOUNGSTER": {
  "pic": "youngster",
  "anims": [
    [[0, 4], "loop"]
  ],
  "flat_key": "0xF7C9"
}
```

- `pic` names the PNG, and the palette of the same name.
- `anims` is the animation ([below](#animation)).
- `flat_key` only keeps the retail build identical; new entries can leave it out.

Check your edits without building:

```sh
python3 tools/pokedata/trainer_pics.py check front data/trainer_graphics/front_pics.json --graphics graphics/trainers --include include
python3 tools/pokedata/trainer_pics.py check back data/trainer_graphics/back_pics.json --graphics graphics/trainers --include include
```

It names the entry and the problem: a PNG of the wrong size, a sequence showing a
frame that doesn't exist, entries out of order, a pixel outside the sprite. The
build runs the same checks.

### Drawing a sprite

- **Size:** 80 pixels wide, 80 × the number of frames tall. Frame 0 is the top 80
  rows, frame 1 the next 80, and so on, with no gaps.
- **Colors:** an indexed (paletted) PNG with 16 colors; color 0 is transparent. The
  colors the game uses come from the `.pal` file, not from the PNG, as in
  pokeemerald. Keep the two the same; most editors can save a JASC `.pal`
  (Aseprite, GraphicsGale, Usenti), or copy an existing one.
- **Position:** the sprite is drawn centered on its spot. Keep the trainer's feet at
  the height of the retail sprites (open one next to yours) or they will float or
  sink on the battle platform.
- **Corner:** the bottom-right 4 pixels of frame 1 must be transparent, because of
  how the [flat picture](#the-flat-picture) is encrypted (no rule for a one-frame
  sprite).

To **change** a sprite, edit its PNG (and `.pal`) and build. To **add** one, add the
PNG and `.pal`, then the entry at the end of the table, after adding the class
([Adding a class](#adding-a-class)).

**Coming from pokeemerald:** a Gen 3 front pic (64×64, 16 colors, JASC `.pal`)
works as-is on an 80×80 canvas. Put it bottom-center (x 8-71, y 16-79) and keep its
`.pal`. GBA sprites are smaller than DS ones, so they look small next to retail
trainers; to fix that, redraw them larger rather than resizing.

### The flat picture

Each sprite also has a 160×80 picture of two frames side by side, which the Hall of
Fame, the Pal Pad and the Wi-Fi Plaza show; for back sprites it is also shown while
the player slides in before a wild battle. **The build makes it from frames 0 and
1** (frame 0 and an empty half for a one-frame sprite). `"flat": [0, 3]` picks other
frames.

Five retail sprites have a flat picture that isn't a copy of their frames (a few
pixels touched up, or drawn differently for Castle Valet). They keep it as its own
PNG, `front_pics/<pic>_flat.png`, named with `"flat": "<pic>_flat"`.

### Back sprites

Back sprites only matter for trainers on *your* side: the player, and partners such
as Silver, Lance, Cheryl or Riley. `TrainerClassToBackpicID` in
`src/pokemon.c` picks one; every class not listed there gets Ethan's or Lyra's by
gender. A new back sprite needs a `TRAINER_BACKPIC_*` constant (next number), an
entry at the end of `back_pics.json`, a case in that function, and a row in
`gBallThrowOffsets` for where the ball appears. A worked example, a third player
character: [player-characters.md §6](player-characters.md#6-battle-trainer-class-and-back-sprite).

## Animation

The `anims` list holds **sequences**, and how many there are decides what the battle
does (`Task_TrainerEncounter` in `src/battle/battle_controller_opponent.c`):

| Sequences | Behavior | Retail examples |
|---|---|---|
| 1 | still: sequence 0 is shown the whole time | almost every regular class |
| 2 | sequence 0 while sliding in; **sequence 1 plays once** when the trainer stops | Pryce, Brock, Misty, the Frontier Brains, Lance as a Pokémon Trainer |
| 3 | **sequence 2** is held while sliding in, then sequence 1 plays when the trainer stops | Falkner, Whitney, Silver, Red, Champion Lance |

For back sprites, sequence 1 is the ball throw.

A sequence is a list of frames, like pokeemerald's `ANIMCMD_FRAME(frame, duration)`:

| Frame | Meaning |
|---|---|
| `[2, 8]` | show frame 2 (of the PNG) for 8 ticks |
| `[2, 8, -1, 0]` | the same, moved 1 pixel left (x, y). In one sequence, give x and y on every frame or on none |
| `[2, 8, "flash"]`, `[2, 8, -1, 0, "flash"]` | the screen flashes when this frame shows (gym leaders, Elite Four) |
| `[2, 8, "play 0"]` | switch to sequence 0 |
| `[2, 8, "end"]` | end the intro animation here |
| `"loop"` (last item) | start the sequence over, like `ANIMCMD_JUMP(0)`; without it the last frame stays |

Falkner, for example (frames 0-2 of `leader_falkner.png`):

```json
"anims": [
  [[1, 4]],
  [[1, 30, 0, 0], [0, 3, 0, 0], [0, 3, 1, 0], [0, 4, 2, 0], [1, 4, 0, 0], [1, 8, -2, 0], [1, 16, -3, 0], [2, 8, -1, 0, "flash"], [2, 8, -2, 0], [2, 24, -3, 0]],
  [[1, 4]]
]
```

He rests on frame 1 and slides in on frame 1 (sequences 0 and 2). When he stops, he
holds it for 30 ticks, steps through frames 0, 1 and 2 with small shifts, and the
screen flashes as frame 2 starts. The retail animations follow that pattern: a still
opening, a short move, then a held last frame.

To make a still class move, draw more frames under the first in its PNG and add
sequences. A typical two-frame wave:

```json
"anims": [
  [[0, 4], "loop"],
  [[0, 10], [1, 12], [0, 20]]
]
```

### Retail details (layouts and the other keys)

These keys exist so retail sprites rebuild unchanged; new sprites don't need them.

| Key | What it does | Used by |
|---|---|---|
| `"palette": "name"` | palette file, if not named like `pic` | back sprite `rival` (`rival_back.pal`) |
| `"frames": {"3": {"offset": [16, 0]}}` | shows frame 3 moved by (x, y) wherever it appears | most back sprites, some gym leaders |
| `"frames": {"3": {"flip": true}}` | shows frame 3 mirrored; the PNG holds it as shown | Erika, Arcade Star |
| `"layout": "name"`, or per frame | another arrangement of hardware sprites (below) | Poké Fan, Castle Valet, Frontier Brains |
| `"empty_cell": true` | one more, empty frame after the last | Koga, Tower Tycoon, Arcade Star |
| `"labels": [...]` | the archive's sequence names, if not `CellAnime0`, `1`... | five classes |
| `"flat"`, `"flat_key"` | [the flat picture](#the-flat-picture) and its encryption seed | |

The DS draws a frame as several hardware sprites. The standard **layout**,
`80x80`, covers the frame with six: 64×64, two 16×32, two 32×16 and a 16×16.
`layouts` at the top of `front_pics.json` defines the others, each sprite as
`[x, y, width, height]` from the frame's center, with optional extras:

- `[x, y, w, h, palette]` draws that sprite with another palette. Its pixels are
  stored in the PNG as `16 × palette + color`, so the PNG is 8-bit.
- `[x, y, w, h, palette, drawX, drawY]` draws the sprite somewhere other than where
  its pixels are in the PNG.

The Poké Fan is only 72 wide (`pokefan`). Castle Valet is two people, the second
drawn with palette 1. The two overlap, so the second one's pixels sit 8 pixels
further right in the PNG than where they are drawn, so no pixel is hidden.

## How the build works

`tools/pokedata/trainer_pics.py build` reads a table, its PNGs and palettes, and
writes five files per entry into the archive, at `5N` to `5N+4`
(`GetTrainerPicFileIds` in `src/pokemon.c`):

| # | File | Made from |
|---|---|---|
| 0 | NCGR | the PNG's frames, cut into the layout's hardware sprites (4bpp tiles) |
| 1 | NCLR | the `.pal` |
| 2 | NCER | one cell per frame: the layout, offset, mirroring |
| 3 | NANR | `anims` |
| 4 | NCGR | the flat picture, encrypted |

The retail archives are no longer in the repository; the build makes them from these
sources, and with the sources unchanged they are byte for byte the retail ones
(`make` passes its checksum tests for both versions). Run the tests with
`python3 tools/pokedata/test_trainer_pics.py` after a build.

`trainer_pics.py extract` made the sources from the retail archives (one-time; it
is kept to redo that).

## Not editable yet

- The gym leader and Elite Four cut-ins (`encounter_effect_leaders.c`) use their own
  graphics, in another archive.
