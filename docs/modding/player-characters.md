<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-27 -->

# Player characters

> AI-generated; not affiliated with pret. See AI.md at the repository root.

HGSS has two player characters, Ethan and Lyra, and the game stores the choice as the
player's **gender**. This guide shows how to add a third character, using Kris as the
example. The character needs overworld sprites (walking, bike, surf, fishing...), a
battle back sprite, a trainer class, trainer card art and intro art. The game keeps
treating the player as a boy or a girl everywhere else.

| pokeemerald | here |
|---|---|
| `gSaveBlock2Ptr->playerGender` (`MALE` / `FEMALE`) | `PlayerProfile.gender` (`PLAYER_GENDER_MALE` / `FEMALE`, `include/player_data.h`) |
| `sPlayerAvatarGfxIds[state][gender]` and `GetPlayerAvatarGraphicsIdByStateIdAndGender` | `PlayerAvatar_GetSpriteByStateAndGender` (`src/player_avatar.c:519`), a `switch` per gender |
| `OBJ_EVENT_GFX_BRENDAN_NORMAL` ... in `object_event_graphics_info_pointers.h` | `SPRITE_HERO` ... rows in `gObjectEventGraphicsInfos` (`asm/overlay_01_sprite_data.s`) |
| `TRAINER_BACK_PIC_BRENDAN`, `gTrainerBackPicTable` | `TRAINER_BACKPIC_ETHAN`, `data/trainer_graphics/back_pics.json` + `graphics/trainers/back_pics/` |
| `sTrainerBackPicAnimations`, ball throw position | the `anims` in `back_pics.json`, and `gBallThrowOffsets` (`asm/battle_controller_opponent_data.s`) |
| trainer card `sKantoTrainerCardPicTiles`... per gender | members 54 / 55 of `files/a/0/4/9`, binary |
| Birch's intro: `sBirchSpeech_*` gender menu, Brendan/May pictures | Oak's speech (`src/oaks_speech.c`), pictures in `files/demo/intro/intro/`, binary |

The changes below were built together with `make release` (2026-10-27) and then
reverted, so this repository still matches retail. "Built" means it compiled, not that
it was played; see [Not verified](#not-verified).

## 1. Why gender can't hold a third value

`gender` is a `u8`, so it could hold a 2, but 107 calls in 73 files read it, and they
assume 0 or 1:

| What reads it | What a 2 does |
|---|---|
| **OT gender of every Pokémon**: `otGender` is a 1-bit field (`include/pokemon_types_def.h:139`) | a Pokémon you catch is saved with OT gender 0, and `BoxmonBelongsToPlayer` (`src/pokemon.c:4118`) and the battle checks (`src/battle/battle_util.c:5256`, `5269`) then see a mismatch. **All your Pokémon count as traded**: they disobey above the badge level cap and get boosted EXP |
| the player's battle trainer class: `trainerClass = gender` (`src/battle/battle_setup.c:569`) | class 2, `TRAINERCLASS_YOUNGSTER`. Its back sprite falls back to Ethan's |
| the Union Room appearance, `sPlayerAvatarAttributes[16][3]` indexed `[i + gender * 8]` (`src/union_room_avatar.c:28`) | read past the end of the table already at New Game (`src/overlay_36.c:202`) |
| the default name, `NamingScreen_SetDefaultName` (`src/naming_screen.c:656`) | an uninitialized string pointer (the code's own comment says so) |
| the tutorial battle: the friend's name is `msg_0445[gender ^ 1]` (`battle_setup.c:117`) | message 3 of a 2-message bank |
| the bag's camera keys `gCameraTweenKeys[2][9]` (`src/application/bag/bag_app.c:3001`), phone messages `msgIDs[2]` (`src/application/pokegear/phone/phone_call.c:228`), the field-move cut-in tables (§5) | read past the end, or show Lance |
| the trainer card, the Frontier card, the photo album: 1-bit `gender` fields | truncated to 0 |
| everything sent over a link: the 0x20-byte profile, the trainer card, Pal Pad entries | other games read your 2. In the Pal Pad, gender 2 means "registered but never met" (`src/application/palpad/palpad.c:273`) |

The rest are `gender == MALE ? ... : ...` branches, and they don't agree on which side
a 2 falls: a third value shows Ethan's art in some places and Lyra's in others.

So **gender stays 0 or 1**. The look gets a field of its own, the **character**.
Everything that is about the player's gender (OT, text, the friend, link play) keeps
reading the gender. What is about the player's look reads the character.

## 2. The character id

Ethan and Lyra get the same numbers as their genders. A link partner's gender (0 or 1)
is then also a valid character id, so code that draws other players keeps working
unchanged.

In `include/constants/global_fieldmap.h`, after the `PLAYER_STATE_*` block. This header
is included both by C and by scripts:

```c
// Who the player looks like. Ethan and Lyra have the same numbers as their genders.
#define PLAYER_CHARACTER_ETHAN 0
#define PLAYER_CHARACTER_LYRA  1
#define PLAYER_CHARACTER_KRIS  2
#define NUM_PLAYER_CHARACTERS  3
```

**Where to save it.** `PlayerProfile` has a byte that nothing reads or writes,
`dummy` (offset 0x1E, `include/player_data.h:23`). Rename it:

```c
    u8 character; // PLAYER_CHARACTER_* + 1, 0 = the one for the gender (PlayerProfile_GetCharacter)
```

and add a getter and setter at the end of `src/player_data.c` (declare them in
`player_data.h`):

```c
void PlayerProfile_SetCharacter(PlayerProfile *profile, u32 character) {
    profile->character = character + 1;
}

// Stored + 1: saves made before there was a character have 0, and get Ethan or Lyra by gender.
u32 PlayerProfile_GetCharacter(PlayerProfile *profile) {
    if (profile->character == 0) {
        return profile->gender;
    }
    return profile->character - 1;
}
```

Storing it plus one means **old saves keep working**: their byte is 0, so they get
the character matching their gender. It also keeps working in temporary profiles
that start zeroed: the tutorial battle's copy, NPC trade partners, link partners
(they send 0 here, being retail or older saves).

The profile is the right place, rather than a free variable: the battle setup, the bag,
the trainer card and most screens get a `PlayerProfile` but not the variables. The byte
travels over link inside the profile. Retail games ignore it as far as this code shows.

**The character's gender** is the player's gender, chosen as usual. A male player can
look like Kris; the game still calls him a boy. To tie them together, set both in
Oak's speech (§3).

## 3. Choosing the character

### From a script

Two commands, appended to the command table
([script-commands.md §6](script-commands.md#6-adding-a-command)). In `src/scrcmd_c.c`,
after `ScrCmd_GetPlayerGender`:

```c
BOOL ScrCmd_GetPlayerCharacter(ScriptContext *ctx) {
    PlayerProfile *profile = Save_PlayerData_GetProfile(FieldSystem_GetSaveData(ctx->fieldSystem));
    u16 *p_ret = ScriptGetVarPointer(ctx);
    *p_ret = PlayerProfile_GetCharacter(profile);
    return FALSE;
}

// The gender stays. The sprite changes at the next setavatarbits + updateavatarstate, or warp.
BOOL ScrCmd_SetPlayerCharacter(ScriptContext *ctx) {
    PlayerProfile *profile = Save_PlayerData_GetProfile(FieldSystem_GetSaveData(ctx->fieldSystem));
    u16 character = ScriptGetVar(ctx);
    GF_ASSERT(character < NUM_PLAYER_CHARACTERS);
    PlayerProfile_SetCharacter(profile, character);
    PlayerAvatar_SetCharacter(ctx->fieldSystem->playerAvatar, character);
    return FALSE;
}
```

Declare both in `include/scrcmd.h`, append `ScrCmd_GetPlayerCharacter,` and
`ScrCmd_SetPlayerCharacter,` to `gScriptCmdTable` (they become 853 and 854), and add the
macros to `asm/macros/script.inc`:

```
	// Sets VAR to who the player looks like (PLAYER_CHARACTER_*)
	.macro GetPlayerCharacter var
	.short 853
	.short \var
	.endm

	// Changes who the player looks like (PLAYER_CHARACTER_*); then setavatarbits(PLAYER_TRANSITION_WALKING) and updateavatarstate
	.macro SetPlayerCharacter character
	.short 854
	.short \character
	.endm
```

`PlayerAvatar_SetCharacter` is from §4. A wardrobe in the player's room that cycles
through the characters (this replaced the Wii sign in `NewBark_PlayerHouse_2F` for the
test build):

```
script NewBark_PlayerHouse_2F_EventScript_ItsAWiiSign {
    lockall
    getplayercharacter(VAR_SPECIAL_RESULT)
    addvar(VAR_SPECIAL_RESULT, 1)
    if (var(VAR_SPECIAL_RESULT) >= NUM_PLAYER_CHARACTERS) {
        setvar(VAR_SPECIAL_RESULT, PLAYER_CHARACTER_ETHAN)
    }
    setplayercharacter(VAR_SPECIAL_RESULT)
    setavatarbits(PLAYER_TRANSITION_WALKING)
    updateavatarstate
    releaseall
    end
}
```

`setavatarbits` + `updateavatarstate` are how retail scripts change the player's sprite
(the Rocket disguise in `Goldenrod_Tunnel_B1F`); they redraw it from the table in §4.

This is the cheap way to offer a third character: Oak's speech still asks boy or girl,
and the look is picked in the game. It needs none of the intro art.

### In Oak's speech

`OakSpeech_Exit` saves the gender (`src/oaks_speech.c:644`). Set the character next to
it, from the gender if nothing else picks it:

```c
    PlayerProfile_SetTrainerGender(profile, namingScreenArgs_Player->playerGenderOrMonSpecies);
    PlayerProfile_SetCharacter(profile, character);
```

A third picture on the selection screen is a bigger job. The screen is built for exactly
two choices ([intro-title-credits.md §4](intro-title-credits.md#4-professor-oaks-speech)
has the states):

| What | Where | For a third choice |
|---|---|---|
| number of choices | `numOptions = 2` (line 1893) | 3 |
| the picture of both kids | bottom screen: tiles member 32, tilemap 51, palettes 30 (HG) / 31 (SS) of `files/demo/intro/intro/`; boy on tiles x 0-15, girl on 16-31 | redraw in thirds. The files are binary: [graphics.md §4](graphics.md#4-changing-a-binary-archive) |
| touch areas | `sTouchscreenHitboxes_GenderSelect[3]` (line 270), `{top, bottom, left, right}` | three columns, the end marker moved to index 3 |
| the blinking frame | `sButtonBlinkPalOffsets[] = {12, 14}` (line 213), `OakSpeech_BlinkHighlightedGenderFrame` asserts `cursorPos` is 0 or 1 and uses `!cursorPos` for the other frame | a third color pair; loop over the other choices |
| indicator sprites | `OakSpeech_SelectedGenderIndicatorSpritesAction` (`src/oaks_speech_obj.c:164`), cases `GENDER_CURSOR_MALE/FEMALE/BOTH/NEITHER` | a sprite and a case for the third |
| hiding the other kid | `FillBgTilemapRect(..., 16 * (cursorPos ^ 1), ...)` (line 1929, again at 2160) | blank every column but the chosen one |
| the yes/no buttons | drawn in the free half: menu id `playerGender + 1` into `sMultichoiceMenuHitboxes[3][4]` and `sMultichoiceMenuBgCursorCoords[3]`, scroll in `OakSpeech_LoadSubScreenMenuGraphics` (line 1238) | a layout for a middle choice: a new row in both tables and a scroll case |
| "So, you're a boy then?" | `msg_0219` 38 / 39 (line 1934) | a new message at the end of `msg_0219.json` |
| the top-screen picture and its shrink | `sBgPicNCGR_NCLR[10][2]` (line 496; Ethan 12-15 + palette 16, Lyra 17-20 + 21), `sPlayerPicShrinkGfx_Male/Female` (line 333; 12, 22-25 and 17, 26-29), the branch at line 2112 and in `OakSpeech_PlayerPicShrinkAnim` (line 1459) | new members appended to the archive, a new `OAK_SPEECH_PIC_*` row, a shrink table |

`playerGender` is also passed to the naming screen as `playerGenderOrMonSpecies`, so
keep it 0 or 1 and carry the character in a field of its own.

## 4. Overworld sprites

### Which sprites

The player's sprite depends on what they're doing, the **state**. Each state has its
own sprite (with its own texture) per character:

| State | Ethan / Lyra | Frames | What it is |
|---|---|---|---|
| `PLAYER_STATE_WALKING` | `SPRITE_HERO` / `HEROINE` | 32 | standing, walking (frames 1-16) and running (17-32) |
| `CYCLING` | `CYCLEHERO` / `CYCLEHEROINE` | 24 | the Bicycle |
| `SURFING` | `SWIMHERO` / `SWIMHEROINE` | 4 | sitting, one per direction. The Pokémon underneath is a field effect shared by both (`src/field/field_surf_mount.c`) |
| `USE_HM` | `SPHERO` / `SPHEROINE` | 4 | the pose for using an HM |
| `WATERING` | `WATERHERO` / `WATERHEROINE` | 7 | the Squirtbottle |
| `FISHING` | `FISHINGHERO` / `FISH_HEROINE` | 16 | casting and reeling |
| `POKETCH` | `POKEHERO` / `POKEHEROINE` | 12 | looking at the Pokégear |
| `SAVING` | `SAVEHERO` / `SAVEHEROINE` | 2 | saving |
| `HEAL` | `BANZAIHERO` / `BANZAIHEROINE` | 12 | arms up at the Pokémon Center |
| `LADDER` | `LADDERHERO` / `LADDERHEROINE` | 6 | climbing |
| `ROCKET` | `RHERO` / `RHEROINE` | 32 | the Team Rocket disguise |
| `ROCKET_HEAL` | `RBANZAIHERO` / `RBANZAIINE` | | the disguise, healing |
| `POKEATHLON` | `PKTHHERO` / `PKTHHEROINE` | 32 | the Pokéathlon outfit |
| `APRICORN_SHAKE` | `SHAKEHERO` / `SHAKEHEROINE` | 8 | shaking an Apricorn tree |
| `ROCKET_SAVING` | `SAVERHERO` / `SAVERHEROINE` | 2 | the disguise, saving |

The states are `PLAYER_STATE_*` in `include/constants/global_fieldmap.h`. Fly has no
state: it is the cut-in of §5.

Not in the table, so not changed by this recipe: `SPRITE_HERO_2` / `HEROINE_2` and
`PL_BOY01C` / `PL_GIRL01C`, used to draw link players from other game versions
(`PlayerAvatar_CreateWithParams`, `src/player_avatar.c:144`), and the statues
`STATUEHERO` / `STATUEHEROINE` in the Pokéathlon Dome.

### Making the sprites

`mapkit sprite add` copies a sprite with its texture layout and drawing settings
([overworld-sprites.md](overworld-sprites.md#adding-a-new-sprite)). Copy each of Lyra's
(or Ethan's):

```sh
M=tools/mapkit/mapkit.sh
for pair in KRIS:HEROINE CYCLEKRIS:CYCLEHEROINE SWIMKRIS:SWIMHEROINE SPKRIS:SPHEROINE \
            WATERKRIS:WATERHEROINE FISHINGKRIS:FISH_HEROINE POKEKRIS:POKEHEROINE \
            SAVEKRIS:SAVEHEROINE BANZAIKRIS:BANZAIHEROINE LADDERKRIS:LADDERHEROINE \
            RKRIS:RHEROINE RBANZAIKRIS:RBANZAIINE PKTHKRIS:PKTHHEROINE \
            SHAKEKRIS:SHAKEHEROINE SAVERKRIS:SAVERHEROINE; do
    $M sprite add ${pair%%:*} --like SPRITE_${pair##*:}
done
```

That makes `SPRITE_KRIS` (1050) ... `SPRITE_SAVERKRIS` (1064), textures
`mmodel_00000863`-`877`, and their rows in `gObjectEventGraphicsInfos`. They are copies
of Lyra so far. To draw them, export each sheet, paint it, and import it back:

```sh
$M sprite export SPRITE_KRIS kris.png      # 1024×32: 32 frames of 32×32
$M sprite import kris.png SPRITE_KRIS
```

Frames 1-16 of the walking sheet are 4 per direction (up, down, left, right), as for
an NPC; frames 17-32 are the same for running (`sFacingBillboardWalkSequences`,
`src/field/map_object_render.c:251`). Keep the frame count and the palette size; the
import keeps everything else.

### The table

Replace the two `switch` statements of `PlayerAvatar_GetSpriteByStateAndGender`
(`src/player_avatar.c:519`) with a table, and rename it to say what it takes now:

```c
// One row per PLAYER_CHARACTER_*, one column per PLAYER_STATE_*.
static const u16 sPlayerSprites[NUM_PLAYER_CHARACTERS][PLAYER_STATE_ROCKET_SAVING + 1] = {
    [PLAYER_CHARACTER_ETHAN] = {
        [PLAYER_STATE_WALKING]        = SPRITE_HERO,
        [PLAYER_STATE_CYCLING]        = SPRITE_CYCLEHERO,
        // ... one line per state, as in the switch
    },
    [PLAYER_CHARACTER_LYRA] = {
        [PLAYER_STATE_WALKING]        = SPRITE_HEROINE,
        // ...
    },
    [PLAYER_CHARACTER_KRIS] = {
        [PLAYER_STATE_WALKING]        = SPRITE_KRIS,
        [PLAYER_STATE_CYCLING]        = SPRITE_CYCLEKRIS,
        [PLAYER_STATE_SURFING]        = SPRITE_SWIMKRIS,
        [PLAYER_STATE_ROCKET]         = SPRITE_RKRIS,
        [PLAYER_STATE_USE_HM]         = SPRITE_SPKRIS,
        [PLAYER_STATE_WATERING]       = SPRITE_WATERKRIS,
        [PLAYER_STATE_POKEATHLON]     = SPRITE_PKTHKRIS,
        [PLAYER_STATE_FISHING]        = SPRITE_FISHINGKRIS,
        [PLAYER_STATE_POKETCH]        = SPRITE_POKEKRIS,
        [PLAYER_STATE_SAVING]         = SPRITE_SAVEKRIS,
        [PLAYER_STATE_HEAL]           = SPRITE_BANZAIKRIS,
        [PLAYER_STATE_LADDER]         = SPRITE_LADDERKRIS,
        [PLAYER_STATE_ROCKET_HEAL]    = SPRITE_RBANZAIKRIS,
        [PLAYER_STATE_APRICORN_SHAKE] = SPRITE_SHAKEKRIS,
        [PLAYER_STATE_ROCKET_SAVING]  = SPRITE_SAVERKRIS,
    },
};

// Link players pass their gender, which is also Ethan's or Lyra's character id.
u32 PlayerAvatar_GetSpriteByStateAndCharacter(s32 state, u32 character) {
    if (character >= NUM_PLAYER_CHARACTERS || state < 0 || state > PLAYER_STATE_ROCKET_SAVING) {
        GF_ASSERT(FALSE);
        return SPRITE_HERO;
    }
    return sPlayerSprites[character][state];
}
```

### Giving the avatar its character

The avatar (`struct PlayerAvatar`, `include/player_avatar.h:26`) only knows a gender.
Add a field at the end (it is allocated with `sizeof`):

```c
    u32 character; // PLAYER_CHARACTER_*; gender is the one whose cut-in and Fly graphics it uses
}; // size: 0x44
```

and replace `PlayerAvatar_SetGender` in `src/player_avatar.c` with a public setter
(declare it and `PlayerAvatar_GetCharacter` in the header):

```c
void PlayerAvatar_SetCharacter(PlayerAvatar *avatar, u32 character) {
    avatar->character = character;
    avatar->gender = character == PLAYER_CHARACTER_ETHAN ? PLAYER_GENDER_MALE : PLAYER_GENDER_FEMALE;
}

u32 PlayerAvatar_GetCharacter(PlayerAvatar *avatar) {
    return avatar->character;
}
```

The avatar's `gender` is only read for the field-move cut-in and the Fly landing
(§5), so here it means "whose cut-in art to borrow": Kris uses Lyra's.

Then pass the character through:

- `PlayerAvatar_Setup`, `PlayerAvatar_CreateWithParams` and
  `PlayerAvatar_CreateWithActiveMapObject` (`src/player_avatar.c`): rename the `gender`
  parameter to `character`, call `PlayerAvatar_SetCharacter`, and call
  `PlayerAvatar_GetSpriteByStateAndCharacter`. The `PL_BOY01C` / `HERO_2` branches compare
  with `PLAYER_GENDER_MALE`; leave them, they only run for link players.
- `src/field_warp_tasks.c:276-313`, where the field creates the avatar: read
  `PlayerProfile_GetCharacter` instead of `PlayerProfile_GetTrainerGender` (three places).
- `src/field/player_avatar_actions.c`: 17 calls of the form
  `PlayerAvatar_GetSpriteByStateAndGender(PLAYER_STATE_X, PlayerAvatar_GetGender(avatar))`.
  One `sed` does them all:
  ```sh
  sed -i 's/PlayerAvatar_GetSpriteByStateAndGender(\(PLAYER_STATE_[A-Z_]*\), PlayerAvatar_GetGender(\([a-zA-Z>-]*\)))/PlayerAvatar_GetSpriteByStateAndCharacter(\1, PlayerAvatar_GetCharacter(\2))/' src/field/player_avatar_actions.c
  ```
- `TakePhoto_RestorePlayerSprite` (`src/field_take_photo.c:823`) puts the sprite back
  after a photo, from the profile gender. Use
  `PlayerAvatar_GetCharacter(playerAvatar)` instead.

`src/comm_player_sync.c:216` (other players in the Union Room) keeps passing the
partner's gender: a valid character id, Ethan or Lyra.

### Checks that name the sprites

A few places compare the player's sprite id with Ethan's and Lyra's. Kris's ids don't
match them:

| Where | What it does | Change |
|---|---|---|
| `Field_PlayerAvatar_TryEnterPoketchPose`, `TryLeavePoketchPose` (`src/field/player_avatar_actions.c:1264`, `1275`) | `sprite - SPRITE_POKEHERO > 1` and `case SPRITE_POKEHERO / POKEHEROINE`. **Without the fix Kris never leaves the Pokégear pose** | compare with `PlayerAvatar_GetSpriteByStateAndCharacter(PLAYER_STATE_POKETCH, PlayerAvatar_GetCharacter(playerAvatar))`: `!=` to enter, `==` to leave |
| `src/field/dowsing_mchn.c:836`, `src/field/touchscreen_menu.c:517` | the sprite is in `FISHINGHERO`..`FISH_HEROINE`: the touch screen shows the fishing action | `spriteId == PlayerAvatar_GetSpriteByStateAndCharacter(PLAYER_STATE_FISHING, PlayerAvatar_GetCharacter(...))` |
| `src/field/field_reflection.c:274`, `291` | reflections in water skip the fishing sprite, but only `SPRITE_FISHINGHERO` (Lyra's isn't skipped either) | optional |
| `MapObject_GetBillboard` (`src/field/map_object_billboard_motion.c:269`) | a `case` per player sprite | none: the default returns the same thing |
| `sPokeathlonNpcTrainerPics` (`src/pokeathlon/pokeathlon_course_pics.c:39`) | sprite → model for the Pokéathlon screens | only if Kris's sprite should show there |

## 5. Field-move cut-in and Fly

Using an HM out of battle shows a banner with the player and the Pokémon
(`FieldMoveCutIn_Start`, `src/field/field_move_cut_in.c:88`). The player's graphics are
picked by `trainerGraphics = gender` from tables in `asm/field_move_effects_data.s:233-247`:

| Table | 0 Ethan | 1 Lyra | 2 Lance |
|---|---|---|---|
| `gCutInTrainerCharFiles` | 17 | 20 | 23 |
| `gCutInTrainerCellFiles` | 18 | 21 | 24 |
| `gCutInTrainerAnimFiles` | 19 | 22 | 25 |
| `gCutInTrainerPlttFiles` (index `trainerGraphics - 1`) | shared palette 6 | 7 | 8 |

These are members of `application/choose_starter/choose_starter_sub_res`, binary.
Index 2 is Lance's (`FieldMoveCutIn_StartFlyWithObject` sets it for his Dragonite).
This is why the avatar's `gender` stays 0 or 1 in §4: a character id of 2 here would
show Lance.

**Kris's own cut-in:** append her char, cell and animation as new members of that
archive ([graphics.md §4](graphics.md#4-changing-a-binary-archive)), add a fourth entry
to the char, cell and anim tables and a third to the palette table, and set
`trainerGraphics` from the character for index 3:

```c
    cutIn->trainerGraphics = character == PLAYER_CHARACTER_KRIS ? 3 : gender;
```

The callers pass `PlayerAvatar_GetGender`: `src/field/player_avatar_actions.c:1352`,
`src/field/field_move_warp_tasks.c:355`, `src/field/field_move_sweet_scent.c:97`,
`src/field_warp_state.c:223`, `225` (Fly take-off), `src/scrcmd_c.c:2314`. Give
`FieldMoveCutIn_Start` the avatar's character as well. Not built.

**Fly landing** has its own branch: `FlyLanding_LoadGraphics`
(`src/field/field_move_cut_in_effects.c:845`), `gender == 0` ? members 17/18/19 :
20/21/22 with palette 7. Kris lands as Lyra until it gets a third branch.

## 6. Battle: trainer class and back sprite

The player's trainer class is the gender (`BattleSetup_SetAllySideBattlersToPlayer`,
`src/battle/battle_setup.c:569`), and the class picks the back sprite
(`TrainerClassToBackpicID`, `src/pokemon.c:4135`). Kris gets a class of her own; this is
[adding a class](trainer-classes.md#adding-a-class) plus a back sprite.

1. **Constants**, in `include/constants/trainer_class.h`:
   ```c
   #define TRAINERCLASS_PKMN_TRAINER_KRIS      129
   ...
   #define TRAINER_BACKPIC_KRIS     17
   ```
2. **Name**: entries 129 in `files/msgdata/msg/msg_0730.json` and `msg_0731.json`,
   copied from 128 ("₧₦ Trainer", "a ₧₦ Trainer").
3. **Gender**: in `sTrainerGenders` (`src/trainer_data.c:136`), add **two** lines. The
   table stops at Lucas Pt (127), so Dawn Pt needs its line before Kris's goes in:
   ```c
       TRAINER_MALE,   // TRAINERCLASS_PKMN_TRAINER_LUCAS_PT
       TRAINER_FEMALE, // TRAINERCLASS_PKMN_TRAINER_DAWN_PT
       TRAINER_FEMALE, // TRAINERCLASS_PKMN_TRAINER_KRIS
   };
   ```
4. **Prize money** (none, like the other player classes): `.short TRAINERCLASS_PKMN_TRAINER_KRIS, 0`
   at the end of `sPrizeMoneyTbl` in `asm/overlay_12_battle_command.s`, and
   `sPrizeMoneyTbl[0x82][2]` in `src/battle/battle_command.c`.
5. **Front picture** (the Hall of Fame, other games in link battles): copy
   `graphics/trainers/front_pics/pkmn_trainer_lyra.png` and its palette to
   `pkmn_trainer_kris.png` / `.pal` and redraw it, and add at the end of
   `data/trainer_graphics/front_pics.json`:
   ```json
   "TRAINERCLASS_PKMN_TRAINER_KRIS": {
     "pic": "pkmn_trainer_kris",
     "anims": [
       [[0, 4], "loop"]
     ]
   }
   ```
6. **Back picture**: `graphics/trainers/back_pics/kris.png` (80×640, 8 frames of 80×80,
   copy `lyra.png`) and `graphics/trainers/palettes/kris.pal`, and at the end of
   `data/trainer_graphics/back_pics.json` Lyra's entry under a new key. Sequence 1 is
   the throw; the frame offsets are how far each throwing frame is shifted
   ([trainer-classes.md](trainer-classes.md#trainer-sprites)):
   ```json
   "TRAINER_BACKPIC_KRIS": {
     "pic": "kris",
     "frames": {
       "3": {"offset": [16, 0]},
       "4": {"offset": [10, 0]},
       "5": {"offset": [11, 1]},
       "6": {"offset": [12, 2]},
       "7": {"offset": [12, 3]}
     },
     "anims": [
       [[0, 4], "loop"],
       [[0, 8], [1, 16], [2, 6], [3, 2], [4, 4], [5, 2], [6, 2], [7, 52], [0, 2]]
     ]
   }
   ```
7. **Where the ball leaves the hand**: `gBallThrowOffsets`
   (`asm/battle_controller_opponent_data.s:43`) has one row per back sprite: (x, y) for
   six throw frames, `0x7FFF` for "no ball yet". It has rows for 0-14 only, because
   `ETHAN_2` and `LYRA_2` (15, 16) never reach it. Add three rows at its end so that
   row 17 exists:
   ```
   	.short 0, 128, -34, 4, -28, -11, 50, -12, 0x7FFF, 0x7FFF, 0x7FFF, 0x7FFF // TRAINER_BACKPIC_ETHAN_2 (never read)
   	.short 0, 128, -34, 4, -28, -11, 50, -12, 50, -12, 0x7FFF, 0x7FFF // TRAINER_BACKPIC_LYRA_2 (never read)
   	.short 0, 128, -34, 4, -28, -11, 50, -12, 50, -12, 0x7FFF, 0x7FFF // TRAINER_BACKPIC_KRIS
   ```
   These are copies of Lyra's row; a back sprite drawn differently needs its own.
8. **The back sprite for the class**, in `TrainerClassToBackpicID`:
   ```c
       case TRAINERCLASS_PKMN_TRAINER_KRIS:
           return TRAINER_BACKPIC_KRIS;
   ```
   Ethan and Lyra also have `_2` back sprites, used when a battle has a follower
   (`isLink`, `src/battle/battle_controller_opponent.c:2154`). Kris has one for both.
9. **The player's class from the character**, in `src/battle/battle_setup.c`:
   ```c
   static const u8 sPlayerCharacterTrainerClasses[NUM_PLAYER_CHARACTERS] = {
       [PLAYER_CHARACTER_ETHAN] = TRAINERCLASS_PKMN_TRAINER_ETHAN,
       [PLAYER_CHARACTER_LYRA]  = TRAINERCLASS_PKMN_TRAINER_LYRA,
       [PLAYER_CHARACTER_KRIS]  = TRAINERCLASS_PKMN_TRAINER_KRIS,
   };

   void BattleSetup_SetAllySideBattlersToPlayer(BattleSetup *setup) {
       setup->trainer[BATTLER_PLAYER].data.trainerClass = sPlayerCharacterTrainerClasses[PlayerProfile_GetCharacter(setup->profile[BATTLER_PLAYER])];
   ```
10. **Link battles keep the gender.** The class is sent to the other game
    (`src/battle_link_comm.c:238`), and a retail game has no class 129. In
    `BattleSetup_InitForLinkBattleWithParty`, replace the
    `BattleSetup_SetAllySideBattlersToPlayer(setup)` call in the `else` (line 389):
    ```c
        } else {
            // The class is sent to the other game, which only knows Ethan's and Lyra's.
            setup->trainer[BATTLER_PLAYER].data.trainerClass = PlayerProfile_GetTrainerGender(profile);
            CopyU16StringArray(setup->trainer[BATTLER_PLAYER].name, PlayerProfile_GetNamePtr(setup->profile[BATTLER_PLAYER]));
            setup->trainer[BATTLER_PLAYER2] = setup->trainer[BATTLER_PLAYER];
        }
    ```

The tutorial battle (the friend catching a Pokémon) makes a fresh profile with the
other gender, so its character byte is 0 and the friend is still Ethan or Lyra.

**The wild-battle slide-in** uses the back sprite's flat picture, built from frames 0
and 1 of `kris.png` ([trainer-classes.md](trainer-classes.md#the-flat-picture)).

## 7. Trainer card

The card's front picture is a background (`src/application/trainer_card/overlay_trainer_card_main.c:617`):
tiles from member 44 of `files/a/0/4/9` (both kids' tiles are in it), then screen
**54** if `card->gender == 0`, else **55**. The archive is binary and has 78 members.

1. Draw Kris into new members: append her tiles and her screen as `00078.NCGR` and
   `00079.NSCR` ([graphics.md §4](graphics.md#4-changing-a-binary-archive), and §9 there
   for tilemaps). The tiles of member 44 are a good start.
2. **The card needs the character.** `TrainerCardData.gender` is one bit
   (`include/trainer_card_data.h:15`), and the card is also exchanged over link. The two
   bytes `unk_36[2]` are padding: rename the first to `character` and set it in
   `TrainerCardData_Build` (`src/trainer_card_data.c:69`) with
   `card->character = PlayerProfile_GetCharacter(profile);`. A link partner's card
   arrives with 0 there, which is Ethan; read it only when `caseVariant == 255` (your
   own card, `src/start_menu.c:1110`), or store it plus one as in §2.
3. In the `caseVariant == 255` branch, load members 78/79 for Kris instead of 44 and
   54/55.

Not built. The card's color depends on its stars, not on the gender.

## 8. Everything else that shows the player

With the recipe above, these still decide by gender, so Kris (a girl) gets Lyra's
version, and a boy who picked Kris in a script gets Ethan's. Each needs new art and a
branch on `PlayerProfile_GetCharacter` to look like Kris:

| Screen | Where | Picks by gender |
|---|---|---|
| naming screen icon | `src/naming_screen.c:1161` | animation 48 / 49 of `files/data/namein/` |
| bag | `src/application/bag/bag_app.c:632`, `3103` | background screen 0x5E / 0x5D, the 3D bag model and animations (members 0x37... / 0x4A...) |
| Pokédex | `src/application/pokedex/pokedex_size_check.c:70`, `pokedex_screen_setup.c:1816`, `pokedex_forms.c:540` | the height comparison silhouette and the player marker |
| Pokégear map, Fly map | `src/application/pokegear/map/pokegear_map_gfx.c:840`, `fly_map_gfx.c:659` | the player icon's animation frame = gender |
| Hall of Fame | `src/register_hall_of_fame.c:2392` | the front picture of class Ethan / Lyra. Use `sPlayerCharacterTrainerClasses` from §6 |
| certificates (Pokédex diplomas) | `src/certificates_app.c:714` | `MMODEL_HERO` / `HEROINE` |
| credits | `src/credits/credits.c:955` | which of two sprites is the player and which the friend |
| Elite Four intro | `src/field/encounter_effect_leaders.c:594` | members 207-210 / 211-214 of `a/1/0/9` |
| Magnet Train | `src/magnet_train_cutscene.c:250` | models |
| Pokéathlon | `src/pokeathlon/pokeathlon_course_pics.c:353`, `pokeathlon_trophies.c:491` | course picture, trophy pose |
| Pokéwalker log | `src/application/pokewalker/pokewalker_event_log.c:916` | pose |
| Battle Frontier map | `Frontier_GetPlayerSpriteId` (`src/frontier/frontier_trainers.c:547`), `src/frontier/frontier_script_commands_ext.c:1419` | `SPRITE_HERO` / `HEROINE`: put Kris's sprite id here |
| Safari Zone objects | `GetSafariObjectConfig` (`src/safari_zone_encounters.c:69`) | statue and flag models (female only when `gender == TRAINER_FEMALE`) |
| VS Recorder, Frontier card | `src/application/vs_recorder/vs_recorder_screen.c:956` | char and palette |
| touch-screen Bag icon | `src/field/touchscreen_menu.c:826` | char 27 / 24 of `a/0/1/4` |

Name colors (blue for boys, red for girls) follow the gender, which is right for any
character.

## 9. Scripts, text and the friend

These are about gender, not looks, so they need nothing for a new character:

- `gendermsgbox(male, female)` (159 uses, e.g. the mom in `NewBark_PlayerHouse_1F`)
  and `getplayergender` pick text by gender.
- **The friend** (Lyra if you're a boy, Ethan if you're a girl) is the other gender:
  `getfriendsprite` (`src/scrcmd_c.c:4599`) gives `SPRITE_HERO` or `HEROINE` into
  `VAR_OBJ_0`, which the friend's `SPRITE_VAR_1` object reads, and `BufferFriendsName`
  (`src/message_format.c:110`) reads `msg_0445`. A girl who plays as Kris meets Ethan.
  To have Lyra as Kris's friend instead, branch on `getplayercharacter` in those nine
  maps (`NewBark`, `NewBark_ElmsLab_1F`, `NewBark_RivalHouse_2F`, `Route29`,
  `IlexForest`, `Goldenrod_Tunnel_1F`, `Route31_VioletGatehouse`, `Route34`,
  `Celadon_Condominiums_3F`) and in the 37 maps with `gendermsgbox`, since the text
  names the friend.
- Where a script shows the **player** as an object (the Battle Hall,
  `BattleFrontier_BattleHall/scripts.pory:89` and `107`, sets `VAR_OBJ_1` to 97 or 0,
  Lyra's or Ethan's sprite id), use Kris's id for her.

## 10. Link play

What other games see of a Kris player:

| Link | What the other game gets |
|---|---|
| Union Room, Wi-Fi Club, Plaza, GTS, Pal Pad | the gender and the Union Room avatar, as before: you appear as the avatar or as Lyra |
| link battle | class Ethan or Lyra (step 10 in §6), so Lyra's back sprite on your side |
| trainer card | gender bit, and the `character` byte, which retail cards leave at 0 |
| the profile (beacon, battle videos) | the `character` byte at 0x1E; retail ignores it |

Two copies of this mod, linked together, see each other as Ethan or Lyra too. Showing
Kris to each other would need the character added to what `comm_player_sync.c` sends.

## Not verified

- Everything in §2, §3 (script commands), §4 and §6 was built with `make release` for
  HeartGold on 2026-10-27, with the wardrobe test script, and then reverted. It was not
  run in an emulator, and SoulSilver was not built. Expected but not seen: Kris's
  sprites on the field in every state, the sprite changing from the script, the Pokégear
  pose ending, her back sprite and ball throw in battle.
- §5 (Kris's own cut-in), §7 (trainer card) and the three-way Oak's speech in §3: steps
  read from the code, not built.
- Whether retail games really ignore the `dummy` byte of a received profile.
- The flat picture made from Kris's back sprite during the wild-battle slide-in.
