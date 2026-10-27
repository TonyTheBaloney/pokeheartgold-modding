<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# The Pokéwalker

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The Pokéwalker is a pedometer that came with HeartGold and SoulSilver. You send a
Pokémon from your PC to it over infrared and walk around with it. Later you link
again to get the Pokémon back, along with steps, watts, the Pokémon it caught and
the items it found. The game side is the **Connect to Pokéwalker** option on the
title menu. It runs as overlay 112, an app separate from the field.

The ROM decides more than you might expect. It holds the table of 27 courses: which
Pokémon and items each course offers, how many watts unlock it, and its image. It
also decides what experience and friendship the Pokémon gets when it comes back. It
picks the course's Pokémon each time you send one, and it draws every name the
Pokéwalker shows as a small bitmap. What the device does with that data during the
walk (counting steps, earning watts, when a Pokémon or item turns up) is the
Pokéwalker's own firmware, and none of that is in this repository.

pokeemerald has nothing like it. The closest thing is the e-Reader/Mystery Gift code,
and that isn't close.

## Where things are

| What | File |
|---|---|
| saved Pokéwalker data (`POKEWALKER`, 0x134 bytes) and its accessors | `include/pokewalker.h:9`, `src/pokewalker.c` |
| course ids `WALKER_COURSE_*` (27 courses) | `include/constants/pokewalker_courses.h` |
| the course table `sPokewalkerCourses` (raw bytes) | `asm/pokewalker_data.s:707`-`1035`; layout in `PokewalkerCourse`, `include/application/pokewalker/pokewalker_app.h:43` |
| course names and descriptions | `files/msgdata/msg/msg_0274.json`, messages 91-117 (names) and 119-145 (descriptions) |
| unlocking courses with watts | `PokewalkerApp_UnlockNextCourse`, `src/application/pokewalker/pokewalker_ui.c:107` |
| other ways a course unlocks | `src/update_dex_received.c:22` (Jirachi), `src/gts/gts_transaction.c:747` (GTS), `src/scrcmd_mystery_gift.c:553` (Mystery Gift) |
| building the data sent with the Pokémon | `PokewalkerApp_BuildStrollData`, `src/application/pokewalker/pokewalker_upload.c:427` |
| the Pokémon coming back: experience, friendship | `src/application/pokewalker/pokewalker_stroll.c:134`-`220` |
| caught Pokémon, items, gifts, Starf Berry | `src/application/pokewalker/pokewalker_stroll.c:201`-`343` |
| choosing a course, the link screens, steps and watts | `src/application/pokewalker/pokewalker_link.c` |
| the infrared protocol | `src/application/pokewalker/pokewalker_ir.c`, `pokewalker_ir_requests.c`, `pokewalker_ir_status.c`; structs in `include/application/pokewalker/pokewalker_ir.h` |
| erasing the Pokéwalker | `src/application/pokewalker/pokewalker_erase.c` |
| Trainer House sets swapped through the Pokéwalker | `src/application/pokewalker/pokewalker_trainer_house.c` |
| Pokéwalker pictures and icons of Pokémon | prebuilt NARCs `files/a/2/5/6` (pictures) and `files/a/2/4/8` (icons) |

## 1. What a link does

The app's top level depends on the saved **stroll state**, the first field of
`POKEWALKER` (`PokewalkerApp_MainMenu_Start`, `pokewalker_main_menu.c:53`-`100`):

| `strollState` | Meaning | Set by |
|---:|---|---|
| 0 | never linked, or erased | `Pokewalker_Init` clears it (`src/pokewalker.c:16`) |
| 1 | linked before; no Pokémon is out on a Stroll | after the Pokémon comes back (`pokewalker_app_modes.c:133`, `:156`) |
| 2 | a Pokémon is out on a Stroll | when it leaves (`pokewalker_stroll.c:56`) |

The second field (`unk_002`) holds the PC box the Pokémon came from. The Pokémon goes
back to that box, or to the next box with a free slot (`pokewalker_stroll.c:143`,
`:161`).

Before anything else, the app needs at least 5 empty PC slots
(`pokewalker_main_menu.c:60`, message 15). It also stops if there is no Pokémon in the
PC and you have never linked (`:65`).

What you pick sets `app->linkAction` (`pokewalker_link.c:1`):

| `linkAction` | Menu item | Request sent | Afterwards (`PokewalkerApp_LinkSave_Enter`, `pokewalker_app_modes.c:125`) |
|---:|---|---|---|
| 0 | Go for a Stroll | 0x32 the first time (stroll state 0), otherwise 0x52 (`pokewalker_link.c:415`) | the Pokémon leaves the PC (`pokewalker_stroll.c:52`) |
| 1 | Return from a Stroll | 0x40 | the Pokémon comes back, gifts are received, a course may unlock |
| 2 | Receive a gift | 0x60 | items and Pokémon received; nothing returns |
| 4 | Send Pokémon back home | 0x40 | the Pokémon comes back without its finds (message 18 warns about this) |

For actions 1, 2 and 4, the request column is inferred: the 0x40 and 0x60 functions say what they read, but the state-table path from `PokewalkerApp_Link_Start` (`pokewalker_link.c:79`) to them wasn't traced.

The app saves with `SaveGameNormal` when a Stroll starts (`pokewalker_stroll.c:92`), after a receive (`pokewalker_app_modes.c:193`, `:223`) and after erasing (`pokewalker_erase.c:448`).

## 2. The infrared protocol

You only need this section if you want to understand what crosses the link. Nothing
here is usually worth changing. The notes are from `pokewalker_ir.c`.

- **Hardware.** The IR transceiver is on the game card and is reached through the
  card's SPI bus (`CARD_SpiWaitReadRange` / `CARD_SpiWaitWriteRange`,
  `pokewalker_ir.c:58`-`72`).
- **Packets.** Each packet is an 8-byte header (command, argument, 16-bit checksum,
  32-bit session id) followed by the payload. Every byte is XORed with 0xAA before it
  is sent (`PokewalkerIr_SendPacket`, `pokewalker_ir.c:80`; checksum at `:28`).
- **Handshake.** Commands 0xFC, 0xFA and 0xF8 set up the session. The session id is
  the peer's id XORed with the game's own, which is taken from the tick counter
  (`pokewalker_ir.c:237`-`294`). 0xF6 and 0xF4 close the link.
- **Identity check.** The game sends a 0x68-byte identity block
  (`PokewalkerIrIdentity`, `pokewalker_ir.h:15`): trainer id, name, game version, the
  save's random "IR clock", and the time. `PokewalkerIr_ValidatePeer`
  (`pokewalker_ir.c:786`) refuses a Pokéwalker that is already registered (0x32), that
  isn't registered, that belongs to another trainer id, or that is in the wrong state
  for the request. The errors become messages 34-43 (`PokewalkerApp_GetLinkErrorMessage`,
  `pokewalker_link.c:995`).
- **Transfers.** Data moves in chunks of up to 128 bytes, each to or from an address
  on the Pokéwalker (`PokewalkerIr_SendChunk`, `:413`; `PokewalkerIr_RequestChunk`,
  `:507`). Large uploads are LZ-compressed in 128-byte blocks first
  (`PokewalkerIr_CompressBlocks`, `:336`).

The four requests the app uses:

| Command | Function | What it moves |
|---|---|---|
| 0x32 register + send | `PokewalkerIr_RequestUpload` (`pokewalker_ir_requests.c:62`) | the **upload image** (0x8C50 bytes to address 0x280), the stroll data (0x28BE bytes to 0xD700), the game's own record (0x224 bytes to 0xD480) |
| 0x52 send again | `PokewalkerIr_RequestSendStroll` (`:98`) | stroll data and record only; then it reads the status back |
| 0x40 receive | `PokewalkerIr_RequestReceive` (`:85`) | reads the walking Pokémon (42 bytes from 0x8F00), the status (0xD4C bytes from 0xCE80), the gift blocks (from 0xB800) and the event records (from 0xDE24) |
| 0x60 receive gifts | `PokewalkerIr_RequestReceiveGifts` (`pokewalker_ir_status.c:8`) | status, gift blocks and records |

The addresses are from the `PokewalkerIr_BeginTransfer` calls in `pokewalker_ir.c`
(lines 469-484, 596-681, 966-1020). The code also handles commands 0x2A (erase,
`:1113`), 0xE0/0xE2/0xF0/0xFE and 0xB0-0xBE, but no request function in the app
sets those last ones.

## 3. Sending a Pokémon

You pick a box Pokémon and a course. The course list shows every unlocked course id
from 0 to 26 in order, five per page (`PokewalkerApp_ListUnlockedCourses`,
`pokewalker_link.c:210`). The Pokémon is copied into the save's `POKEWALKER` and
deleted from the PC (`pokewalker_stroll.c:56`-`59`).

`PokewalkerApp_BuildStrollData` (`pokewalker_upload.c:427`) fills
`PokewalkerStrollData` (`pokewalker_app.h:54`):

- **The walking Pokémon:** species, moves, level, form, shininess, friendship,
  gender, nickname, and the BASE_FLIP flag from its personal data (lines 445-460).
  Its picture comes from NARC `a/2/5/6` via `PokewalkerApp_GetPictureFile`
  (`pokewalker_ui.c:70`). Spinda gets its spots drawn on (line 494). Its icon comes
  from `a/2/4/8`.
- **Three course Pokémon.** The course has six Pokémon in three pairs, and one of
  each pair is chosen at random. The RNG is seeded from the clock
  (`PokewalkerApp_PickRouteMons`, `pokewalker_upload.c:382`-`407`). Each one keeps
  its species, level, held item, form, gender, moves, steps and chance. Only the
  third pick's picture is sent (line 474).
- **Advantage types.** If the walking Pokémon has one of the course's three types,
  the three Pokémon's step values become 75% of the table value
  (`PokewalkerApp_ApplyAdvantageTypes`, `pokewalker_upload.c:410`-`425`).
- **Ten course items**, each with its steps and chance (lines 480-484).
- **The course image:** `routeImageId - 1` and a 0xC0-byte picture from
  `gPokewalkerRouteImages` (lines 461, 485).
- **Text as pictures.** The course name, the nickname, the three species names and
  the ten item names are printed into windows. They are then converted to the
  Pokéwalker's 2-bit format (`PokewalkerApp_PrintStrollTexts`, `:520`;
  `PokewalkerApp_ConvertTo2bpp`, `:584`). The Pokéwalker never receives text, only
  these bitmaps.

On first registration (0x32), the **upload image** is also sent
(`PokewalkerApp_BuildUploadImage`, `pokewalker_upload.c:203`). It is built from
dozens of small graphics in `asm/pokewalker_data.s` (digits, arrows, menu pieces)
and the player's name, rendered the same way. Request 0x52 doesn't send it again
(`PokewalkerApp_BuildSendStrollData`, `pokewalker_app.c:271`).

## 4. Coming back: steps, watts, experience, friendship

**Steps.** The save keeps the Pokéwalker's step counter from the last link. When a
link reads the status, `PokewalkerApp_UpdateSavedSteps` (`pokewalker_link.c:687`)
stores the device's current count. It keeps the old one if the new one is lower. The
Stroll's steps are the new count minus the old one (`pokewalker_link.c:763`).

**Watts.** `Pokewalker_SetStepsAddWatts` (`src/pokewalker.c:35`) **replaces** the
steps and **adds** the watts the Pokéwalker sent (`irStatus.watts`, a `u16`). The
total stops at 9,999,999. Message 45 ("Collected … W on the Stroll!") suggests
`irStatus.watts` is what was earned since the last link. The saved total only grows.
The game never spends it, and it is used only for unlocking courses (§6).

**Experience.** One experience point per step, but never past the next level
(`PokewalkerApp_AddStrollExp`, `pokewalker_stroll.c:173`-`198`):

```c
toNextLevel = CalcBoxMonExpToNextLevel(boxMon);
if (exp >= toNextLevel) {
    exp = toNextLevel;
    leveledUp = TRUE;
}
```

So a Stroll gives **at most one level** (message 52). After the level-up,
`CalcMonLevelAndStats` recalculates the stats. No moves are learned and nothing
evolves here. Level 100 Pokémon get nothing.

**Friendship.** There are two sources:

| When | Change | Code |
|---|---|---|
| the Stroll was 5000 steps or more | +1 (up to 255) | `PokewalkerApp_AddStrollFriendship`, `pokewalker_stroll.c:211`-`220` |
| the Pokémon leveled up | `MonApplyFriendshipMod(mon, 0, 8)`: event 0 (`FRIENDSHIP_EVENT_GROW_LEVEL`, +5/+3/+2 by tier), with the usual Luxury Ball and location bonuses | `pokewalker_stroll.c:194`; table at `src/pokemon.c:2020` |

The `8` passed as `location` is compared with the Pokémon's egg/met location
(`src/pokemon.c:2062`). What map section 8 stands for here wasn't checked.

**Which Pokémon comes back.** Normally it's the copy kept in the save
(`Pokewalker_TryGetBoxMon`), so its IVs, OT and ribbons are unchanged. If the
Pokéwalker reports `hasWalkerMon`, the game makes a new Pokémon from the Pokéwalker's
data instead (`pokewalker_stroll.c:153`-`159`). It gets the player as OT, a random
nature and the met location "Pokéwalker". The code doesn't say when the Pokéwalker
sets that flag.

## 5. What else comes back

`PokewalkerApp_ReceiveMons` and `PokewalkerApp_ReceiveItems`
(`pokewalker_stroll.c:250`-`337`) handle the rest:

| Received | Becomes |
|---|---|
| up to 3 Pokémon caught on the Stroll (`irStatus.caughtMons`) | new Pokémon with the species, level, held item, moves, form and gender from the **course table entry** the Pokéwalker sent back. The player is OT, the met location is `MAPSEC_POKEWALKER` (233, `include/constants/map_sections.h:237`) and the nature is `MTRandom() % 24` (line 300). They go to the first free PC slot and are marked seen and caught. |
| a gift Pokémon (`irBlocks.giftMon`) | made from the Pokéwalker's data, with that data's OT name, OT id, OT gender, met location, ability and ball, and the fateful-encounter flag set (lines 309-334). If the data says shiny, its personality is made shiny (`ChangePersonalityToNatureGenderAndAbility`, `src/pokemon.c:3874`-`3881`). |
| items: 3 + 10 entries in the status, and a gift item block | each non-empty one goes into the bag, 1 of each (lines 250-267) |
| Starf Berry | once per save: given if the Pokéwalker sets `giveStarfBerry` and the save's `receivedStarfBerry` is still 0 (`PokewalkerApp_GiveStarfBerry`, line 201). Messages 53-54 tie it to reaching 9,999,999 steps; that decision is made on the device. |
| other games' records | the event log (24 records, `pokewalker_event_log.c`). Trainer House sets from other HeartGold/SoulSilver games go into the Trainer House (`PokewalkerApp_AddPeerTrainerHouseSets`, `pokewalker_link.c:675`). |

The nature roll is `% 24`, so a Pokémon caught on a Stroll is never nature 24
(Quirky), and neither is a gift. The non-shiny branch of
`ChangePersonalityToNatureGenderAndAbility` asserts that `nature & 1` equals the
ability bit, and the caller passes `nature & 1` (`pokewalker_stroll.c:238`).

The Pokémon on the Pokéwalker still counts as owned in one place:
`GetOwnedRotomFormsMask` checks it (`src/scrcmd_c.c:4314`-`4322`).

## 6. Courses and how they unlock

The bit field `unlockedCourses` in the save holds one bit per course
(`Pokewalker_UnlockCourse`, `src/pokewalker.c:112`). A new save starts with Refreshing
Field and Noisy Forest (`Pokewalker_Init`, `src/pokewalker.c:15`-`19`). Erasing the
Pokéwalker clears everything else but keeps the unlocked courses (`Pokewalker_Reset`,
`:21`).

**By watts.** After every "Return from a Stroll", `PokewalkerApp_UnlockNextCourse`
(`pokewalker_ui.c:107`-`124`, called at `pokewalker_app_modes.c:145`) walks courses 0
to `count - 1`. It unlocks the **first** locked course whose `wattsRequired` is at or
below the saved watts total, and then stops:

- `count` is 8 without the National Pokédex and 20 with it (`pokewalker_ui.c:112`-`116`).
- At most **one course per link**. If you have watts for three, you get them over
  three links.
- "Watts required to find the next Route" uses the same loop
  (`PokewalkerApp_GetWattsToNextCourse`, `pokewalker_ui.c:126`).

**Not by watts.** Courses 20-26 are past both counts, so watts never unlock them:

| Course | Unlocked by | Code |
|---|---|---|
| 20 Beyond the Sea | receiving a Pokémon from another language on the GTS | `src/gts/gts_transaction.c:751` |
| 21 Night Sky's Edge | any received Pokémon that is Jirachi (`UpdatePokedexWithReceivedSpecies`, called by gifts, trades, eggs, Mystery Gift...) | `src/update_dex_received.c:21`-`24` |
| any course 0-26 | a Mystery Gift card of type `MG_TAG_POKEWALKER_COURSE` (14); the card's `pokewalkerCourse` byte is the course id. It is refused if that course is already unlocked. | `src/scrcmd_mystery_gift.c:553`-`569`; `include/mystery_gift.h:22`, `:54` |

Courses 22-26 (Yellow Forest, Rally, Sightseeing, Winner's Path, Amity Meadow) had no
other way in, so in practice they were Mystery Gift courses. No script command
unlocks a course.

## 7. The course table

`sPokewalkerCourses` is 27 entries of 192 (0xC0) bytes, written as raw `.byte` lines
in `asm/pokewalker_data.s` from line 707 to 1035. It hasn't been converted to C or
JSON yet. Two quirks: the label `gPokewalkerCourseRouteImageIds` (line 710) points
**into** entry 0, at its `routeImageId`. The code reads that column through it
(`pokewalker_upload.c:187`-`192`). Also, line 708 holds only course 0's watts.

Layout (`pokewalker_app.h:24`-`50`), byte offsets within one entry:

| Offset | Field | Notes |
|---:|---|---|
| 0 | `u32 wattsRequired` | 0 for the starting and special courses |
| 4 | `u32 routeImageId` | 1-8. The Pokéwalker gets this minus 1, and the picture is `gPokewalkerRouteImages[id]` (`asm/pokewalker_data.s:4451`, entry 0 unused) |
| 8 + 20·i | `mons[i]`, i = 0-5 | pairs (0,1), (2,3), (4,5); one of each pair is used |
| +0 | `u16 species` | |
| +2 | `u16 level` | |
| +4 | `u16 heldItem` | the caught Pokémon holds it |
| +6 | `u8 form` | |
| +7 | `u8 gender` | 1 = female, anything else male (`pokewalker_stroll.c:234`) |
| +8 | `u16 moves[4]` | the caught Pokémon knows exactly these |
| +16 | `u16 steps` | 75% of it with an advantage type |
| +18 | `u16 chance` | commented "percent" |
| 128 + 6·j | `items[j]`, j = 0-9 | `u16 item`, `u16 steps`, `u16 chance` |
| 188 | `u8 advantageTypes[3]` | `TYPE_*` ids (`include/constants/pokemon.h:18`) |
| 191 | padding | 0 |

All values are little-endian. The Pokéwalker firmware decides what `steps` and
`chance` actually do. Going by the table, steps is how far you must have walked
before the entry can appear, and chance is how likely it is.

To find a byte: for course `c` and offset `o` from the table above, the byte is
number `c*192 + o` in the blob. From line 712 on, each line has 16 bytes, so byte
`n ≥ 8` is on line `712 + (n-8) // 16`, column `(n-8) % 16` (first byte = column 0).
This short script prints the whole table with names:

```python
import re, struct
def consts(path, rx):
    d = {}
    for l in open(path):
        m = re.match(r'#define\s+(' + rx + r'\w+)\s+(\d+)\s*$', l.split('//')[0].rstrip() + '\n')
        if m: d.setdefault(int(m.group(2)), m.group(1))
    return d
sp = consts('include/constants/species.h', 'SPECIES_')
it = consts('include/constants/items.h', 'ITEM_(?!FIELD_USE_|BATTLE_USE_|DATA_|VAR_)')
lines = open('asm/pokewalker_data.s').read().split('\n')[707:1035]
b = bytearray(int(x, 16) for l in lines if l.strip().startswith('.byte') for x in l.strip()[5:].split(','))
for c in range(27):
    o = c * 192
    print(c, 'watts', struct.unpack_from('<I', b, o)[0])
    for i in range(6):
        s, lv, hi, fo, ge, *mv, st, ch = struct.unpack_from('<HHHBB4HHH', b, o + 8 + 20 * i)
        print('  ', sp.get(s, s), lv, it.get(hi, hi), 'steps', st, 'chance', ch)
    for j in range(10):
        x, st, ch = struct.unpack_from('<HHH', b, o + 128 + 6 * j)
        print('  ', it.get(x, x), 'steps', st, 'chance', ch)
```

The Pokémon, read from the table this way (level after the name; pairs separated by
"/"):

| # | Course | Watts | Pair 1 | Pair 2 | Pair 3 | Advantage types |
|---:|---|---:|---|---|---|---|
| 0 | Refreshing Field | 0 | Kangaskhan 8 / Doduo 8 | Nidoran♀ 5 / Nidoran♂ 5 | Pidgey 5 / Sentret 5 | Fire, Bug, Flying |
| 1 | Noisy Forest | 0 | Wobbuffet 15 / Bellsprout 8 | Venonat 6 / Paras 6 | Oddish 5 / Spearow 5 | Fire, Ice, Flying |
| 2 | Rugged Road | 50 | Magby 9 / Onix 9 | Machop 7 / Ponyta 7 | Hoothoot 6 / Geodude 8 | Water, Fighting, Ground |
| 3 | Beautiful Beach | 200 | Psyduck 10 / Staryu 10 | Slowpoke 8 / Poliwag 8 | Sunkern 6 / Wooper 6 | Grass, Electric, Dragon |
| 4 | Suburban Area | 500 | Elekid 11 / Magnemite 11 | Magnemite 8 / Murkrow 11 | Hoothoot 7 / Rattata 7 | Fighting, Normal, Psychic |
| 5 | Dim Cave | 1000 | Smoochum 12 / Gastly 15 | Gastly 10 / Onix 10 | Zubat 8 / Machop 8 | Water, Dark, Rock |
| 6 | Blue Lake | 2000 | Dratini 10 / Poliwag 15 | Krabby 12 / Shellder 12 | Goldeen 9 / Tentacool 9 | Grass, Electric, Dragon |
| 7 | Town Outskirts | 3000 | Abra 15 / Voltorb 15 | Koffing 13 / Grimer 13 | Rattata 16 / Furret 15 | Fighting, Ghost, Normal |
| 8 | Hoenn Field | 5000 | Skitty 30 / Linoone 30 | Illumise 25 / Volbeat 25 | Zigzagoon 17 / Wurmple 15 | Fire, Bug, Flying |
| 9 | Warm Beach | 7500 | Wailmer 31 / Azurill 20 | Horsea 20 / Carvanha 26 | Goldeen 22 / Magikarp 15 | Grass, Electric, Dragon |
| 10 | Volcano Path | 10000 | Slugma 31 / Meditite 32 | Houndour 27 / Rhyhorn 25 | Ponyta 19 / Geodude 29 | Water, Fighting, Rock |
| 11 | Treehouse | 15000 | Kecleon 30 / Castform 30 | Girafarig 28 / Stantler 28 | Gloom 14 / Weepinbell 13 | Fire, Ice, Flying |
| 12 | Scary Cave | 20000 | Marowak 30 / Tauros 30 | Golbat 33 / Natu 24 | Machop 13 / Gastly 15 | Dark, Ghost, Rock |
| 13 | Sinnoh Field | 25000 | Mime Jr. 29 / Combee 30 | Shinx 33 / Budew 30 | Bidoof 13 / Kricketot 15 | Fire, Ice, Flying |
| 14 | Icy Mountain Rd. | 30000 | Snover 31 / Snorunt 28 | Sneasel 28 / Bronzor 20 | Swinub 16 / Mareep 15 | Fire, Ice, Ground |
| 15 | Big Forest | 40000 | Tropius 35 / Bonsly 30 | Tangela 30 / Bibarel 30 | Mareep 19 / Exeggcute 17 | Fire, Ice, Flying |
| 16 | White Lake | 50000 | Chingling 22 / Misdreavus 32 | Haunter 25 / Buizel 28 | Remoraid 19 / Chinchou 17 | Grass, Electric, Dragon |
| 17 | Stormy Beach | 65000 | Finneon 26 / Shellos 30 | Magikarp 30 / Seel 27 | Psyduck 22 / Shellder 20 | Grass, Electric, Dragon |
| 18 | Resort | 80000 | Pachirisu 33 / Pikachu 30 | Jigglypuff 30 / Clefairy 31 | Marill 25 / Hoppip 25 | Fighting, Normal, Psychic |
| 19 | Quiet Cave | 100000 | Spiritomb 31 / Munchlax 33 | Chingling 26 / Feebas 30 | Noctowl 30 / Golbat 33 | Dark, Psychic, Ghost |
| 20 | Beyond the Sea | (GTS) | Staryu 18 @Water Stone / Octillery 19 @Focus Band | Horsea 15 / Corsola 16 | Remoraid 14 / Chinchou 12 | Grass, Electric, Dragon |
| 21 | Night Sky's Edge | (Jirachi) | Clefairy 8 / Jigglypuff 10 | Zubat 9 / Hoothoot 6 | Geodude 5 / Onix 5 | Water, Fighting, Ground |
| 22 | Yellow Forest | (gift) | Pikachu 15 @Shuca / Pikachu 14 @Lum | Pikachu 13 @Leppa / Pikachu 12 @Sitrus | Pikachu 10 @TinyMushroom / Pikachu 10 @Oran | Ground, Electric, Grass |
| 23 | Rally | (gift) | Chatot 15 / Sableye 15 | Pikachu 10 / Croagunk 10 | Buneary 5 / Pachirisu 5 | Ground, Psychic, Ice |
| 24 | Sightseeing | (gift) | Torchic 10 / Eevee 10 | Pelipper 15 / Poliwhirl 15 | Meowth 10 / Pikachu 8 | Water, Electric, Fighting |
| 25 | Winner's Path | (gift) | Munchlax 5 @Leftovers / Beldum 5 @Shuca | Horsea 5 @Dragon Scale / Duskull 5 @Reaper Cloth | Magikarp 5 @Wacan / Bronzor 5 @Occa | Dark, Electric, Fighting |
| 26 | Amity Meadow | (gift) | Elekid 5 @Tamato / Magby 5 @Kelpsy | Smoochum 5 @Hondew / Happiny 5 @Pomeg | Igglybuff 5 @Grepa / Cleffa 5 @Qualot | Fighting, Ground, Fire |

Each course also has 10 items. Refreshing Field's, as an example: Revive, Full Heal,
Burn Heal, Ice Heal, Chesto Berry, Awakening, Cheri Berry, Parlyz Heal, Oran Berry,
Potion. Their steps run from 2500 down to 0 and their chances from 20 up to 100. Run
the script for the rest.

## 8. What is saved

`SAVE_POKEWALKER` is chunk 39 in save block 0, 308 bytes (`src/save_arrays.c:293`;
[save-data.md](save-data.md)). Layout (`include/pokewalker.h:9`-`22`):

| Offset | Field | Meaning |
|---:|---|---|
| 0x000 | `strollState`, `unk_002` | §1: state 0/1/2 and the source box |
| 0x004 | `BoxPokemon pokemon` | the Pokémon on the Stroll (all zero when none, `pokewalkerHasBoxmon`, `src/pokewalker.c:76`) |
| 0x08C | 0x6C bytes | unused by `src/pokewalker.c` |
| 0x0F8 | `course` | course of the current Stroll (shown in the Stroll report, `pokewalker_app_modes.c:615`) |
| 0x0FA | `receivedStarfBerry` | the one-time Starf Berry was given |
| 0x0FC | `irClock[10]` | random numbers made with the new game (`src/overlay_36.c:206`-`209`), sent as part of the identity |
| 0x124 | `linkCount` | successful sends (`pokewalker_link.c:632`, `:963`); 1 after the first one triggers the "registered" message (`pokewalker_stroll.c:103`) |
| 0x128 | `steps` | the Pokéwalker's step count at the last link |
| 0x12C | `watts` | total watts collected, up to 9,999,999 |
| 0x130 | `unlockedCourses` | one bit per course |

The bit field is 32 bits and `Pokewalker_CourseIsUnlocked` returns FALSE for 32 and
up (`src/pokewalker.c:105`). Changing the table, watts or experience doesn't touch
the save layout.

## 9. How-tos

### Change a course's Pokémon

Edit the bytes of `mons[i]` (§7). Example: Refreshing Field's Pidgey (course 0,
`mons[4]`, offset 88) is line 717. Make it a Lv. 5 male Eevee with Tackle and Tail
Whip (`SPECIES_EEVEE` = 133 = 0x85, `MOVE_TACKLE` = 0x21, `MOVE_TAIL_WHIP` = 0x27):

```diff
-	.byte 0x10, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x21, 0x00, 0x1C, 0x00, 0x00, 0x00, 0x00, 0x00
+	.byte 0x85, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x21, 0x00, 0x27, 0x00, 0x00, 0x00, 0x00, 0x00
```

Steps and chance (0 and 100) are the first four bytes of line 718.

- Keep the species a real one. `PokewalkerApp_IsEventLogInvalid`
  (`pokewalker_trainer_house.c:30`) rejects HeartGold/SoulSilver records with a
  species above `NATIONAL_DEX_COUNT`, and the event log is then skipped
  (`pokewalker_app_modes.c:524`). The gift and walking Pokémon are checked the same way
  (`pokewalker_link.c:703`-`723`).
- The Pokéwalker picture is looked up per species in `gPokewalkerPictureFiles`, with
  special cases for forms (`pokewalker_ui.c:70`-`104`). A species added by a hack
  ([adding-a-species.md](adding-a-species.md)) has no picture there.
- The moves and held item are given to the caught Pokémon as they are. Nothing
  checks that it can learn the moves.

### Change a course's items

Edit `items[j]` (offset 128 + 6·j). Example: Refreshing Field's last item, a Potion
(17 = 0x11) at steps 0, chance 100, is offset 182, so line 722, columns 14-15. Make it
a Super Potion (26 = 0x1A):

```diff
-	.byte 0x32, 0x00, 0x16, 0x00, 0xF4, 0x01, 0x32, 0x00, 0x9B, 0x00, 0x2C, 0x01, 0x32, 0x00, 0x11, 0x00
+	.byte 0x32, 0x00, 0x16, 0x00, 0xF4, 0x01, 0x32, 0x00, 0x9B, 0x00, 0x2C, 0x01, 0x32, 0x00, 0x1A, 0x00
```

The item's name on the Pokéwalker is drawn from the game's item names when the
Pokémon is sent, so a renamed item shows its new name ([items.md](items.md)).

### Change watts needed, or the National Dex gate

- **Watts per course:** the first 4 bytes of each entry. Rugged Road (course 2) is
  line 735, columns 8-11 (`0x32, 0x00, 0x00, 0x00` = 50).
- **Which courses watts can unlock:** the `count = 20` / `count = 8` pairs in
  `pokewalker_ui.c:112`-`116` and `:129`-`133`. Change both pairs the same way. To
  open courses 8-19 without the National Dex, use 20 in both branches.
- **More than one course per link:** in `PokewalkerApp_UnlockNextCourse`, remove the
  `return;` after `Pokewalker_UnlockCourse` (`pokewalker_ui.c:121`). `app->unlockedCourse`
  then holds only the last one, and the "new Route" message names only that one.

### Start with more courses, or unlock one from the game

New saves get whatever `Pokewalker_Init` unlocks:

```diff
 void Pokewalker_Init(POKEWALKER *pokeWalker) {
     MI_CpuClearFast(pokeWalker, sizeof(POKEWALKER));
     Pokewalker_UnlockCourse(pokeWalker, WALKER_COURSE_REFRESHING_FIELD);
     Pokewalker_UnlockCourse(pokeWalker, WALKER_COURSE_NOISY_FOREST);
+    Pokewalker_UnlockCourse(pokeWalker, WALKER_COURSE_YELLOW_FOREST);
 }
```

That only affects saves created afterwards. To unlock a course during play, copy the
Jirachi hook in `src/update_dex_received.c:21`. For example, open Yellow Forest
whenever a Pikachu is received as a gift, trade or egg:

```diff
         if (species == SPECIES_JIRACHI) {
             POKEWALKER *pokeWalker = Save_Pokewalker_Get(saveData);
             Pokewalker_UnlockCourse(pokeWalker, WALKER_COURSE_NIGHT_SKY_S_EDGE);
         }
+        if (species == SPECIES_PIKACHU) {
+            Pokewalker_UnlockCourse(Save_Pokewalker_Get(saveData), WALKER_COURSE_YELLOW_FOREST);
+        }
```

To tie a course to a story event, you would add a script command that calls
`Pokewalker_UnlockCourse`. None exists. [script-commands.md](script-commands.md)
explains how commands are added.

### Change experience or friendship on return

All in `src/application/pokewalker/pokewalker_stroll.c`:

| To | Change |
|---|---|
| double the experience | `app->strollSteps * 2` in the `PokewalkerApp_AddStrollExp` call (line 148) |
| allow more than one level | remove the cap at lines 182-185, and limit `totalExp` to `GetMonExpBySpeciesAndLevel(species, MAX_LEVEL)` so it can't go past level 100. Levels are recalculated, but moves aren't learned and nothing evolves. |
| friendship for shorter Strolls | the `5000` at line 213 |
| more friendship per Stroll | the `friendship++` at line 216 (keep the `FRIENDSHIP_MAX` check) |
| no level-up friendship | remove `MonApplyFriendshipMod` at line 194 |
| allow Quirky (nature 24) | `MTRandom() % 24` → `% NATURE_NUM` at lines 155, 300, 316. The non-shiny branch asserts `nature & 1 == ability` and gets `nature & 1` as the ability, so that holds. |

### Adding a 28th course (what it touches)

This hasn't been tried. The places that assume 27 courses:

- `WALKER_COURSE_MAX` (`include/constants/pokewalker_courses.h`) and a new 192-byte
  entry after line 1035 of `asm/pokewalker_data.s`.
- `PokewalkerApp_ListUnlockedCourses` loops to a literal 27 (`pokewalker_link.c:223`).
  `courseList` holds 30 (`pokewalker_app.h:231`).
- `BufferPokewalkerCourseName` asserts below 27 (`src/message_format.c:617`).
- The names are `msg_0274_00091 + course` and the descriptions `msg_0274_00119 + course`.
  Course 27's name would be message 118, which is the "--------" shown for an empty
  list slot (`pokewalker_link.c:195`). Its description would be 146. So the messages
  have to move.
- `PokewalkerApp_IsEventLogInvalid` rejects records whose `course` is 8 or more
  (`pokewalker_trainer_house.c:48`). That only makes sense if the record holds the
  route image id (0-7), not the course id. So keep `routeImageId` between 1 and 8.
- How the Pokéwalker treats a course it was never shipped with is unknown. It only
  receives the name bitmap, the image id and picture, and the Pokémon and item lists.

## 10. What the ROM can't change

The Pokéwalker runs its own firmware, and this repository has none of it. Everything
below happens on the device, and the game only reads the results:

- how steps are counted, and how many watts they earn (`irStatus.watts` arrives as a
  number);
- spending watts on the Poké Radar and dowsing; the battles and catches on the device;
  when a course Pokémon or item actually turns up (the game only sends `steps` and
  `chance`);
- meeting other Pokéwalkers, the events in the event log, and the "happy" and nap
  entries (`include/application/pokewalker/pokewalker_event_log.h:16`-`35`);
- gift Pokémon and gift items stored on the device (the game copies whatever is in
  the blocks, §5), and when `giveStarfBerry` is set;
- how the screens are laid out and animated.

Some things look like device features but come from the ROM, as images built when
you link:

| On the Pokéwalker | Comes from | Sent |
|---|---|---|
| course name, Pokémon nickname, species and item names | text printed and converted to 2bpp (`pokewalker_upload.c:520`, `:584`) | every Stroll |
| Pokémon pictures and icons | NARCs `a/2/5/6`, `a/2/4/8` (prebuilt binaries, copied as-is) | every Stroll |
| course picture | `gPokewalkerRouteImages` (8 pictures, 0xC0 bytes each) | every Stroll |
| digits, arrows, symbols, menu graphics, the player's name | the upload image, `PokewalkerApp_BuildUploadImage` (`pokewalker_upload.c:203`) | only on first registration (0x32) |

Changes to the upload image only reach a Pokéwalker when it is registered again, which
means erasing it first. The 2bpp format is described in `PokewalkerApp_ConvertTo2bpp`:
columns of 8 pixels, two bytes each, bit plane 1 then bit plane 0.

## Not verified

None of this was built or tried on a Pokéwalker or an emulator. Everything is read
from the code.

- The diffs in §9 (table bytes, `Pokewalker_Init`, the Pikachu hook, the experience
  and friendship changes) were not built. Byte-table edits keep the file the same
  size, but they change the ROM, so the matching checksum fails by design.
- What the Pokéwalker does with `steps`, `chance` and the advantage types beyond the
  75% step reduction.
- That `irStatus.watts` is the watts earned since the last link (inferred from
  message 45).
- When the Pokéwalker sets `hasWalkerMon`, `giveStarfBerry`, and the gift blocks.
- The meaning of the 0x6C unused bytes in the save, the identity fields `unk_*`, the
  0xB0-0xBE / 0xE0 / 0xF0 / 0xFE commands, and the second item list
  (`irStatus.unk_48`).
- That the event record's `course` field holds the route image id (inferred from the
  `>= 8` check).
- Which map section the `8` in `MonApplyFriendshipMod(mon, 0, 8)` refers to.
- Which IR request each of link actions 1, 2 and 4 sends (§1).
- Adding a 28th course: only the places in the code were listed.
- The species table in §7 was decoded by script from the raw bytes and checked by
  hand only for course 0 (lines 712-723) and course 2's watts (line 735).
