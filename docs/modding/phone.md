<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Pokégear phone calls and rematches

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The phone has 75 contacts: Mom, the professors, Bill, Kurt, the Day-Care couple,
Buena, Baoba, the rival, 16 gym leaders and 45 route trainers. A contact is one
row of the **phone book**, one **text file**, and, for trainers, 16 rows that
decide what they say when you call them or they call you. A call can have a side
effect: setting a flag, promising a gift, or making the trainer want a
**rematch**. The battle itself happens when you walk up to the trainer.

| pokeemerald (Match Call) | here |
|---|---|
| `gMatchCallTrainers` in `src/match_call.c` | phone book: `files/tel/pmtel_book.json` |
| `data/text/match_call.inc` | one text file per contact, `files/msgdata/msg/msg_06xx.json` |
| `sMatchCallTextTables` / random topics | `sGenericPhoneCallHeaders` (`src/application/pokegear/phone/phone_generic_headers.c`) |
| `gRematchTable` (`src/battle_setup.c`) | `sTrainerRematchSets` (`src/trainer_rematch.c`) |
| rematch from VS Seeker / step counter | a call sets a "wants a rematch" bit; you then talk to the trainer |

## Where things are

| What | File |
|---|---|
| contact ids (`PHONE_CONTACT_*`, `NUM_PHONE_CONTACTS`) | `include/constants/phone_contacts.h` |
| the phone book (one entry per contact) | `files/tel/pmtel_book.json` → `tel/pmtel_book.dat` |
| each contact's text file | `sPhoneMessageGmm`, `src/phonebook_dat.c:60` |
| call scripts: which message, what side effect | `gPhoneCallScriptDef`, `src/application/pokegear/phone/phone_script_defs.c:95`; ids in `include/constants/phone_scripts.h` |
| trainers' call rules (16 per contact) | `sGenericPhoneCallHeaders`, `phone_generic_headers.c:40` |
| greetings ("Hello, this is…") | `sGreetingMsgIDs`, `phone_generic_headers.c:29`; text in `msg_0640.json` |
| special contacts (Mom, Elm, Kurt, Bill, Buena...) | `src/application/pokegear/phone/scripts/phone_scripts_*.c` |
| when the phone rings | `src/field/gear_phone_calls.c`, `src/gear_phone_ring_manager.c` |
| rematch teams | `sTrainerRematchSets`, `src/trainer_rematch.c:12` ([trainers.md](trainers.md#rematches)) |
| asking for your number, rematch battles, gifts on the route | the shared trainer script, `files/fielddata/script/scr_seq/scr_seq_0953.s` (from line 1488) |
| what is saved | `PhoneCallPersistentState` and `phoneContacts` in `include/save_pokegear.h` |

## 1. The phone book

`files/tel/pmtel_book.json` has one entry per contact, **in contact-id order**. The
game reads entry *n* as contact *n*, so the position matters and `id` only labels
it. Joey's:

```json
{"id": "PHONE_CONTACT_JOEY", "type": 0, "unk2": 0, "trainerClass": "TRAINERCLASS_YOUNGSTER",
 "trainerId": "TRAINER_YOUNGSTER_JOEY", "mapId": "MAP_ROUTE_30", "gift": "ITEM_HP_UP",
 "phoneScriptIfLocal": "PHONE_SCRIPT_029", "unkC": 0, "rematchWeekday": "RTC_WEEK_MONDAY",
 "rematchTimeOfDay": "TIMEOFDAY_WILD_DAY", "unkF": 1, "sortParam": [75, 40, 47, 0]}
```

The JSON keeps two old names. `unkC` is `greetingMsgSet` in C, and `unkF` is
`randomCallGroup` (`PhoneBookEntry`, `include/gear_phone.h`).

| Field | Meaning |
|---|---|
| `type` | which code handles calls ([§3](#3-call-types)). 0 for every route trainer, 12 for gym leaders. |
| `unk2` | unused (0 everywhere) |
| `trainerClass` | the class shown under the name. Non-trainers use the `TRAINERCLASS_PHONE_*` classes, whose titles are in `msg_0271`. |
| `trainerId` | the trainer this contact belongs to. The shared trainer script finds the contact by this field (`LoadPhoneBookEntryI`). Generic calls name a random Pokémon from this trainer's party. |
| `mapId` | where the contact lives. Calls name this place, the Pokégear map marks it, and you get the "you're nearby" line if you call while standing on this exact map. Contacts never ring you on their own map. |
| `gift` | an item the trainer gives **after every rematch win** (Joey: HP Up). `ITEM_CHERI_BERRY` means a random one of the 10 berries from Cheri to Lum. `ITEM_NONE` for no gift. |
| `phoneScriptIfLocal` | the script used when you call while on `mapId` (route trainers only) |
| `unkC` (`greetingMsgSet`) | a row of `sGreetingMsgIDs` (0-7), or 255 for no greeting line |
| `rematchWeekday`, `rematchTimeOfDay` | the day (`RTC_WEEK_*`) and time (`TIMEOFDAY_WILD_MORN` / `_DAY` / `_NITE`) on which calling them can set up a rematch. `RTC_WEEK_MAX` / `TIMEOFDAY_WILD_MAX` for never. |
| `unkF` (`randomCallGroup`) | which group the contact rings in: 0, 1 or 2 ([§5](#5-when-the-phone-rings)) |
| `sortParam` | the contact's rank in the three sort orders the list menu offers: by title, alphabetical, by location. The fourth value is unused. |

Times of day here are the three wild-encounter periods: morning 4:00-9:59, day
10:00-19:59, night 20:00-3:59 ([day-night-and-rtc.md](day-night-and-rtc.md)).

## 2. The text file

Each contact has its own text file, listed in `sPhoneMessageGmm`
(`src/phonebook_dat.c:60`). For route trainers the first six messages have fixed
jobs, because the shared trainer script uses them by number. Joey (`msg_0675.json`):

| # | Used by | Joey |
|---:|---|---|
| 0 | the contact list, ring screen | "Joey" |
| 1 | after your first win: asks for your number (needs `{YESNO 0}`) | "Hey, can I get your number? I'll ring you up to battle." |
| 2 | you said yes | "I'll ring you whenever I get the urge to battle!" |
| 3 | you said no | "Oh, all right... But I won't lose to you again!" |
| 4 | talking to him later, if you said no: asks again | "Can I get your phone number? I don't want to lose against you!..." |
| 5 | handing over a gift (after a rematch, or one promised on the phone) | "...Here, take this." |
| 6+ | the calls, picked by the call scripts | |

Placeholders that calls fill in (`PhoneCall_InitMsgDataAndBufferNames`,
`phone_call.c`; copy them from an existing message):

| In the text | Is |
|---|---|
| `{STRVAR_1 3, 0, 0}` | the player's name |
| `{STRVAR_1 3, 1, 0}` | the contact's name |
| `{STRVAR_1 4, 2, 0}` | where the player is |
| `{STRVAR_1 4, 3, 0}` | where the contact is (`mapId`) |
| `{STRVAR_1 0, 10, 0}` | a random Pokémon from the contact's team (calls with handler 1 only) |
| `{STRVAR_1 0, 11, 0}` | a random wild Pokémon from the contact's route at this time of day; for Fishermen, a Good Rod Pokémon (handler 1 only) |

## 3. Call types

When a call starts, the contact's `type` picks a function that chooses a **call
script** (`PhoneCall_GetCallScriptId`, `phone_call.c:149`):

| `type` | `PHONECALLTYPE_*` | Contacts | Chooser |
|---:|---|---|---|
| 0 | `GENERIC` | the 45 route trainers | the 16 rows in `sGenericPhoneCallHeaders` ([§4](#4-what-route-trainers-say)) |
| 1 | `MOM` | Mom | story flags; savings menu |
| 2, 3 | `PROF_ELM`, `PROF_OAK` | the professors | story flags, badges, Pokédex |
| 4 | `KURT` | Kurt | Apricorns he holds |
| 5 | `BIKE_SHOP` | Bike Shop | |
| 6 | `KENJI` | Black Belt Kenji | his training trip |
| 7 | `BILL` | Bill | PC boxes |
| 8, 9 | `DAYCAREMAN`, `DAYCARELADY` | Day-Care | what they're raising, eggs |
| 10 | `BUENA` | Buena | her radio show's hours |
| 11 | `ETHAN_LYRA` | Ethan or Lyra | where the player is |
| 12 | `GYMLEADER` | the 16 leaders | rematch dates ([§6](#gym-leaders)) |
| 13 | `BAOBA` | Baoba | Safari Zone progress |
| 14 | `IRWIN` | Juggler Irwin | story flags (`FLAG_UNK_998`-`9A5`, [unknown-flags-vars.md](unknown-flags-vars.md)) |

A call script is a row of `gPhoneCallScriptDef` (`phone_script_defs.c:95`),
`PHONE_SCRIPT_001`-`455`:

```c
    // PHONE_SCRIPT_033
    {
     .msgIds = { msg_0675_00010, msg_0675_00010 },   // what to say: if the player is Ethan, if Lyra
     .scriptType = PHONESCRIPTTYPE_REMATCH,           // side effect
     .param0 = 1,
     .param1 = 0,
     },
```

| `scriptType` (side effect) | Does (`PhoneCall_ApplyGenericNPCcallSideEffect`, `phone_call.c:255`) |
|---|---|
| `PHONESCRIPTTYPE_NONE` | nothing: just talk |
| `PHONESCRIPTTYPE_FLAG` | set (`param0` = 1) or clear (0) flag `param1` |
| `PHONESCRIPTTYPE_REMATCH` | the contact now **wants a rematch** |
| `PHONESCRIPTTYPE_ITEM` | the contact now **has a gift** for you: item `param1`. `ITEM_CHERI_BERRY` gives a random berry (Cheri to Lum), `ITEM_POKE_BALL` a random one of Ultra, Great and Poké Ball. |
| `PHONESCRIPTTYPE_WORD` | put one of `param0` messages, starting at `param1`, in placeholder 4 |

The call is then run by one of 16 **handlers** (`sPhoneCallHandlers`,
`phone_call.c:16`). The special contacts have their own handlers. Route trainers use
the first three:

| Handler | Shows |
|---:|---|
| 0 `GearPhoneCall_Simple` | greeting, then the script's message |
| 1 `GearPhoneCall_Generic` | the same, after filling in placeholders 10 and 11 (team and wild Pokémon) |
| 2 `GearPhoneCall_Generic2` | greeting, then one of 11 messages starting at the script's message |

**Greetings.** Unless `greetingMsgSet` is 255, a call starts with a line from
`msg_0640.json`: `sGreetingMsgIDs[set]` has 12 entries, for whether you called or
were called × morning/day/night × Ethan/Lyra (`PhoneCall_PrintGreeting`,
`phone_call.c:437`). There are 8 sets; Joey uses 0, Ralph 4.

**Where calls work.** A map's `allow_outgoing_calls` and `allow_incoming_calls`
(`map.json`, [maps-and-warps.md](maps-and-warps.md)) are checked before any call
(`PhoneCall_InitContext`, `phone_call.c:116`). Where they're off, you get the
"out of service" tones.

## 4. What route trainers say

Each contact has 16 rows in `sGenericPhoneCallHeaders` (`phone_generic_headers.c:40`),
at `contact id × 16`. The first 8 are used when **you call them**, the last 8 when
**they call you** (`PhoneCall_GetScriptId_Generic`, `phone_scripts_generic.c:24`).
If you call while standing on their `mapId`, `phoneScriptIfLocal` is used instead.
Non-trainer contacts have rows too, all empty.

The rows are tried in order. The **first row whose condition passes** gives the call
script and handler. If none passes, the **last real row is used anyway**, so put the
everyday chit-chat last (`PhoneScriptGeneric_GetScriptIdInternal`, line 38). A row
of type `PHONECALLGENERIC_NIL` or `_NONE` ends the list (`PHONE_GENERIC_TERM`,
`PHONE_GENERIC_NULL`).

```c
    // PHONE_CONTACT_JOEY/1                    <- you call Joey
    { .type = PHONECALLGENERIC_FIGHTPOSTROCKETSNOTBUGCONTEST, .chance = 100, .scriptType = 0, .scriptID = PHONE_SCRIPT_034 },  // "What's keeping you?"
    { .type = PHONECALLGENERIC_POSTROCKETWEEKTIME,            .chance = 100, .scriptType = 0, .scriptID = PHONE_SCRIPT_033 },  // "Let's battle!" (REMATCH)
    { .type = PHONECALLGENERIC_RAND1,                         .chance = 100, .scriptType = 1, .scriptID = PHONE_SCRIPT_035 },  // chit-chat
    // PHONE_CONTACT_JOEY/2                    <- Joey calls you
    { .type = PHONECALLGENERIC_FIGHTPOSTROCKETS, .chance = 60, .scriptType = 0, .scriptID = PHONE_SCRIPT_033 },  // 60%: "Let's battle!"
    { .type = PHONECALLGENERIC_RAND1,            .chance = 40, .scriptType = 1, .scriptID = PHONE_SCRIPT_030 },
    { .type = PHONECALLGENERIC_RAND1,            .chance = 40, .scriptType = 1, .scriptID = PHONE_SCRIPT_031 },
    { .type = PHONECALLGENERIC_RAND1,            .chance = 100, .scriptType = 1, .scriptID = PHONE_SCRIPT_032 },
```

(Shortened; the file has one field per line.) `scriptType` in a row is the
**handler** (0, 1 or 2 above), not the side effect.

| `type` | Passes when | Used for |
|---|---|---|
| `RAND1` (and any type not below) | the chance roll | chit-chat |
| `FIGHTPOSTROCKETS` | nothing is pending (no rematch waiting, no gift waiting) and the roll; **and** if the script is a rematch (with handler 0), only after `FLAG_BEAT_RADIO_TOWER_ROCKETS` | an incoming call that asks for a battle or offers a gift |
| `POSTROCKETWEEKTIME` | after the Radio Tower, today is the contact's `rematchWeekday` and it is their `rematchTimeOfDay`; and the roll | calling them on their day |
| `FIGHTPOSTROCKETSNOTBUGCONTEST` | after the Radio Tower, a rematch **is** waiting, the contact isn't at National Park during the Bug Contest; and the roll | "Where are you? I'm waiting!" |
| `GIFTNOTBUGCONTEST` | a gift is waiting, same Bug Contest rule; and the roll | "Come get your present!" |
| `BUGCONTESTDAYS` | Tuesday, Thursday or Saturday; and the roll | Bug Contest talk |
| `DURINGROCKETS` | during the Radio Tower takeover; and the roll | |

The roll passes when a random number from 0 to 99 is **at most** `chance`
(`rollPercentChance`, line 87). So 100 always passes, and 40 is really 41%.

## 5. When the phone rings

Every frame the player stands still on a map that allows incoming calls, the game
tries to start a call (`GearPhoneRingManager_TryStartCall`, `gear_phone_calls.c:108`,
from `field_control.c:319`). It only tries once **10 minutes** have passed since the
last attempt, counted on the DS clock (`callIntervalMinutes`,
`gear_phone_ring_manager.c:104`; [day-night-and-rtc.md](day-night-and-rtc.md)). Then:

1. **Call triggers first.** These are one-off calls that game events queue up
   ([below](#call-triggers)). If any is queued for a contact who isn't on the
   player's map, one is picked at random and the phone rings.
2. **Otherwise a random call**, with a 50% chance (`randomCallChance`; the comparison
   makes it 51%). If no call happens, the 10 minutes start again.

**Who can make a random call** (`GearPhoneRingManager_TryRandomCall`, line 149):

- The game picks a group: 0 (50%), 1 (30%) or 2 (20%). Only registered contacts
  whose `randomCallGroup` is that group can ring. The route trainers are split 11 /
  13 / 21 over groups 0 / 1 / 2, and all 16 gym leaders are in group 2, so a group-2
  trainer rings less often than a group-0 one.
- Only these call types ever ring at random: route trainers, gym leaders, Ethan/Lyra,
  Buena and Irwin. Mom, the professors, Bill and the rest only call through triggers
  or story scripts.
- Not if the contact lives on the player's current map.
- Not if they called recently. The game remembers the last 4 callers of group 0 and
  the last 2 of groups 1 and 2 (`phoneRecentCallers`, `src/save_misc.c:109`). The
  memory is cleared when every candidate in the group is in it.
- Not Buena during her radio show's password hour or the Rocket takeover; not a
  National Park contact during the Bug Contest.

The phone rings until you answer. If you don't open the Pokégear within about 30
seconds, it stops (`GearPhoneRingManager_HandleTimeAdvance`, line 205).

### Call triggers

A trigger is a queued call that waits until the next attempt. Scripts set one with
`setphonecalltrigger(CALL_TRIGGER_X, ring_soon)` and clear one with
`unsetphonecalltrigger`. With `ring_soon` TRUE the 10 minutes are cut to 1. They are
saved as bits in `callTriggerFlags`.

| `CALL_TRIGGER_*` (`include/constants/phone_constants.h`) | Contact | Set by |
|---|---|---|
| `ELM_EGG_HATCHED` | Elm | the Togepi egg hatching (`FieldSystem_TryTriggerElmEggHatchedCall`, `src/gear_phone_ring_manager.c`) |
| `ELM_POKERUS` | Elm | a standard script, when the party has Pokérus (`scr_seq_0003.s:245`) |
| `BIKE_SHOP_STEPS` | Bike Shop | 1,024 steps on the bike (`FieldSystem_UpdateBikeShop`, `src/field/field_control.c`) |
| `BILL_PC_FULL` | Bill | all boxes full (`FieldSystem_TryTriggerBillPCFullCall`) |
| `OAK_DEX_PROGRESS` | Oak | every 50 Pokémon owned (`FieldSystem_TryTriggerOakDexProgressCall`) |
| `DAYCARE_HAS_EGG` | Day-Care Man | an egg appearing (`FieldSystem_TryTriggerDaycareEggCall`) |
| `BAOBA_NEW_POKEMON` | Baoba | `src/safari_zone_encounters.c:173` |
| `BAOBA_*` (the other 5) | Baoba | Safari Zone progress over time (`GearPhoneRingManager_CheckSafariCalls`) |
| `MOM_BOUGHT_SOMETHING` | Mom | Mom spending your savings after a battle (`src/battle/battle_setup.c:416`) |

Each trigger has a fixed call script and a "force pick-up" setting in
`sPhoneCallTriggers` (`gear_phone_calls.c:33`). A forced call doesn't wait for you:
the field runs standard script 2047, which rings twice and opens the phone.

### Calls from map scripts

`phonecall(PHONE_CONTACT_X, 2, n)` makes a contact call you right now (the
`PhoneCall` macro and `std_phone_call`; [script-commands.md](script-commands.md)).
The second argument 2 means "from a map script", and `n` picks one of that contact's
story calls. Only Elm (`sPhoneCallData_ProfElm_MapScripts`), Oak, Mom and Baoba read
it. A route trainer ignores both numbers and gives a normal incoming call. A story
call from a trainer needs a new branch in `PhoneCall_GetScriptId_Generic`.

## 6. Rematches

### Route trainers

1. **The number.** After you first beat a trainer who has a phone-book entry, they
   ask for your number (message 1). Yes registers them (`registergearnumber`). No
   means they ask again (message 4) whenever you talk to them. This is all in the
   shared trainer script, so any trainer placed with `std_trainer(TRAINER_X)` does it
   once they have a phone-book entry (`scr_seq_0953.s`, `_0D9F`).
2. **The call.** A call whose script has the `REMATCH` side effect sets the contact's
   "wants a rematch" bit. Route trainers get there two ways: by calling you
   (`FIGHTPOSTROCKETS`, Joey 60%), or by you calling them on their
   `rematchWeekday` at their `rematchTimeOfDay` (`POSTROCKETWEEKTIME`). Both need
   the Radio Tower cleared.
3. **The map.** The Pokégear map marks routes where a registered trainer wants a
   rematch or holds a gift (`PokegearMap_MapHasPhoneRematchOrGift`,
   `pokegear_map_view.c:781`).
4. **The battle.** Talk to the trainer. `getphonebookrematch` returns the trainer id
   to fight, or 0 if no rematch is waiting (`PhoneBookTrainerGetRematchInfo`,
   `src/phone_rematch.c:9`). The intro line is the trainer's battle text of type
   `TRMSG_PHONE_REMATCH_INTRO` (17). After a win, the bit is cleared and the
   phone-book `gift`, if any, is handed over with message 5 (`_0C7F`).
5. **Gifts promised on the phone** (`ITEM` side effect) are saved per contact and
   handed over the next time you talk to them, before any rematch check (`_0C9C`).

**Which team.** The trainer's row in `sTrainerRematchSets`
(`src/trainer_rematch.c:12`) lists the teams. Column 0 is the trainer on the map.
Columns 1-5 are the rematches, and column 1 is normally the original trainer again.
The game takes the first column whose trainer you haven't beaten. Before using
column *n* it checks flag `FLAG_UNK_97B + n`, and if that flag isn't set yet it
steps back **one** column (`GetIndexOfFirstUnbeatenRematch`, line 99):

| Column | Unlocked by | Set in |
|---:|---|---|
| 1 | nothing (no check) | |
| 2 | `FLAG_UNK_97D` | Radio Tower, after Archer |
| 3 | `FLAG_UNK_97E` | Hall of Fame |
| 4 | `FLAG_UNK_97F` | beating Blue |
| 5 | `FLAG_UNK_980` | nothing sets it |

So Joey's rematches are his first team until the Radio Tower, then `JOEY_2`, and so
on. Once every column is beaten, the last one repeats. To change the teams, edit
those trainers in `trainers.json`. To add tiers, see
[trainers.md](trainers.md#rematches).

**Kenji** is a route trainer with his own call type: he leaves on a training trip
for a few days, and his rematch only works during the day (`src/phone_rematch.c:16`,
`phone_scripts_blackbelt_kenji.c`).

### Gym leaders

Leaders don't call to ask for a fight. You call them: with all 16 badges, on their
`rematchWeekday` during their `rematchTimeOfDay`, the leader offers a battle, and
yes sets the rematch bit (`GearPhoneCall_GymLeader_Outgoing`,
`phone_scripts_gym_leader.c`). They then wait in Saffron's Fighting Dojo
([gyms.md](gyms.md)). Their text files share one layout (message 2 the
greeting, 5 the offer, 9 "I'm waiting").

`isDojoFull` (line 126) looks meant to stop a sixth leader from agreeing while five
are waiting, but its loop only checks Falkner, so the limit never applies. To enable
it, loop over `NELEMS(sGymLeaderContacts)` instead of 1.

## 7. Example: give a route trainer a phone number

This gives Bug Catcher Don (Route 30) a number, calls, and a rematch. It was built;
see [Not verified](#not-verified).

**1. The contact id.** `include/constants/phone_contacts.h`:

```c
#define PHONE_CONTACT_ERNEST      74
#define PHONE_CONTACT_DON         75
#define NUM_PHONE_CONTACTS        76
```

This grows the save ([§9](#9-saves)).

**2. The text file.** A new message bank: `files/msgdata/msg/msg_0829.json` (the next
free number). Add `NARC_msg_msg_0829_bin` as a new last line of
`files/msgdata/NARC_msg.txt`, and `msg_0829, // PHONE_CONTACT_DON` at the end of
`sPhoneMessageGmm` in `src/phonebook_dat.c`. The `key` can be any number from 1 to
65535. Messages 0-5 as in [§2](#2-the-text-file) (copy Joey's 1-5 to start), then
the calls:

```json
{
  "key": 12345,
  "messages": [
    { "id": "msg_0829_00000", "en_US": "Don" },
    ...
    { "id": "msg_0829_00006", "en_US": ["Huh? You’re right here on Route 30!\n", "Come talk to me instead!"] },
    { "id": "msg_0829_00007", "en_US": ["My {STRVAR_1 0, 10, 0} is getting\n", "really strong!\r", "I bet it could beat a wild\n", "{STRVAR_1 0, 11, 0} easily!"] },
    { "id": "msg_0829_00008", "en_US": ["I’ve been training my Bug Pokémon!\n", "Let’s battle!\r", "I’ll be waiting on {STRVAR_1 4, 3, 0}!"] },
    { "id": "msg_0829_00009", "en_US": ["Hurry up! I’m waiting on\n", "{STRVAR_1 4, 3, 0}!"] }
  ]
}
```

**3. Call scripts.** `include/constants/phone_scripts.h`: add `PHONE_SCRIPT_456`-`459`
and make `NUM_PHONE_SCRIPTS` 460. In `phone_script_defs.c`, add
`#include "msgdata/msg/msg_0829.h"` with the others and four entries at the end of
`gPhoneCallScriptDef`:

| Script | Message | Side effect |
|---|---|---|
| `PHONE_SCRIPT_456` | `msg_0829_00006` (nearby) | `PHONESCRIPTTYPE_NONE` |
| `PHONE_SCRIPT_457` | `msg_0829_00007` (chit-chat) | `PHONESCRIPTTYPE_NONE` |
| `PHONE_SCRIPT_458` | `msg_0829_00008` (let's battle) | `PHONESCRIPTTYPE_REMATCH`, `param0 = 1` |
| `PHONE_SCRIPT_459` | `msg_0829_00009` (waiting) | `PHONESCRIPTTYPE_NONE` |

**4. Call rules.** 16 rows at the end of `sGenericPhoneCallHeaders` (they must be the
75th block of 16):

```c
    // PHONE_CONTACT_DON/1
    { .type = PHONECALLGENERIC_FIGHTPOSTROCKETSNOTBUGCONTEST, .chance = 100, .scriptType = 0, .scriptID = PHONE_SCRIPT_459 },
    { .type = PHONECALLGENERIC_POSTROCKETWEEKTIME,            .chance = 100, .scriptType = 0, .scriptID = PHONE_SCRIPT_458 },
    { .type = PHONECALLGENERIC_RAND1,                         .chance = 100, .scriptType = 1, .scriptID = PHONE_SCRIPT_457 },
    PHONE_GENERIC_NULL, PHONE_GENERIC_NULL, PHONE_GENERIC_NULL, PHONE_GENERIC_NULL, PHONE_GENERIC_NULL,

    // PHONE_CONTACT_DON/2
    { .type = PHONECALLGENERIC_FIGHTPOSTROCKETS, .chance = 50,  .scriptType = 0, .scriptID = PHONE_SCRIPT_458 },
    { .type = PHONECALLGENERIC_RAND1,            .chance = 100, .scriptType = 1, .scriptID = PHONE_SCRIPT_457 },
    PHONE_GENERIC_NULL, PHONE_GENERIC_NULL, PHONE_GENERIC_NULL, PHONE_GENERIC_NULL, PHONE_GENERIC_NULL, PHONE_GENERIC_NULL,
```

**5. The phone book.** Append to `files/tel/pmtel_book.json` (it must be the 76th
entry):

```json
{"id": "PHONE_CONTACT_DON", "type": 0, "unk2": 0, "trainerClass": "TRAINERCLASS_BUG_CATCHER",
 "trainerId": "TRAINER_BUG_CATCHER_DON", "mapId": "MAP_ROUTE_30", "gift": "ITEM_NONE",
 "phoneScriptIfLocal": "PHONE_SCRIPT_456", "unkC": 0, "rematchWeekday": "RTC_WEEK_TUESDAY",
 "rematchTimeOfDay": "TIMEOFDAY_WILD_DAY", "unkF": 1, "sortParam": [76, 76, 76, 0]}
```

`sortParam` 76 puts him last in every sort order. To place him properly, give him a
rank and add 1 to every entry ranked at or after it.

**6. The rematch team.** A row at the end of `sTrainerRematchSets`. This one
rematches with his original team. Add `TRAINER_BUG_CATCHER_DON_2` etc. to
`trainers.json` and put them in columns 2-5 for stronger teams:

```c
    { TRAINER_BUG_CATCHER_DON,           TRAINER_BUG_CATCHER_DON,           TRAINER_NONE,                        TRAINER_NONE,                       TRAINER_NONE,                       TRAINER_NONE },
```

**7. The rematch intro line.** Add a `TRMSG_PHONE_REMATCH_INTRO` line to Don's
`messages` in `files/poketool/trainer/trainers.json`, then regenerate the battle-text
tables. Without it he greets you with an empty text box.

```json
{"type": "TRMSG_PHONE_REMATCH_INTRO", "message": "You called, so here I am!\\nMy bugs are ready this time!\\r"}
```

```sh
python3 tools/trmsg/trmsg.py build
```

A stronger rematch team (`TRAINER_BUG_CATCHER_DON_2`) needs its own `TRMSG_LOSE`
line too. [trainer-text.md](trainer-text.md) covers every message type and how the
tables work.

**8. The map.** Nothing: Don is already placed with
`std_trainer(TRAINER_BUG_CATCHER_DON)`, which asks for the number after a win. A
trainer placed with a custom script needs the steps of the shared script
(`scr_seq_0953.s` from line 1488) in their own script: `checkregisteredphonenumber`,
`registergearnumber`, `getphonebookrematch`, `clearphonerematchseeking`.

## 8. Quick changes

| To | Change |
|---|---|
| change a trainer's rematch day or time | `rematchWeekday`, `rematchTimeOfDay` in `pmtel_book.json` |
| make calls more or less frequent | `callIntervalMinutes` (10) and `randomCallChance` (50) in `GearPhoneRingManager_New` (`gear_phone_ring_manager.c:100`); `randomCallChance` is also reset in `gearRingingManagerReset` |
| allow rematches before the Radio Tower | remove the `FLAG_BEAT_RADIO_TOWER_ROCKETS` checks in `phone_scripts_generic.c` (lines 108, 117, 129) |
| make a trainer ask for a rematch more often | raise `.chance` on their `FIGHTPOSTROCKETS` row |
| change the item after each rematch | `gift` in `pmtel_book.json` |
| change what a call says | the contact's text file; the call script picks the message |
| change rematch teams | the `_2`-`_4` trainers in `trainers.json` ([trainers.md](trainers.md#rematches)) |

## 9. Saves

Saved per contact (`include/save_pokegear.h`): whether the number is registered
(`phoneContacts`, one byte each), and the rematch bit and pending gift
(`PhoneRematch`, 4 bytes each). Both arrays are `NUM_PHONE_CONTACTS` long, so a new
contact grows `SAVE_POKEGEAR` by 5 bytes, and every chunk after it moves. Old saves
won't load. Block 0 has room ([save-data.md](save-data.md)). Changing text, call
rules, rematch days, chances or teams doesn't touch the save.

## Not verified

- The example in §7 was built (`make release`, the ROM built) and not played: not
  the number request, the calls, the map marker, or the rematch.
- What `scr_seq_0953.s` does for double-battle trainers (twins, couples) when asking
  for a number; it reads the double partner's script number but wasn't traced.
- The special contacts (Mom's savings and gifts, Kurt, Buena, Baoba, the Day-Care,
  Ethan/Lyra) are only summarized here.
- When exactly the trigger setters run (which field loop or script calls
  `FieldSystem_TryTrigger*Call`); only the setters themselves were read.
