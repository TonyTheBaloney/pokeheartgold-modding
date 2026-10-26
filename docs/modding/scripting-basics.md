<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# The basics of scripting

> AI-generated; not affiliated with pret. See AI.md at the repository root.

A tutorial for people who have never written a game script. It builds one small
event in Cherrygrove City, a fisherman, a step at a time, and explains each new idea
when it first appears. When you finish it you will be able to make an NPC talk, give
an item once, ask a yes/no question, move people around and start a scene when the
player steps on a tile.

The reference guides go further:
[SCRIPTING.md](SCRIPTING.md) (the language), [script-commands.md](script-commands.md)
(commands by task), [npcs-and-scripts.md](npcs-and-scripts.md) (NPCs, flags, text).

## 0. What a script is

Almost everything that *happens* on a map is a script: an NPC talking, a sign, an
item ball, a rival who blocks the road, a gym leader's battle. A script is a list of
**commands** the game runs from top to bottom, such as "show this text", "wait for a
button", "give an item", "walk two steps left".

Every map keeps its scripts in one file:

```
data/maps/<MapName>/scripts.pory
```

The game runs a script when one of these happens:

| Event | Where it's set up | Example |
|---|---|---|
| The player talks to an **NPC** | `object_events` in `map.json` | most people |
| The player reads a **sign** or checks a tile | `bg_events` in `map.json` | town signs, bookshelves |
| The player steps on a **trigger** tile | `coord_events` in `map.json` | a rival who stops you |
| The map **loads** | the `mapscripts` block in `scripts.pory` | hiding an NPC after an event |

In `map.json` each of these has a `"script"` field that names a script in
`scripts.pory`. That name links the two files.

## 1. Before you start

You need a build that works ([README.md](README.md#building-a-modified-rom)):

```sh
make release          # builds build/heartgold.us/pokeheartgold.us.nds
```

Commit (or copy) the unmodified project first, so that you can always compare your
changes with the original.

Most steps below use `mapkit`, the map tool in this repository. Save typing with a
shell variable:

```sh
M=tools/mapkit/mapkit.sh       # in fish: set M tools/mapkit/mapkit.sh
$M show Cherrygrove            # NPCs, signs, triggers and the scripts they run
```

Open `data/maps/Cherrygrove/scripts.pory` in your editor and look around. You don't
need to understand it yet; you will recognise most of it by the end.

## 2. Your first NPC

Add a fisherman who says one thing:

```sh
$M script add Cherrygrove Cherrygrove_EventScript_Fisher
$M npc add Cherrygrove fisher SPRITE_FISHING_2 532 404 \
    --movement MOVEMENT_TYPE_LOOK_AROUND --script Cherrygrove_EventScript_Fisher
```

The first command adds an empty script to the end of `scripts.pory`. The second adds
the NPC to `map.json` at tile (532, 404) and points it at that script. (To put
someone elsewhere, see [maps-and-warps.md](maps-and-warps.md#coordinates) for how
coordinates work.)

Now fill in the script. At the bottom of `scripts.pory` you will find:

```
script Cherrygrove_EventScript_Fisher {
}
```

Make it:

```
script Cherrygrove_EventScript_Fisher {
    playse(SEQ_SE_DP_SELECT)
    lockall
    faceplayer
    npcmsg("The sea breeze here\n"
           "is so refreshing!")
    waitbuttonpress
    closemessage
    releaseall
    end
}
```

Build and play:

```sh
$M validate Cherrygrove
make release
```

Walk up to the fisherman and press A. Line by line:

| Line | What it does |
|---|---|
| `script Cherrygrove_EventScript_Fisher { ... }` | the script and its name. By convention names are `<Map>_EventScript_<Who>` |
| `playse(SEQ_SE_DP_SELECT)` | the little "click" every NPC makes when you talk to them |
| `lockall` | freezes the player and everyone else, so nobody walks off mid-conversation |
| `faceplayer` | turns the NPC toward the player |
| `npcmsg("...")` | opens the text box and prints the text |
| `waitbuttonpress` | waits for the player to press A or B |
| `closemessage` | closes the text box |
| `releaseall` | lets everyone move again |
| `end` | the script is finished |

Almost every NPC script starts with `playse`, `lockall`, `faceplayer` and ends with
`waitbuttonpress`, `closemessage`, `releaseall`, `end`. If you remember only one thing
from this tutorial, remember that pattern: the parts in between change, that frame
doesn't.

> **If you forget `releaseall`**, the player stays frozen forever after the text
> closes. If you forget `lockall`, the NPC may walk away while you talk to them.

## 3. Writing text

Text goes between double quotes. Two strings next to each other are joined, so you
can write one line of the text box per line of code:

```
npcmsg("First line of the box\n"
       "second line of the box\r"
       "this scrolls up into view.\f"
       "And this starts an empty box.")
```

| Code | Meaning |
|---|---|
| `\n` | new line inside the box (a box shows two lines) |
| `\r` | wait for a button, then scroll up by one line |
| `\f` | wait for a button, then clear the box and start fresh |

The box is narrow. Keep each line under about 30 characters and test it in game; a
line that's too long runs off the edge of the box.

**The player's name.** Put it in a "string slot" first, then use the slot in the text:

```
bufferplayersname(0)
npcmsg("Hi, {STRVAR_1 3, 0, 0}!\n"
       "Caught anything good?")
```

`bufferplayersname(0)` fills slot 0 and `{STRVAR_1 3, 0, 0}` prints it. Other
`buffer...` commands fill slots with an item, species or move name, or a number
([script-commands.md](script-commands.md#text)). Copy the `{STRVAR_1 ...}` code
from an existing script that does what you want.

You never edit text numbers by hand: the build stores your strings in the map's
`text.json` by itself ([SCRIPTING.md](SCRIPTING.md#text) explains how).

## 4. Remembering things: flags

Let the fisherman give the player a Potion, but only once. The game needs to
*remember* that it already happened, even after the player saves and turns the game
off. That memory is a **flag**: a single on/off switch stored in the save file.

Every flag is a name in `include/constants/flags.h`. You need one that nothing else
uses. [unknown-flags-vars.md](unknown-flags-vars.md#free-flags) lists the free ones;
`FLAG_UNK_040` is one of them. Give it a name that says what it means: in
`include/constants/flags.h`, change

```c
#define FLAG_UNK_040      0x40
```

to

```c
#define FLAG_GOT_POTION_FROM_CHERRYGROVE_FISHER      0x40
```

and check that nothing else used the old name:

```sh
$M refs FLAG_UNK_040           # should find nothing
```

Now the script:

```
script Cherrygrove_EventScript_Fisher {
    playse(SEQ_SE_DP_SELECT)
    lockall
    faceplayer
    if (flag(FLAG_GOT_POTION_FROM_CHERRYGROVE_FISHER)) {
        npcmsg("Nothing’s biting today...")
        waitbuttonpress
        closemessage
        releaseall
        end
    }
    npcmsg("You look like a new Trainer.\n"
           "Take this with you!\r")
    if (!itemspace(ITEM_POTION, 1)) {
        callstd(std_bag_is_full)
        closemessage
        releaseall
        end
    }
    giveitemnocheck(ITEM_POTION, 1)
    setflag(FLAG_GOT_POTION_FROM_CHERRYGROVE_FISHER)
    closemessage
    releaseall
    end
}
```

New pieces:

- **`if (condition) { ... }`** runs the lines between `{` and `}` only when the
  condition is true. `flag(F)` is true when flag `F` is set; `!` means "not".
- **Each branch ends with its own `end`.** The first `if` handles "already got
  it": it talks, cleans up and ends, so the rest of the script never runs a second time.
- `itemspace(ITEM_POTION, 1)` is true when the bag has room for one Potion.
  `callstd(std_bag_is_full)` shows the game's usual "bag is full" message.
- `giveitemnocheck(ITEM_POTION, 1)` puts the Potion in the bag and shows
  "*Player* received the Potion!" with the fanfare.
- `setflag(...)` turns the flag on. Next time, the first `if` is true.

Set the flag **after** giving the item. If you set it first and the bag is full, the
player never gets the Potion.

`clearflag(F)` turns a flag off again. You can write `else` and `elif` too:

```
if (flag(FLAG_A)) {
    ...
} elif (flag(FLAG_B)) {
    ...
} else {
    ...
}
```

## 5. Asking a question

A yes/no box is a message that ends with `{YESNO 0}`, followed by reading the
answer:

```
npcmsg("Want me to tell you about fishing? {YESNO 0}")
touchscreenmenuhide
getmenuchoice(VAR_SPECIAL_RESULT)
touchscreenmenushow
if (var(VAR_SPECIAL_RESULT) == 0) {
    npcmsg("Find a Rod first, then face\n"
           "the water and use it!")
} else {
    npcmsg("Suit yourself.")
}
waitbuttonpress
```

`getmenuchoice` waits for the player's choice and writes it into a **variable**:
0 for Yes, 1 for No. Copy the three lines around it as they are; every yes/no in the
game uses them.

## 6. Variables

A flag is on or off. A **variable** ("var") holds a number from 0 to 65535, which is
useful for anything with more than two states: how far a quest has got, a counter, a
choice from a menu.

| Kind | Names | Lasts |
|---|---|---|
| Saved vars | `VAR_*` in `include/constants/vars.h` | for good (in the save file) |
| Temporary vars | `VAR_TEMP_x4000` ... | until the player leaves the map |
| Special vars | `VAR_SPECIAL_RESULT`, `VAR_SPECIAL_x8004` ... | scratch space for commands, overwritten all the time |

Use temporary or special vars for short-lived values (the menu answer above), and a
saved var for a quest's progress. Free saved vars are listed in
[unknown-flags-vars.md](unknown-flags-vars.md#free-vars), the same way as flags.

```
setvar(VAR_X, 2)                   // VAR_X = 2
addvar(VAR_X, 1)                   // VAR_X = VAR_X + 1
if (var(VAR_X) == 3) { ... }       // also !=, <, <=, >, >=
```

For many values, `switch` reads better than a chain of `elif`:

```
getweekday(VAR_SPECIAL_RESULT)
switch (var(VAR_SPECIAL_RESULT)) {
    case 0:
        npcmsg("Sundays are for resting.")
    case 6:
        npcmsg("Saturdays are for fishing!")
    default:
        npcmsg("I’d rather be fishing.")
}
```

Each `case` stops by itself at the next one; you don't need `break`.

## 7. Moving people

Movements are written in a separate `movement` block, then run with
`applymovement`:

```
movement Cherrygrove_Movement_FisherSurprised {
    emote_exclamation_mark
    walk_left * 2
    face_down
}
```

```
applymovement(obj_T21_fisher, Cherrygrove_Movement_FisherSurprised)
waitmovement
```

- The first argument is who moves: the NPC's `local_id` from `map.json`
  (`obj_T21_fisher`; `$M show Cherrygrove` lists them), or `obj_player` for the player.
- `walk_left * 2` means two steps left. Other actions: `walk_up`/`down`/`left`/`right`,
  `walk_fast_...`, `walk_slow_...`, `face_...`, `jump_...`, `walk_in_place_...`,
  `delay_8`, `emote_exclamation_mark`. [SCRIPTING.md](SCRIPTING.md#movement) explains
  the naming.
- `waitmovement` waits until everyone has finished moving. Without it the script carries
  on while they're still walking.
- You can start several movements (the player and an NPC) and then wait once for all of them.

Put `movement` blocks after the script that uses them, outside its `{ }`.

**Making someone disappear.** `hideperson(obj_T21_fisher)` removes the fisherman at
once, but he is back the next time the map loads. To keep him gone, give him a hide
flag in `map.json` (`"flag": "FLAG_..."`) and set that flag in the script:

```
setflag(FLAG_HIDE_CHERRYGROVE_FISHER)
hideperson(obj_T21_fisher)
```

An NPC whose `flag` is set doesn't appear. `clearflag` + `showperson` brings it
back.

## 8. Signs and triggers

**A sign** is a script with no NPC. Add a `bg_events` entry to `map.json`:

```json
{ "type": "BG_TYPE_SIGNPOST", "x": 534, "y": 404, "elevation": 0,
  "player_facing_dir": "BG_DIR_ALL", "script": "Cherrygrove_EventScript_PierSign" }
```

and the script (signs often just show text):

```
script Cherrygrove_EventScript_PierSign {
    lockall
    npcmsg("Cherrygrove Pier\n"
           "No swimming!")
    waitbuttonpress
    closemessage
    releaseall
    end
}
```

`$M script add Cherrygrove Cherrygrove_EventScript_PierSign` creates the empty block
for you, as in step 2. See [maps-and-warps.md](maps-and-warps.md) for the other sign
types.

**A trigger** runs a script when the player steps on its tiles. It is a
`coord_events` entry in `map.json`, from Cherrygrove (the Guide Gent's tour):

```json
{ "x": 566, "y": 397, "elevation": 0, "width": 1, "height": 4,
  "var": "VAR_SCENE_CHERRYGROVE_CITY_OW", "var_value": 0,
  "script": "Cherrygrove_EventScript_GuideGentTour" }
```

The trigger covers `width` x `height` tiles, and fires **only while `var` equals
`var_value`**. That's how a scene happens once: the script changes the var at the
end, so the trigger stops matching:

```
script Cherrygrove_EventScript_FisherScene {
    lockall
    applymovement(obj_T21_fisher, Cherrygrove_Movement_FisherSurprised)
    waitmovement
    npcmsg("Hey! Watch where you’re walking!")
    waitbuttonpress
    closemessage
    setvar(VAR_FISHER_SCENE, 1)
    releaseall
    end
}
```

(`VAR_FISHER_SCENE` here is a free saved var you renamed, as with the flag in step
4; `VAR_UNK_4059` is one. Saved vars start at 0 in a new game.)

**When the map loads**, the `mapscripts` block at the end of `scripts.pory` can run
a script. It's used to put things in the right state before the player sees the map,
for example moving an NPC that has finished a quest:

```
mapscripts Cherrygrove_MapScripts {
    INIT_SCRIPT_ON_TRANSITION: Cherrygrove_OnTransition
}
```

Every map has at most one `mapscripts` block; add to the existing one.
[npcs-and-scripts.md](npcs-and-scripts.md#init--level-scripts-mapscripts) lists the kinds.

## 9. When something goes wrong

| Problem | Likely cause |
|---|---|
| The build stops with `scripts.pory:<line>: ...` | a typo at that line: a missing `)` or `}`, a misspelt command or constant. The message says what it expected |
| `$M validate` reports an unknown script | the name in `map.json` doesn't match the name after `script` in `scripts.pory` |
| The player can't move after talking | a path through the script that misses `releaseall` |
| Talking to the NPC does nothing | `"script"` in `map.json` is `0` or names another script; check with `$M show <Map>` |
| The event happens every time | the flag or var is never set, or is set in a branch that doesn't run |
| The NPC is gone and won't come back | its hide `flag` is set; something sets it, or it's a flag another event uses |
| Text runs off the box | line too long; break it with `\n` |
| A trigger never fires | its var doesn't equal `var_value`, or the player doesn't walk onto those tiles |
| It worked, then broke after you reordered scripts | scripts are numbered by position; read [SCRIPTING.md](SCRIPTING.md#script-numbers-scrdef) before moving `script` blocks around or editing the `scrdefs` list |

`$M pory show Cherrygrove` prints exactly what your script turns into, if you want to
see the commands the game receives.

## 10. Where to go next

- **Learn from the game.** Every retail script is in `data/maps/*/scripts.pory`. Find
  an event that does what you want and copy it. To find who uses a command:
  `grep -rn 'givemon(' data/maps`.
- **Find a command for a job.** HGSS has no "specials"; every feature is a command.
  [script-commands.md](script-commands.md) groups the common ones by task, and
  `python3 tools/scriptcmds/scriptcmds.py --find <word>` searches all 853.
- **Give a Pokémon, start a battle:** `givemon(...)`, `wildbattle(...)`,
  `trainerbattle(...)` in [script-commands.md](script-commands.md#pokémon-and-party)
  and [trainers.md](trainers.md#starting-a-battle).
- **Menus with more than two choices:** [ui.md](ui.md#menus-from-scripts).
- **Shared scripts** (Nurse Joy, marts, the save prompt): `callstd(...)`,
  [script-commands.md](script-commands.md#5-standard-scripts-callstd).
- **Story flags:** [story-progression.md](story-progression.md) lists the flags and
  vars the main story uses, so your events can check how far the player has got.
- **The full language** (`while`, `goto`/`call`, `const`, version differences):
  [SCRIPTING.md](SCRIPTING.md).
