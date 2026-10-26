<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Script commands and standard scripts

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers how script commands work, the ones a hack uses most, grouped by task,
and the standard scripts that play the role of pokeemerald's specials. The **complete
list** of all 853 commands, with arguments, uses and C functions, is generated:
[script-commands-list.md](script-commands-list.md). [SCRIPTING.md](SCRIPTING.md) covers
the `scripts.pory` language (`if`, `while`, text, movement) and
[npcs-and-scripts.md](npcs-and-scripts.md) covers attaching scripts to NPCs and triggers.

## 1. There are no specials

pokeemerald has a few hundred script commands, plus `special X` / `specialvar` to call one
of several hundred C functions by number. HGSS has neither `special` nor `specialvar`.
**Every feature is its own script command**, so the command table has 853 entries. The
mapping:

| pokeemerald | here |
|---|---|
| `special HealPlayerParty` | the command `healparty` |
| `specialvar VAR_RESULT, GetPlayerFacingDirection` | `getplayerfacing(VAR_SPECIAL_RESULT)`: the command writes the variable you name |
| `special ChoosePartyMon` + `waitstate` | `partyselectui`, then `getpartyselection(VAR)`. Commands that open a screen wait by themselves |
| `std` scripts (`STD_OBTAIN_ITEM`...) | `callstd(std_x)` (§5) |
| `VAR_0x8000`-`VAR_0x800B` | `VAR_SPECIAL_x8000`-`VAR_SPECIAL_x800B` (`include/constants/vars.h`) |
| `VAR_RESULT`, `VAR_LAST_TALKED` | `VAR_SPECIAL_RESULT` (0x800C), `VAR_SPECIAL_LAST_TALKED` (0x800D) |
| `VAR_TEMP_0`-`F` (cleared on map change) | `VAR_TEMP_x4000`... |

**Finding the command for something:**

```sh
python3 tools/scriptcmds/scriptcmds.py --find party    # number, name, arguments, how they're read, uses, C file:line
```

Or search [script-commands-list.md](script-commands-list.md), which groups them by task.
To see how the game uses one, grep the map scripts:
`grep -rn 'getpartymonspecies(' data/maps`.

## 2. How a command works

A command is a 16-bit number followed by its arguments, written by a macro in
[asm/macros/script.inc](../../asm/macros/script.inc):

```
    .macro GiveItem arg0, arg1, arg2
    .short 125          // the command number
    .short \arg0        // item
    .short \arg1        // quantity
    .short \arg2        // the variable that gets TRUE if it fit
    .endm
```

The number indexes `gScriptCmdTable`
([src/data/fieldmap/script_cmd_table.h](../../src/data/fieldmap/script_cmd_table.h)), which
points at the C function `ScrCmd_GiveItem` ([src/scrcmd_items.c](../../src/scrcmd_items.c)).
The function reads its arguments in order and returns:

- `FALSE`: done, run the next command at once;
- `TRUE`: stop for this frame. Commands that wait (for text, a fade, a screen to close)
  return `TRUE` after `SetupNativeScript(ctx, func)`, and the script continues when
  `func` returns `TRUE`.

In `scripts.pory`, write a command lowercased or as its macro name, with the arguments in
parentheses: `giveitem(ITEM_POTION, 1, VAR_SPECIAL_RESULT)`. Many macros still name their
arguments `arg0`, `arg1`. The C function says what they mean; the list links to it.

### Numbers or variables: how an argument is read

The **Read as** column of the list shows how the C function reads each argument. It
decides whether you may pass a variable:

| Read as | Read with | Pass |
|---|---|---|
| `val` | `ScriptGetVar` | a number **below 0x4000**, or a variable (`VAR_*`, `VAR_SPECIAL_*`), whose value is used |
| `var` | `ScriptGetVarPointer` | a variable. The command writes its result there, or reads it by name |
| `u8`, `u16`, `u32` | `ScriptReadByte` / `Halfword` / `Word` | a fixed number only |

Two traps follow from this:

- A `u8`/`u16` argument given a variable gets the variable's **id**, not its value.
  `playbgm(VAR_SPECIAL_x8004)` would play song 0x8004. Look for a `...Var` variant:
  `multichoiceadditemvar` takes variables where `multichoiceitemadd` takes bytes.
- A `val` argument treats anything at or above 0x4000 as a variable id. That's fine for
  species, items and moves, but a literal 16384 or more can't be passed. `u32` arguments
  (money amounts) don't have this limit.

## 3. Commands by task

The most used and most useful commands, checked against their C functions. `VAR` means
"a variable for the result". Every other command is in
[script-commands-list.md](script-commands-list.md).

### Flow, locking and waiting

| Command | Does |
|---|---|
| `lockall` / `releaseall` | freeze / unfreeze the player and every object (start and end of nearly every NPC script) |
| `lock(obj)` / `release(obj)` | the same for one object |
| `faceplayer` | turn the talked-to object toward the player |
| `end`, `return`, `goto(L)`, `call(L)` | finish, return from a `call`, jump, call. In `.pory`, write these as statements |
| `wait(frames, VAR)` | pause (the var is used as the counter) |
| `waitbutton`, `waitabpress` | wait for a button (alias `waitbuttonpress`) |
| `callstd(std_x)` | run a standard script and wait (§5) |
| `Switch(VAR)` / `Case(n, L)` | helper macros: copy `VAR` to `VAR_SPECIAL_x8008` and jump on its value. In `.pory`, `switch (var(V)) { case n: ... }` does it for you |

### Flags and variables

| Command | Does |
|---|---|
| `setflag(F)` / `clearflag(F)` | set / clear an event flag (a constant, `u16`) |
| `setvar(V, n)`, `addvar(V, x)`, `subvar(V, x)`, `copyvar(dst, src)` | variables. `addvar`/`subvar` take a number or a variable |
| `random(VAR, n)` | `VAR` = a random number from 0 to n-1 |
| `settrainerflag(T)` | mark a trainer as defeated, for `defeated(T)` |
| `getgameversion(VAR)` | `VERSION_HEARTGOLD` (7) or `VERSION_SOULSILVER` (8) |

In `.pory`, test flags and variables with `if (flag(F))` and `if (var(V) == n)`. The
compiler emits `checkflag`/`compare` and the jump ([SCRIPTING.md](SCRIPTING.md#conditions)).

### Text

| Command | Does |
|---|---|
| `npcmsg("text")` or `npcmsg(msg_id)` | the dialogue box (alias `message`). A string becomes a new message in the map's `text.json` |
| `closemsg` | close it (alias `closemessage`) |
| `holdmsg` | keep it open for what follows (a menu, a mart) |
| `nonnpcmsg(msg_id)` | a message from the map bank without the NPC behaviour |
| `msgboxextern(bank, msg)` | a message from another message bank |
| `gendermsgbox(male_msg, female_msg)` | pick a message by the player's gender (both are `u8` ids) |
| `SimpleNPCMsg(msg)` | helper: the click sound, `lockall`, `faceplayer`, the message, wait, close |
| `bufferplayersname(n)`, `bufferrivalsname(n)` | put a name into string slot n for `{STRVAR_1 ...}` in the text |
| `bufferitemname(n, item)`, `buffermovename(n, move)`, `bufferspeciesname(n, species, 0, 0)` | names |
| `bufferpartymonnick(n, slot)`, `buffermonspeciesname(n, slot)` | a party Pokémon's nickname / species |
| `bufferint(n, value)` | a number |

**Yes/no:** end the message with `{YESNO 0}`, then read the answer:

```
npcmsg("Should I explain how it works? {YESNO 0}")
touchscreenmenuhide
getmenuchoice(VAR_SPECIAL_RESULT)      // 0 = yes, 1 = no
touchscreenmenushow
if (var(VAR_SPECIAL_RESULT) == 0) { ... }
```

Multichoice and list menus: [ui.md](ui.md#menus-from-scripts).

### Objects and the player

| Command | Does |
|---|---|
| `applymovement(obj, Movement)`, `waitmovement` | run a movement script on an object (`obj_player` for the player), wait for all of them |
| `hideperson(obj)` / `showperson(obj)` | remove / add an object now (aliases `removeobject`, `addobject`). Its `flag` in `map.json` decides whether it is there next time |
| `moveperson(obj, x, z)` | change where an object appears when the map loads |
| `movepersonfacing(obj, x, y, z, dir)` | move it now, facing `dir` |
| `setobjectfacing(obj, dir)` | its default facing |
| `getplayercoords(VAR_X, VAR_Z)`, `getpersoncoords(obj, VAR_X, VAR_Z)` | positions |
| `getplayerfacing(VAR)` | the player's direction |
| `getplayerstate(VAR)` | walking, cycling, surfing (`PLAYER_STATE_*`) |
| `warp(MAP_X, 0, x, z, dir)` | warp the player |
| `followingpokemonmovement(m)`, `waitfollowingpokemonmovement`, `togglefollowingpokemonmovement(on)` | the walking Pokémon in cutscenes |

### Items and money

| Command | Does |
|---|---|
| `giveitem(item, n, VAR)` | add to the bag. `VAR` = TRUE if it fit. No message |
| `takeitem(item, n, VAR)` | remove from the bag |
| `hasitem(item, n, VAR)` | `VAR` = TRUE if the bag has at least n |
| `hasspaceforitem(item, n, VAR)` | `VAR` = TRUE if n more fit |
| `getitemquantity(item, VAR)`, `getitempocket(item, VAR)` | |
| `GiveItemNoCheck(item, n)` | helper: puts the item in `VAR_SPECIAL_x8004`/`x8005`, then `callstd(std_give_item_verbose)` ("X received the Y!" plus the fanfare and pocket message) |
| `addmoney(n)`, `submoneyimmediate(n)`, `hasenoughmoneyimmediate(VAR, n)` | money (`n` is a `u32` constant) |
| `showmoneybox(x, y)`, `updatemoneybox`, `hidemoneybox` | the money window |
| `getcoinamount(VAR)`, `givecoins(n)`, `takecoins(n)` | Game Corner coins. They are in `OVY_22`: load it first with `scriptoverlaycmd(3, 0)` (§6) |

The usual gift, as the retail scripts write it:

```
if (!itemspace(ITEM_CHARCOAL, 1)) {
    callstd(std_bag_is_full)
    closemsg
    releaseall
    end
}
GiveItemNoCheck(ITEM_CHARCOAL, 1)
```

Marts: [items.md](items.md#marts).

### Pokémon and party

| Command | Does |
|---|---|
| `givemon(species, level, item, form, ability, VAR)` | add a Pokémon to the party; `VAR` = TRUE if there was room |
| `giveegg(species, ?)` | add an Egg. The second argument is passed to `SetEggStats`; copy a retail use |
| `getpartycount(VAR)` | how many in the party |
| `getpartymonspecies(slot, VAR)` | its species (0 for an Egg) |
| `getpartyleadalive(VAR)` | the first slot with a healthy Pokémon |
| `monhasmove(VAR, move, slot)`, `getpartyslotwithmove(VAR, move)` | moves, for HM checks |
| `healparty` | heal everyone |
| `partyselectui`, `getpartyselection(VAR)` | let the player pick a Pokémon |
| `nicknameinput(slot, VAR)` | the nickname screen |
| `checkbadge(badge, VAR)`, `givebadge(badge)` | badges (`BADGE_*`) |

### Battles

| Command | Does |
|---|---|
| `trainerbattle(T, T2, 0, 0)`, `checkbattlewon(VAR)`, `whiteout` | a scripted trainer battle ([trainers.md](trainers.md#starting-a-battle)) |
| `wildbattle(species, level, shiny)` | a wild battle (`shiny` is a `u8` constant) |
| `getstaticencounteroutcome(VAR)` | how a legendary battle ended |

### Sound and screen

| Command | Does |
|---|---|
| `playse(SEQ_SE_X)`, `waitse(SEQ_SE_X)` | a sound effect |
| `playfanfare(SEQ_ME_X)`, `waitfanfare` | a jingle |
| `playcry(species, 0)`, `waitcry` | a cry |
| `playbgm(SEQ_GS_X)`, `stopbgm(0)`, `fadeoutbgm(0, 30)`, `tempbgm(SEQ_GS_X)` | music ([music.md](music.md)); all `u16` constants. `fadeoutbgm`'s second argument is the length in frames |
| `fadescreen(6, 1, 0, RGB_BLACK)`, `waitfade` | the arguments are duration, speed, type and colour. Type 0 fades out (`FADE_TYPE_BRIGHTNESS_OUT`) and 1 fades in; retail scripts nearly always use `6, 1` or `6, 6` |
| `screenshake(x, y, repeats, period)` | shake the screen |

### Time

| Command | Does |
|---|---|
| `getweekday(VAR)` | 0 = Sunday ... 6 |
| `getcurrenthour(VAR)` | 0-23 |
| `getcurrenttimeofday(VAR)` | morning, day, evening, night, late night (`RTC_TIMEOFDAY_*`) |

## 4. Commands that open screens

Many commands launch an application (the PC, the Pokédex, the bag, a trade, the name
screen) and wait until it closes. They come in pairs or with a result variable:

- `partyselectui` + `getpartyselection(VAR)`;
- `nicknameinput(slot, VAR)`;
- `martbuy(n)`, `martsell`;
- `openpcbox(mode)`, `opendressup(mode, VAR, arg)`.

Search the list for `Open` or `UI` to find others. They work from any NPC or sign script, because the
command does the launching ([ui.md](ui.md#launching-an-application) explains what
happens underneath).

## 5. Standard scripts (`callstd`)

`callstd(std_x)` runs one of the shared scripts in `files/fielddata/script/scr_seq/` and
waits for it. They are the nearest thing to pokeemerald's `std` and many of its specials.
Ids are in [include/constants/std_script.h](../../include/constants/std_script.h), and
`sScriptBankMapping` in [src/script_manager.c](../../src/script_manager.c) maps each range to
its script file. The ones map scripts use most:

| Script | Does | Set first |
|---|---|---|
| `std_give_item_verbose` | "X received the Y!", fanfare, "put it in the ... pocket" | `VAR_SPECIAL_x8004` item, `x8005` quantity (or `GiveItemNoCheck`) |
| `std_obtain_item_verbose` | the other wording of the same message; retail gift scripts use both | the same |
| `std_bag_is_full` | the "bag is full" message | |
| `std_nurse_joy` | the whole Pokémon Center nurse | `VAR_SPECIAL_x8007` (copy the value from a retail Center) |
| `std_pokecenter_pc` | the Center PC | |
| `std_mart_intro`, `std_pokemart`, `std_special_mart` | a mart clerk ([items.md](items.md#marts)) | `VAR_SPECIAL_x8004` = the mart |
| `std_prompt_save` | "Would you like to save?" | |
| `std_signpost`, `std_hidden_item_fanfare`, `std_bike_rack` | signs, hidden items, bike racks | |
| `std_phone_call` (or the `PhoneCall` helper) | a scripted Pokégear call | `VAR_SPECIAL_x8004`-`x8006` |
| `std_play_rival_intro_music` / `std_fade_end_rival_intro_music` (and the friend, Eusine, Kimono Girl... pairs) | character themes during a scene | |
| `std_trainer(TRAINER_X)`, `std_trainer_2(...)` | an NPC trainer's whole battle ([npcs-and-scripts.md](npcs-and-scripts.md#trainers)) | |

All 649 ids are in the header. The 2000-2999 ones are listed with their use counts in
[script-commands-list.md](script-commands-list.md#standard-scripts-callstd). Trainer,
item-ball and hidden-item ids are computed per trainer or item.

## 6. Adding a command

1. Write `BOOL ScrCmd_MyCommand(ScriptContext *ctx)`. Read the arguments in order with
   `ScriptGetVar` (number or variable), `ScriptGetVarPointer` (a result variable) or
   `ScriptReadHalfword`/`Byte`/`Word` (constants). Return `FALSE`, or `TRUE` after
   `SetupNativeScript` to wait. Declare it in `include/scrcmd.h`.
2. Append it to `gScriptCmdTable` in `src/data/fieldmap/script_cmd_table.h`. Its position is
   its number (853 is the next one). **Don't insert in the middle**: every command after it
   would change number and every compiled script would break.
3. Add the macro to `asm/macros/script.inc`, with a `//` comment above it (the list shows
   it):

   ```
       // Sets VAR to the party's highest level
       .macro GetPartyMaxLevel var
       .short 853
       .short \var
       .endm
   ```

4. Use it in a `.pory` file as `getpartymaxlevel(VAR_SPECIAL_RESULT)`, and regenerate the
   list: `python3 tools/scriptcmds/scriptcmds.py --markdown > docs/modding/script-commands-list.md`.

A command that should appear as a condition (`if (getpartymaxlevel() > 50)`) also needs an
`autovar` entry in `tools/mapkit/script_config.json` ([SCRIPTING.md](SCRIPTING.md#conditions)).

Where to put the function: `src/scrcmd_c.c`, `scrcmd_items.c` and most other `scrcmd_*.c`
files are static ARM9, so their commands work from any script. A command in an overlay
only works while that overlay is loaded ([engine.md §5](engine.md#5-overlays)):

- `overlay_03_scrcmds.c` is in `OVY_3`, which is loaded on ordinary maps.
- `overlay_22.c`, with the coin and points commands, is in `OVY_22`. Scripts load it
  themselves with **`scriptoverlaycmd(3, 0)`** and unload it with `scriptoverlaycmd(3, 1)`.
  Index 3 picks `OVY_22` from the table in `ScrCmd_ScriptOverlayCmd`; 0-4 are `OVY_20`,
  `bug_contest`, `OVY_21`, `OVY_22` and `OVY_25`.

Calling `getcoinamount` without that load runs whatever is at that address.

Static ARM9 space is the tight resource, so keep a large command small, or put its bulk in
one of those overlays and load it from the script.
