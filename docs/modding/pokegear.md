<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# The Pokégear: cards, radio and the map card

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The Pokégear is one screen with up to four apps: the skin picker, the radio, the map and
the phone. The map and radio are **cards** you get during the story. The radio plays
twelve shows; which one you hear depends on where the tuner cursor is, where you are,
the hour, and story flags. Some radio songs change wild encounters.

This guide covers the Pokégear frame, the cards and skins, the whole radio, and the parts
of the map card the other guides don't: markings, roamer icons, the rematch icon, zoom and
scrolling, and how the Kanto unlock is drawn.

- The phone app, calls and rematches: [phone.md](phone.md).
- Map sections, the Town Map picture, the location table, fly points, the unlock levels:
  [town-map-and-fly.md](town-map-and-fly.md).
- What March, Lullaby, Hoenn/Sinnoh Sound and the Unown signal do to encounters:
  [encounter-mechanics.md §9](encounter-mechanics.md#9-the-radio).

| pokeemerald (PokéNav) | here |
|---|---|
| `src/pokenav.c`, one menu with conditions/ribbons/match call | `src/application/pokegear/main/`: a frame that runs one app overlay at a time |
| PokéNav "region map" | the map card, `src/application/pokegear/map/` |
| no radio | `src/application/pokegear/radio/`, one file per show in `shows/` |
| `FLAG_ADDED_MATCH_CALL_TO_POKENAV` and friends | `registerpokegearcard(n)`, saved in `SavePokegear.registeredCards` |

## Where things are

| What | File |
|---|---|
| frame: launches apps, switches between them | `src/application/pokegear/main/pokegear_main.c` |
| app buttons, card masks, skin graphics, clock | `src/application/pokegear/main/pokegear_app_ui.c` |
| app ids (`GEAR_APP_*`) | `include/application/pokegear/pokegear_internal.h:9` |
| card ids (`GEARCARD_*`) | `include/constants/pokegear_card.h` |
| saved Pokégear data | `SavePokegear`, `include/save_pokegear.h:41`; `src/save_pokegear.c` |
| skin picker | `src/application/pokegear/configure/` |
| radio app, which dial layout | `src/application/pokegear/radio/pokegear_radio.c` |
| tuner: dial spots, input | `src/application/pokegear/radio/pokegear_radio_tuner.c` |
| dial spot → show, show runner, text printer | `src/application/pokegear/radio/radio_show.c` |
| one show each | `src/application/pokegear/radio/shows/*.c` |
| show ids (`RADIO_STATION_*`) | `include/constants/radio_station.h` |
| radio sound player | `src/sound_radio_sys.c` |
| radio song → encounter effect | `GetRadioMusicPlayingSeq`, `src/field/gear_phone_calls.c:276` |
| show text | `files/msgdata/msg/msg_0409.json` to `msg_0420.json` ([§3](#3-the-shows)) |
| map card | `src/application/pokegear/map/pokegear_map*.c` |
| map markings | `src/application/pokegear/map/pokegear_map_markings.c`, `src/map_markings_ram.c`, `include/map_markings_ram.h` |

## 1. The frame, cards and skins

### Apps

`Pokegear_Main` (`src/application/pokegear/main/pokegear_main.c:97`) is a state machine.
Each app is a separate overlay (`PokegearMap_*`, `PokegearRadio_*`, `PokegearPhone_*`,
`PokegearConfigure_*`, all in overlay `pokegear_app`). When an app ends, the frame reads
`appReturnCode` and launches the next one (`Pokegear_MainStep_RunMap`, line 217, and the
other `Run*` steps).

| `GEAR_APP_*` | Value | App |
|---|---:|---|
| `CONFIGURE` | 0 | skin picker |
| `RADIO` | 1 | radio |
| `MAP` | 2 | map card |
| `PHONE` | 3 | phone |
| `CANCEL` | 4 | the close button; also used internally to return from Easy Chat to the map |

The **Easy Chat** screen for map memos is launched by the frame, not the map app: the map
returns `GEAR_RETURN_CANCEL`, the frame unloads its graphics and runs Easy Chat
(`Pokegear_MainStep_LaunchDebug`, line 248, despite the name), then reopens the map with
the chosen word (`Pokegear_MainStep_RunDebug`, line 262).

**Which app opens first** (`Pokegear_Init`, line 72):

- a scripted phone call opens the phone;
- otherwise the last app used (`lastUsedApp`, saved on exit at line 144), unless it was
  the map or radio and that card is missing, then the skin picker.

A new save starts with `lastUsedApp = 3`, the phone (`src/save_pokegear.c:32`).

The bottom row of the touch screen has five buttons (`sTouchscreenButtonHitboxes`,
`pokegear_app_ui.c:26`). Buttons for missing cards are covered with a blank tile block
(`PokegearApp_DrawAppButtons`, line 114) and ignored on touch (line 72). With the D-pad,
the button list has 3, 4 or 5 entries depending on the cards (`sAppSwitchButtonSpecs`,
line 464).

### Cards

| Card | Script | Saved | Given in |
|---|---|---|---|
| phone | always there | | |
| map | `registerpokegearcard(1)` | `registeredCards` bit 0 | `data/maps/Cherrygrove/scripts.pory:463` (the guide gent) |
| radio | `registerpokegearcard(2)` | `registeredCards` bit 1 | `data/maps/Goldenrod_RadioTower_1F/scripts.pory:156` (the quiz); also `data/maps/Lavender_RadioStation/scripts.pory:39` if you don't have it yet |

`ScrCmd_RegisterPokegearCard` (`src/scrcmd_c.c:4609`) calls `SavePokegear_RegisterCard`
(`src/save_pokegear.c:59`). Card 1 and 2 are OR-ed in. **Card 0, or any other value,
clears both cards** (`registeredCards = 0`, line 62), so `registerpokegearcard(0)` takes
the map and radio away.

The radio's Kanto stations need two more flags, not cards ([§2](#which-dial-layout)):
`FLAG_RESTORED_POWER` (`data/maps/Route10_PowerPlantBroken/scripts.pory:47`) and
`FLAG_GOT_EXPN_CARD` (`data/maps/Lavender_RadioStation/scripts.pory:37`).

The map's Kanto unlock is `setpokegearmapunlocklevel(n)`
(`ScrCmd_SetPokegearMapUnlockLevel`, `src/scrcmd_c.c:4627`); values above 2 are ignored
(`Pokegear_SetMapUnlockLevel`, `src/save_pokegear.c:77`). What each level shows is in
[town-map-and-fly.md](town-map-and-fly.md#regions-and-kanto); how it is drawn is in
[§5](#the-kanto-unlock).

### Skins

There are six skins, picked in the configure app (a 3×2 grid,
`PokegearConfigure_SetNewSkin`, `src/application/pokegear/configure/pokegear_configure_ui.c:73`).
The skin is saved in `SavePokegear.skin` when the picker closes
(`pokegear_configure.c:94`).

Every app loads its graphics as "skin + base file": the frame's background, buttons and
palettes from `files/application/pokegear/pgear_gra/` (`PokegearApp_LoadSkinGraphics`,
`pokegear_app_ui.c:269`: tiles 48-53, 36-41, palettes 30-35, 24-29, tilemaps 54-59,
42-47), the radio from `radio/pgradio_gra/` (`pokegear_radio_gfx.c:305`), the map from
`map/pgmap_gra/` (`pokegear_map_gfx.c:294`). A seventh skin needs a seventh file after
each of those groups, which shifts every file after it in the archive, and a new spot in
the picker.

**Skin unlocks were cut.** The save has a 9-bit `unlockedSkins` field and the picker greys
out locked skins (`PokegearConfigure_DrawUnlockedSkinsButtons`, `pokegear_configure_ui.c:80`),
but the picker reads the saved bits and then overwrites them with `0xFF`
(`pokegear_configure.c:89-90`). Nothing writes `unlockedSkins`. To lock skins, delete line
90 and set the bits from a new script command.

### What is saved

`SavePokegear` (`include/save_pokegear.h:41`, 0x658 bytes):

| Field | Meaning |
|---|---|
| `lastUsedApp` | app to open next time |
| `mapZoomed` | map card zoom, kept between visits |
| `radioCursorX`, `radioCursorY` | tuner cursor, kept between visits (starts at 128, 128) |
| `unlockedSkins` (9 bits) | unused ([above](#skins)) |
| `unk_4_9` (9 bits), `unk_4_29` (3 bits) | unused; nothing reads or writes them |
| `skin` (7 bits) | current skin |
| `registeredCards` (2 bits) | bit 0 map, bit 1 radio |
| `mapUnlockLevel` (2 bits) | 0, 1, 2 |
| `mapMarkings` | 100 map markings ([§5](#markings-and-memos)) |
| `callPersistentState`, `phoneContacts` | the phone ([phone.md §9](phone.md#9-saves)) |

The unused bits are free space for a mod without changing the save size
([save-data.md](save-data.md)).

## 2. The radio tuner

### The dial is not a frequency

The radio has no frequency number. The touch screen shows a round dial (the tuning area is
a circle at (128, 92), radius 52, `sTuningAreaHitbox`,
`src/application/pokegear/radio/pokegear_radio_tuner.c:12`). You drag a cursor around it,
move it with the D-pad (2 pixels per frame, line 233), or press one of four buttons that
snap the cursor to a spot (`sTuningButtonHitboxes`, line 78; A cycles through them, line
225).

Each station is **two circles around the same point**: inside the small one you hear it
clearly, inside the big one with static. The lists are in `sTuningHitboxes`
(line 68), one per dial layout:

| Spot | Centre | Clear radius | Static radius | Dial slot |
|---|---|---:|---:|---:|
| top left | (112, 76) | 4 | 16 | 0 |
| top right | (152, 76) | 4 | 20 | 1 |
| bottom left | (96, 108) | 4 | 16 | 2 |
| bottom right | (136, 116) | 4 | 20 | 3 |
| top centre (Expansion Card only) | (128, 48) | 4 | 8 | 4 |

`Radio_GetTunedStationID` (line 281) finds the first circle that contains the cursor. Its
index / 2 is the **dial slot**, and an even index (the small circle) means a clear signal
(line 310). With static, about 70% of the letters of each line are replaced by dots
(`PrintRadioLine`, `radio_show.c:241`, calling `String_RadioAddStatic(msg, 70)`,
`src/pm_string.c:301`).

The four buttons always snap to the four Johto spots (`Radio_SnapCursorToChannelHitbox`,
line 405). There is no button for the top-centre spot; you have to drag to it.

### Which dial layout

When the radio opens, `Radio_GetAvailableChannels` (`pokegear_radio.c:152`) picks one
layout for the whole visit. The checks run in this order:

| # | Condition | Layout (`RADIO_STATION_SELECTION_*`) | Spots |
|---:|---|---|---|
| 1 | the map's `radio_signal` is false | `NO_SIGNAL` | none |
| 2 | the map is in `sAlphMaps` (`pokegear_radio.c:103`: Ruins of Alph hall and entrance, including the Sinjoh event copies) | `ALPH` | centre (128, 92): clear r 4, static r 16 → slot 5 |
| 3 | the map's `region` is Kanto, before `FLAG_RESTORED_POWER` | `NO_SIGNAL` | none |
| 4 | Kanto, with `FLAG_GOT_EXPN_CARD` | `KANTO_EXPN` | slots 0-4 |
| 5 | Kanto, without it | `KANTO` | slots 0-2 |
| 6 | the map is in `sMahoganyMaps` (line 111: Mahogany, its buildings, the Rocket hideout, Route 43, Lake of Rage) and `FLAG_ROCKET_HIDEOUT_CLEARED` is not set | `MAHOGANY` | whole dial: clear r 38, static r 52 → slot 7 |
| 7 | the Rocket takeover is on (`VAR_SCENE_ROCKET_TAKEOVER` is 2, 3 or 4, `Save_VarsFlags_IsInRocketTakeover`, `src/sys_vars.c:252`) | `ROCKET` | whole dial → slot 6 |
| 8 | otherwise | `JOHTO` | slots 0-3 |

`radio_signal` and `region` are per-map fields in `map.json`
([maps-and-warps.md](maps-and-warps.md)); the code reads them with
`MapHeader_CanReceiveRadioSignal` and `MapHeader_GetRegionNo` (`src/map_header.c:173`,
`:128`).

The takeover variable is set to 2 in `data/maps/Goldenrod_RadioTower_1F/scripts.pory:394`
(and Cianwood, Olivine, Mahogany), 3 in `Goldenrod_Tunnel_B1F:580`, 4 in
`Goldenrod_RadioTower_1F:448`, and 5 (over) in `Goldenrod_RadioTowerObservationDeck:171`.

### From dial slot to show

`RadioShow_TranslateStationID` (`src/application/pokegear/radio/radio_show.c:94`) turns
the dial slot into a show id (`RADIO_STATION_*`), reading the DS clock each time a segment
starts:

| Dial slot | Show | When |
|---:|---|---|
| 0 | Pokémon Music (`RADIO_STATION_POKEMON_MUSIC`) | always |
| 1 | Pokémon Talk | always |
| 2 | Trainer Profiles | even hours (0:00, 2:00 ... 22:00) |
| 2 | That Town, These People | odd hours |
| 3 | Pokémon Search Party | hours 0, 3, 6 ... 21 |
| 3 | Serial Radio Drama | hours 1, 4, 7 ... 22 |
| 3 | Buena's Password | hours 2, 5, 8 ... 23 |
| 4 | Poké Flute | always |
| 5 | Unown signal | always |
| 6 | Team Rocket broadcast | always |
| 7 | Mahogany signal | always |
| (none) | Commercials | between two segments, [below](#segments-and-commercials) |

The code is `hour % 2` and `hour % 3` (lines 112, 117), so the show changes **every
hour**. The comments above those lines ("00:00 - 11:59", "16:00 - 23:59") don't match the
code. The phone agrees with the code: Buena's "on air" check is `hour % 3 == 2`
(`Phone_IsBuenasPasswordHour`, `src/phonebook_dat.c:142`).

Put together, what you can hear where:

| | Johto | Kanto, power on | Kanto + Expansion Card | Ruins of Alph | Mahogany area | Rocket takeover |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Pokémon Music, Pokémon Talk | ✓ | ✓ | ✓ | | | |
| Trainer Profiles / That Town | ✓ | ✓ | ✓ | | | |
| Search Party / Drama / Buena | ✓ | | ✓ | | | |
| Poké Flute | | | ✓ | | | |
| Unown, Team Rocket, Mahogany signal | | | | Unown | Mahogany | Rocket |

There is no Sinjoh Ruins station: the Sinjoh event maps of the Ruins of Alph get the Unown
signal through `sAlphMaps`. The **Lucky Channel** lottery is not a radio show; it is a
counter script in the Radio Tower (`data/maps/Goldenrod_RadioTower_1F/scripts.pory:703`,
`src/scrcmd_lottery.c`).

### Segments and commercials

A show runs in **segments**. `RadioShow_BeginSegment` (line 131) calls the show's
`setup`, and every frame `RadioShow_Main` (line 207) calls its `print` until it returns
TRUE. Then `teardown` runs, the text scrolls away, and a new segment starts on the same dial
slot.

A show that sets `radioShow->triggerCommercials` before returning TRUE gets one commercial
next (line 98). Talk, Search Party, Drama, Buena, Trainer Profiles and That Town do this.
Pokémon Music doesn't, and the four signal shows never end.

**Text printing** (`RadioPrintInit`, line 258): a message is split at `\n` and printed one
line at a time into a 2-line window (28 tiles wide, `sWindowTemplates`,
`pokegear_radio_gfx.c:28`). After 45 frames the window scrolls up one line
(`RadioShow_DelayAndScrollLine`, line 171). Placeholders are expanded first. Most shows end
with `RadioPrintAndPlayJingle` (line 281): it starts `SEQ_GS_RADIO_JINGLE` and the
segment ends when the jingle stops.

The show title and host name are printed in two small windows: messages 0 and 1 of each
show's bank.

## 3. The shows

| Show (`RADIO_STATION_*`) | File | Text | Music |
|---|---|---|---|
| 0 Pokémon Music | `shows/pokemon_music.c` | `msg_0416` | by weekday ([below](#pokémon-music)) |
| 1 Pokémon Talk | `shows/pokemon_talk.c` | `msg_0414` | `SEQ_GS_OHKIDO_RABO` |
| 2 Pokémon Search Party | `shows/pokemon_search_party.c` | `msg_0419` | `SEQ_GS_RADIO_VARIETY` |
| 3 Serial Radio Drama | `shows/serial_radio_drama.c` | `msg_0413` | `SEQ_GS_RADIO_VARIETY` |
| 4 Buena's Password | `shows/buenas_password.c` | `msg_0411` | `SEQ_GS_AIKOTOBA` |
| 5 Trainer Profiles | `shows/trainer_profiles.c` | `msg_0420` | `SEQ_GS_RADIO_TRAINER` |
| 6 That Town, These People | `shows/that_town_these_people.c` | `msg_0415` | `SEQ_GS_RADIO_PT` |
| 7 Poké Flute | `shows/poke_flute.c` | `msg_0417` (title only) | `SEQ_GS_HUE` |
| 8 Unown signal | `shows/unown.c` | `msg_0410` (title only) | `SEQ_GS_RADIO_UNKNOWN` |
| 9 Team Rocket | `shows/team_rocket.c` | `msg_0418` | `SEQ_GS_SENKYO_R` |
| 10 Mahogany signal | `shows/mahogany_signal.c` | `msg_0409` (title only) | `SEQ_GS_KAIDENPA` |
| 11 Commercials | `shows/commercials.c` | `msg_0412` | none (silence after the jingle) |

The show id is the row of `sRadioShowFuncs` (`radio_show.c:36`). Every bank's message 0 is
the title and message 1 the host. `RadioShow_Create` also loads `msg_0269` (line 69), but
nothing reads it. `include/radio_show.h` describes older layouts of the show data and is
not included anywhere.

### Pokémon Music

`RadioShow_PokemonMusic_Setup` (`shows/pokemon_music.c:96`) picks a song and a message by
the weekday:

| Day | Song | Message |
|---|---|---|
| Sunday, with GB Sounds in the bag | one of 25 GB Sounds songs, at random | 3 |
| Sunday, without | March | 12 |
| Monday, Friday | March | 4, 8 |
| Tuesday, Saturday | Lullaby | 5, 9 |
| Wednesday | Hoenn Sound with the National Dex, else March | 10, else 6 |
| Thursday | Sinnoh Sound with the National Dex, else Lullaby | 11, else 7 |

Messages are `msg_0416`: 2 is the intro, then `3 + weekday` (Sunday = 0) unless replaced as
above. The day message repeats until the date changes (line 180); then the song fades and
the show restarts with the new day.

The songs are `sMusicIDs_Default` (March `SEQ_GS_RADIO_MARCH`, Lullaby
`SEQ_GS_RADIO_KOMORIUTA`, Hoenn `SEQ_GS_RADIO_R_101`, Sinnoh `SEQ_GS_RADIO_R_201`, line
48) and `sMusicIDS_GBSounds` (line 55). The GB pick is `(LCRandom() % 25000) / 1000`
(line 87); since `LCRandom` returns 0-65535, entries 0-14 are a little more likely
(about 4.6% each) than entries 16-24 (about 3.1%).

The GB list includes the GB March, GB Lullaby and GB Poké Flute (entries 20-22).
`GetRadioMusicPlayingSeq` counts those as March, Lullaby and Poké Flute, so on a Sunday
the radio can, rarely, boost encounters or wake Snorlax.

**Encounter effects** are in [encounter-mechanics.md §9](encounter-mechanics.md#9-the-radio):
March +25 and Lullaby −25 to the movement factor (`src/field/encounter_check.c:583`),
Hoenn/Sinnoh Sound swap grass slots 2-5 (line 155), the Unown signal favours uncaught
letters (line 1323). The song keeps playing after you close the Pokégear.

### Pokémon Talk

Each segment (`RadioShow_PokemonTalk_Init`, `shows/pokemon_talk.c:152`):

1. If a swarm is active today, message 32 names its place and species
   (`GetSwarmInfoFromRand`, line 166; [encounter-mechanics.md §8](encounter-mechanics.md#8-swarms)).
2. Five pairs of "*species* may be seen around *place*" (message 4) and a two-part
   comment from Mary (message 5).
3. The jingle (message 3), then a commercial.

**Places** (`RadioShow_PokemonTalk_SampleMapAreasAndEncounters`, line 184): every map with
wild encounters in the **same region as the player**, except the maps in
`sFilterLandmarks` (line 43: Mt. Moon Square, the Bug Contest park, the Ruins of Alph
halls, Ice Path B1F-B3F, Whirl Islands B1F-B2F, Tohjo Falls' hidden room, the Safari Zone
entrance), and except Routes 47 and 48 until fly flag 25 is set (by
`Route47_OnTransition`, [unknown-flags-vars.md](unknown-flags-vars.md)). Five different
map sections are drawn at random. The list holds at most 150 maps (an assert at line 212).

**Species** (`RadioShow_PokemonTalk_SampleSpeciesFromMapEncounters`, line 256): all
species in that map's tables (morning/day/night grass, surf, Rock Smash, three rods, the
night fishing species). It prefers species you **haven't caught**: if there are two or more
uncaught, one of them; if exactly one, that one half the time.

**Mary's comment** is message 5: `{STRVAR_1 28, 2, 0}` from messages 6-18 and
`{STRVAR_1 28, 3, 0}` from 19-31. The two starting points are random and step by 2, 4 or 6
each pair, so the five comments in a segment never repeat (line 169).

Roamers are not mentioned on the radio; they appear on the map card ([§5](#roamers)).

### Buena's Password

`RadioShow_BuenasPassword_Init` (`shows/buenas_password.c:81`):

- With the **Blue Card** in the bag, message 4 announces today's password and sets
  `FLAG_DAILY_HEARD_BUENAS_PASSWORD` (line 54). Without it, message 5 tells you to get one.
- The password is message `40 + set` of `data/maps/Goldenrod_RadioTower_2F/text.json`
  (`msg_0066_D23R0102`), where `set` is `VAR_BUENAS_PASSWORD_SET % 30` (line 93). The 30
  words come in groups of three (three starters, three potions, three Balls...).
- The set changes once a day: `Save_VarsFlags_UpdateBuenasPasswordSet`
  (`src/sys_vars.c:269`, from `FieldSystem_HandleDaysPassed`, `src/field_time_events.c:94`)
  picks a new random 0-29, never the same as yesterday.
- Buena's own script asks with `getbuenaspassword(VAR_A, VAR_B)`
  (`ScrCmd_GetBuenasPassword`, `src/field/scrcmd_pokemon_misc.c:1254`): it returns the
  first message of the group and the position (0-2) in it, so the 2F script can offer the
  three words of the group as choices.

### Search Party, Radio Drama, Trainer Profiles, That Town

These four pick episodes at random from a message range. Search Party and That Town only
use episodes whose story condition is met.

| Show | Episodes | Per segment | Unlock conditions |
|---|---|---|---|
| Serial Radio Drama | `msg_0413` 4-25 (22) | 1, never the same as last time (`% 22`, `serial_radio_drama.c:84`) | none |
| Trainer Profiles | `msg_0420` 4-19 (16) | 3 different (`% 16`, `trainer_profiles.c:99`) | none |
| Pokémon Search Party | `msg_0419` 4-16 (13) | 1, not the same as last time | `sEpisodeUnlockFlags`, `pokemon_search_party.c:153` |
| That Town, These People | `msg_0415` 4-23 (20) | 3 different | `sEpisodeUnlockFlags`, `that_town_these_people.c:34` |

Search Party (`RadioShow_PokemonSearchParty_Init`, line 225): episodes 0-1 always, 2 after
`FLAG_BEAT_AZALEA_ROCKETS`, 3 with the Plain Badge, 4 after `FLAG_BEAT_RADIO_TOWER_ROCKETS`,
5 with 8 badges, 6 with 9 badges, 7-9 after visiting Vermilion, 10-12 with 16 badges.

That Town (`RadioShow_ThatTownThesePeople_Init`, line 122): episodes 0-6 (New Bark to
Ecruteak) always, 7 (Cianwood) after fly flag `FLYPOINT_GOLDENROD`, 8 Mahogany, 9
Blackthorn, 10-19 (Kanto towns) after Vermilion. `FLYPOINT_GOLDENROD` is index 15, which
is really **Cianwood's** flag ([town-map-and-fly.md](town-map-and-fly.md#4-fly-points));
so episode 7 waits for Cianwood, and the enum comment "effectively always" is wrong.

"Not the same as last time" is kept in `lastEpisodeID` across commercials, and reset when
you tune to a different show (`radio_show.c:149`).

### Commercials

`RadioShow_Commercials_Init` (`shows/commercials.c:287`) picks one of 36 commercials
(`msg_0412` 2-37) from `sCommercialsData` (line 208). Each row has three bytes:

| Byte | Meaning |
|---|---|
| 0 | unlock condition: always, `FLAG_GOT_POKEDEX`, a fly flag, `FLAG_GAME_CLEAR` or `FLAG_RESTORED_POWER` (lines 301-308) |
| 1 | region: 1 Johto, 2 Kanto, 3 both; compared with the player's map region + 1 (line 318) |
| 2 | **dial slot** it plays after (1 Talk, 2 Profiles/That Town, 3 Search Party/Drama/Buena), or `0xFF` for any |

The fly flags here have the same naming problem: `COMM_UNLOCK_ECRUTEAK` checks
`FLYPOINT_ECRUTEAK` (index 16, Goldenrod's flag) and `COMM_UNLOCK_CIANWOOD` checks
`FLYPOINT_CIANWOOD` (index 18, Ecruteak's flag) (lines 303-304).

### The signal shows

Poké Flute, Unown and Mahogany print nothing: their `print` returns FALSE forever, so you
see the title and hear the song. Team Rocket prints `msg_0418` message 2 over and over
(`RadioShow_TeamRocket_Print`, `shows/team_rocket.c:37`).

The Poké Flute song is what wakes Snorlax: `radiomusicisplaying(5, VAR_SPECIAL_RESULT)` in
`data/maps/Route11/scripts.pory:31` and `data/maps/Route12/scripts.pory:156`
(`ScrCmd_RadioMusicIsPlaying`, `src/field/scrcmd_pokemon_misc.c:1160`).

## 4. Radio music

The radio has its own sound player, `PLAYER_RADIO` (9, `include/sound.h:9`), set up in
`SndRadio_Init` (`src/sound_radio_sys.c:12`): one sequence at a time, its own channel mask
(0xA7FE) and a 0x2EE0-byte heap. It is not one of the players listed in
`sound/sound_data.json`, so a song's `"player"` there doesn't matter for the radio.

| Function | Does |
|---|---|
| `SndRadio_StartSeq(seq)` (line 20) | stops the field and BGM players, starts `seq` on the radio player with the bank from its `sound_data.json` entry, and remembers `seq` (0 if it failed to start) |
| `SndRadio_StopSeq(fade)` (line 32) | stops it and forgets the number |
| `SndRadio_GetSeqNo()` (line 37) | the remembered number; 0 = radio silent |

`SndRadio_GetSeqNo` is what the rest of the game checks:

- `GetRadioMusicPlayingSeq` (`src/field/gear_phone_calls.c:276`) maps it to the encounter
  effect and to `radiomusicisplaying` values (1 March, 2 Lullaby, 3 Hoenn, 4 Sinnoh, 5 Poké
  Flute, 6 Unown).
- While it isn't 0, getting on or off the bike and starting to surf don't change the music
  (`src/field_use_item.c:295`, `:304`; `src/field/player_avatar_actions.c:603`).
- Any new field or BGM song stops the radio (`SndRadio_StopSeq(0)` in
  `src/sound_playback.c:100`, `:120`, and `ClearPlayingBGM`, `:139`). Fanfares pause it
  (`PlayFanfare`, line 695).

Each show's `setup` calls `StopBGM(...)` and then `SndRadio_StartSeq(...)`. Tuning to a spot
with no station stops everything (`Radio_CoordsToStation`, `pokegear_radio_tuner.c:378`).

## 5. The map card beyond the Town Map

The Town Map, Fly screen and map card share code ([town-map-and-fly.md](town-map-and-fly.md#2-the-town-map)).
The map card (`PGMAP_TYPE_GEAR`) adds zoom, markings, roamer icons and the rematch icon.
The Fly screen and Town Map item (`FlyMap_*`, `src/application/pokegear/map/fly_map.c`) load
the markings (line 102) but draw none of these on the map.

### Moving and zooming

| Input | Does | Code |
|---|---|---|
| D-pad | moves the cursor one square; the map scrolls to keep it in view | `PokegearMap_HandleDpadMove`, `pokegear_map_input.c:75` |
| touch the map, drag | selects the square, drags the view | `PokegearMap_HandleMapTouch`, line 214 |
| X, or the lower side button | zoom in / out | line 142, line 242 |
| Y, or the upper side button | open markings for the selected place | line 156 |
| B | back to the app buttons | line 30 |

Unzoomed, a square is 8 pixels and the view is 24 × 17 squares; zoomed, 16 pixels and 12 ×
8 squares (`PokegearMap_UpdateCursorBounds`, `pokegear_map_view.c:45`). The zoom setting is
saved when the map closes (`PokegearMap_ExitInternal`, `pokegear_map.c:223`).

Scrolling stops at tile row 17 and at a column set by the unlock level
(`sMapXScrollLimits`, `pokegear_map.c:36`): 26, 29, 45. The cursor can go one column less
(`pokegear_map_input.c:100`).

### The Kanto unlock

`mapUnlockLevel` changes the map card in three places:

| Level | Scroll limit (`pokegear_map.c:36`) | Tilemap (`PokegearMap_DrawMapTilemap`, `pokegear_map_view.c:956`) | Selecting squares (`PokegearMap_SelectLocationAtCoord`, line 688) |
|---:|---:|---|---|
| 0 | 26 | Johto's east edge copied over x 22-27 | nothing at x ≥ 22, except Mt. Silver (25, 10) |
| 1 | 29 | the Indigo Plateau edge copied over x 29-31 | anything |
| 2 | 45 | the whole map | anything |

Grey "not visited" patches over towns are skipped for Kanto towns below level 2 (line
973). The region name on the info panel comes from the player's square, not the cursor
(`PokegearMap_UpdateLocationPanel`, line 895).

### Markings and memos

Every place in the location table can carry a marking: **four slots, each with an icon and
an Easy Chat word**. Places with a marking show a small icon on the map
(`PokegearMap_UpdateLocationIcons`, `pokegear_map_view.c:491`), and the info panel lists
the icons and words (`PokegearMap_PrintLocationPanel`, line 865).

| Icon (`MapMarkingIcon`, `include/map_markings_ram.h:6`) | In the picker |
|---|---|
| 0 Poké Ball, 1 Pikachu, 2 !, 3 ?, 4 Apricorn, 5 Egg, 6 House, 7 TM/HM | yes |
| 8 `SHOCK` | no; nothing uses it |
| 15 `NULL` | empty slot |

In marking mode (`PokegearMap_HandleKeyInput_SelectMarkingsSlot`,
`pokegear_map_input.c:821`) an even slot takes an icon from the pool of eight and an odd
slot opens Easy Chat for a word (line 851). The map remembers the place and slot in
`sessionState`, the frame runs Easy Chat ([§1](#apps)), and on return the word is stored
(`PokegearMap_InitInternal`, `pokegear_map.c:170`). Icons and words can be dragged
between slots or onto the trash can.

Sinjoh Ruins and the S.S. Aqua can't be marked (`PokegearMap_CanMarkLocation`,
`pokegear_map_view.c:644`).

**Storage.** In RAM the markings are a linked list of up to 100 nodes
(`MapMarkingsHeapNode`, `pokegear_map_markings.c`); a node is freed when all eight parts
are empty (`MapMarkingsRAM_IsInUse_EraseIfNot`, `src/map_markings_ram.c:40`). On exit the
list is written, in order, to `SavePokegear.mapMarkings`: 100 entries of a map id, four
4-bit icons and four words (`MapMarkingsSave`, `include/map_markings_ram.h:25`). Entries are
keyed by **map id**, so a marking follows the location table entry with that `mapId`. Map
id 0 or ≥ `MAP_ID_MAX` marks an empty entry (`MapMarkingsSave_MapIDisValid`,
`src/map_markings_ram.c:9`).

An icon is saved in 4 bits, so ids 0-14 fit. To add a ninth picker icon, draw it in the
markings sprite sheet and extend the pool hitboxes (`pokegear_map_input.c:889`) and
sprites (`PGMAP_SPRITE_MARKINGS_MENU_ICON_*`,
`include/application/pokegear/map/pokegear_map_internal.h:71`). Not tried.

### Roamers

When the map card opens, it reads each **active** roamer's current map
(`ROAMER_DATA_MET_LOCATION`, which holds the map it is on,
[roamers.md](roamers.md#1-the-saved-data)) into `roamerLocations`
(`PokegearMap_InitInternal`, `pokegear_map.c:207`). Inactive roamers get 0
(`MAP_EVERYWHERE`), which hides the icon (`pokegear_map_view.c:537`).

The icon is drawn at the **location table entry** for that map
(`PokegearMap_GetLocationSpecByMapID`, line 542), at the entry's square plus its
`objXoffset`/`objYoffset`. The result is not checked for NULL: a roamer on a map that has
no entry in `sLocationSpecs`, or on a hidden one, makes the game read through a null pointer.
All 41 maps in `sRoamerLocations` (`src/field_roamer.c:27`) have entries today, so **if you
add a roaming map, add a location entry for it too**
([town-map-and-fly.md](town-map-and-fly.md#adding-a-place-to-the-town-map)).

Roamer *i* uses sprite `PGMAP_SPRITE_ROAMER_RAIKOU + i`, which shows animation frame *i*
(`pokegear_map_gfx.c:829`). The roamer ids are Raikou 0, Entei 1, Latias 2, Latios 3
(`include/constants/roamer.h:4`), while the sprite enum names slot 2 Latios and slot 3
Latias (`pokegear_map_internal.h:47`). Which picture frame 2 is was not checked.

The icons are only read on opening: a roamer that moves while the map is open doesn't move
on it.

### The rematch icon

The only phone information on the map is one icon on the info panel
(`PGMAP_SPRITE_GEAR_BATTLE`). It shows when the selected place is the `mapId` of a
**registered route trainer** (phone book `type` 0) who wants a rematch now or holds a gift
(`PokegearMap_MapHasPhoneRematchOrGift`, `pokegear_map_view.c:781`, called at line 860).
"Wants a rematch now" is `PhoneBookTrainerGetRematchInfo` (`src/phone_rematch.c:9`), which
for Kenji (contact 16) also requires daytime. Gym leaders (type 12) never show it. See
[phone.md §6](phone.md#6-rematches).

## 6. How-tos

### Change what a show says

Edit the bank from [§3](#3-the-shows) in `files/msgdata/msg/`. Keep each line (between
`\n`) within the 28-tile radio window: the radio prints line by line, so `\r` page breaks
aren't needed. Keep the placeholders the code fills in (Talk's `{STRVAR_1 0, 1, 0}`,
`{STRVAR_1 4, 0, 0}`; Buena's `{STRVAR_34 18, 0, 0}`). See
[text-and-messages.md](text-and-messages.md#8-line-width) for widths.

**More episodes.** The counts are in the code. To add a 23rd radio drama:

1. Add `msg_0413_00026` at the end of `msg_0413.json`.
2. In `RadioShow_SerialRadioDrama_Init` (`shows/serial_radio_drama.c:84`):
   ```diff
   -    data->episodeID = LCRandom() % 22;
   +    data->episodeID = LCRandom() % 23;
        if (data->episodeID == radioShow->lastEpisodeID) {
   -        data->episodeID = (data->episodeID + 1) % 22;
   +        data->episodeID = (data->episodeID + 1) % 23;
   ```

The same pattern for the others:

| Show | Change |
|---|---|
| Trainer Profiles | `% 16` (`trainer_profiles.c:99`) |
| That Town | a row in `sEpisodeUnlockFlags`, the `20` in the loop (line 141) and `unlockedEpisodes[20]` (line 27) |
| Search Party | a row in `sEpisodeUnlockFlags`; `unlockedEpisodes[13]` (line 147) |
| Commercials | a row in `sCommercialsData`; `unlockedCommercials[36]` (line 199) |
| Talk comments | the `13`s in `RadioShow_PokemonTalk_Init` (lines 169-176) and the offset `msg_0414_00019 - msg_0414_00006` (line 118); the step must stay coprime with the count |
| Buena's passwords | `% 30` in `buenas_password.c:93`, `src/sys_vars.c:271` and `:274`, and `scrcmd_pokemon_misc.c:1258`, plus the choices in the Radio Tower 2F script (not traced) |

### Change where or when a station can be heard

- **No radio on a map:** set `"radio_signal": false` in its `map.json`.
- **Unown or Mahogany signal on more maps:** add the map to `sAlphMaps` or `sMahoganyMaps`
  (`pokegear_radio.c:103`, `:111`).
- **A different unlock:** change the flags in `Radio_GetAvailableChannels`
  (`pokegear_radio.c:152`). For Kanto radio from the start, drop the `FLAG_RESTORED_POWER`
  check.
- **Give Johto the Poké Flute:** add the top-centre spot to the Johto list. Its indexes 8
  and 9 become dial slot 4:
  ```diff
   static const TouchscreenHitbox sTuningHitboxes_Johto[] = {
       ...
       { .circle = { TOUCHSCREEN_CIRCLE_SENTINEL, 136, 116, 20 } },
  +    { .circle = { TOUCHSCREEN_CIRCLE_SENTINEL, 128, 48, 4 } },
  +    { .circle = { TOUCHSCREEN_CIRCLE_SENTINEL, 128, 48, 8 } },
       { .rect = { TOUCHSCREEN_RECTLIST_END } },
   };
  ```
  A spot's circles must not overlap another spot's, or the first one in the list wins.
- **Different hours:** change `RadioShow_TranslateStationID` (`radio_show.c:104`). If you
  move Buena, change `Phone_IsBuenasPasswordHour` (`src/phonebook_dat.c:142`) to match,
  since her phone calls (`src/field/gear_phone_calls.c:209`,
  `phone_scripts_buena.c:102`) use it. For example, Buena from 18:00 to 23:59, the Drama
  in the afternoon, the Search Party otherwise:
  ```diff
       case 3:
  -        return RADIO_STATION_POKEMON_SEARCH_PARTY + (radioShow->time.hour % 3);
  +        if (radioShow->time.hour >= 18) {
  +            return RADIO_STATION_BUENAS_PASSWORD;
  +        } else if (radioShow->time.hour >= 12) {
  +            return RADIO_STATION_SERIAL_RADIO_DRAMA;
  +        }
  +        return RADIO_STATION_POKEMON_SEARCH_PARTY;
  ```
  ```diff
   BOOL Phone_IsBuenasPasswordHour(int x) {
  -    return (x % 3) == 2;
  +    return x >= 18;
   }
  ```

The show is chosen when a segment starts, so a show that is already playing finishes even if
the hour changes.

### Change the music

- **A show's song:** the constant in its `setup` (table in [§3](#3-the-shows)), or
  `sMusicIDs_Default` / `sMusicIDS_GBSounds` / the weekday switch in `pokemon_music.c`.
- **Keep the encounter effects right:** they follow the sequence number, not the show. If
  you replace `SEQ_GS_RADIO_MARCH` with another song, add that song to the March case of
  `GetRadioMusicPlayingSeq` (`src/field/gear_phone_calls.c:279`), or the boost is lost.
  Any show that plays a March/Lullaby/Hoenn/Sinnoh/Poké Flute/Unown sequence gets its effect.
- **A new song:** add it to `sound/` as in [music.md](music.md#adding-a-song) and use its
  `SEQ_*`. It plays on the radio player whatever `"player"` says; the radio player's heap
  is 0x2EE0 bytes, and whether a large song fails to start there was not tested.

### Add a station

A show is three functions and a row in `sRadioShowFuncs`. This adds a "Trivia" show on the
top-centre spot in Johto (in Kanto the spot stays the Poké Flute).

1. **The id.** `include/constants/radio_station.h`:
   ```c
   #define RADIO_STATION_COMMERCIALS            11
   #define RADIO_STATION_TRIVIA                 12
   ```
2. **The text.** A new bank `msg_0829.json` (or the next free number) with title, host, an
   intro and a few lines; add it as in [text-and-messages.md](text-and-messages.md#adding-a-bank).
3. **The show.** `src/application/pokegear/radio/shows/trivia.c`, modelled on
   `trainer_profiles.c`:
   ```c
   #include "global.h"

   #include "application/pokegear/radio/radio_internal.h"
   #include "msgdata/msg.naix"
   #include "msgdata/msg/msg_0829.h"

   #include "math_util.h"
   #include "sound_playback.h"
   #include "sound_radio.h"

   typedef struct TriviaData {
       u16 state;
       u16 msgID;
   } TriviaData;

   BOOL RadioShow_Trivia_Setup(RadioShow *radioShow) {
       TriviaData *data = Heap_Alloc(radioShow->heapID, sizeof(TriviaData));
       MI_CpuClear8(data, sizeof(TriviaData));
       radioShow->showData = data;
       radioShow->showMsgData = NewMsgDataFromNarc(MSGDATA_LOAD_DIRECT, NARC_msgdata_msg, msg_0829, radioShow->heapID);
       ReadMsgDataIntoString(radioShow->showMsgData, msg_0829_00000, radioShow->showTitle);
       ReadMsgDataIntoString(radioShow->showMsgData, msg_0829_00001, radioShow->showHost);
       data->msgID = msg_0829_00003 + LCRandom() % 4;   // messages 3-6
       StopBGM(GF_GetCurrentPlayingBGM(), 0);
       SndRadio_StartSeq(SEQ_GS_RADIO_TRAINER);
       return FALSE;
   }

   BOOL RadioShow_Trivia_Print(RadioShow *radioShow) {
       TriviaData *data = radioShow->showData;
       switch (data->state) {
       case 0:
           RadioPrintInitEz(radioShow, msg_0829_00002);   // intro
           ++data->state;
           break;
       case 1:
           if (Radio_RunTextPrinter(radioShow)) {
               RadioPrintInitEz(radioShow, data->msgID);
               ++data->state;
           }
           break;
       case 2:
           if (Radio_RunTextPrinter(radioShow)) {
               radioShow->triggerCommercials = TRUE;
               return TRUE;
           }
           break;
       }
       return FALSE;
   }

   BOOL RadioShow_Trivia_Teardown(RadioShow *radioShow) {
       DestroyMsgData(radioShow->showMsgData);
       Heap_Free(radioShow->showData);
       radioShow->showData = NULL;
       return FALSE;
   }
   ```
   `teardown` can run twice for one segment (`RadioShow_Main` line 213, then
   `RadioShow_EndSegment` line 159 only if `showData` is still set), so clear `showData`.
4. **Declare and register it.** Prototypes next to the others in
   `include/application/pokegear/radio/radio_internal.h`, and a 13th row in
   `sRadioShowFuncs` (`radio_show.c:36`):
   ```c
       { RadioShow_Trivia_Setup, RadioShow_Trivia_Print, RadioShow_Trivia_Teardown },
   ```
5. **Build it.** Add `'application/pokegear/radio/shows/trivia.c',` to `src/meson.build`
   (line 136 area) and `Object main.nef.p/src_application_pokegear_radio_shows_trivia.c.o`
   after the other radio objects in the `pokegear_app` overlay of `main.lsf` (line 1409
   area). A `.c` file `main.lsf` doesn't name isn't linked
   ([debugging.md](debugging.md)).
6. **Put it on the dial.** Add the (128, 48) circles to `sTuningHitboxes_Johto` as in
   the Poké Flute example, and in `RadioShow_TranslateStationID`:
   ```diff
       case 4:
  -        return RADIO_STATION_POKE_FLUTE;
  +        return radioShow->regionNo == MAP_REGION_JOHTO ? RADIO_STATION_TRIVIA : RADIO_STATION_POKE_FLUTE;
   ```
   `MAP_REGION_JOHTO` is in `include/map_header.h:55`; include it if `radio_show.c`
   doesn't see it.

The dial slot is limited to 0-7: `RadioShow_TranslateStationID` and
`RadioShow_BeginSegment` turn 8 and up into 0 (lines 95, 133), and `Radio_Start` ignores
it (`pokegear_radio_tuner.c:142`). A ninth spot needs those three checks raised, which is
why the example reuses slot 4. Commercials with a channel byte of 4 would play after it.

## 7. Quick reference

| To | Change |
|---|---|
| give or take a card | `registerpokegearcard(1)` map, `(2)` radio, `(0)` clears both |
| radio on/off for a map | `radio_signal` in `map.json` |
| Kanto radio unlock | `FLAG_RESTORED_POWER`, `FLAG_GOT_EXPN_CARD` in `Radio_GetAvailableChannels` |
| show hours | `RadioShow_TranslateStationID`; keep `Phone_IsBuenasPasswordHour` in step |
| the weekday songs | `RadioShow_PokemonMusic_Setup` |
| a song's encounter effect | `GetRadioMusicPlayingSeq` and [encounter-mechanics.md](encounter-mechanics.md#9-the-radio) |
| static amount | the 70 in `PrintRadioLine` (`radio_show.c:243`) |
| map zoom / scroll limits | `sMapXScrollLimits`; `maxYscroll = 17` (`pokegear_map.c:198`) |
| marking icons | `MapMarkingIcon` and the pool in `pokegear_map_input.c` |
| skins | six file groups per app; `unlockedSkins` is forced to 0xFF |

## Not verified

Nothing in this guide was tried in an emulator, and none of the code changes were built.

- The recipes in §6 (more episodes, Poké Flute in Johto, Buena's hours, the Trivia station)
  were written from the code and not built.
- Which dial spot the touch screen art shows where: the spot coordinates come from the
  hitbox tables, not from the picture.
- The percentages for the GB Sounds pick and the static are arithmetic on the code.
- That a roamer on a map without a location entry crashes the map card: the code reads
  through the null pointer, but the result was not seen.
- Which roamer picture each animation frame shows (frame 2 named Latios in the sprite enum,
  roamer 2 is Latias).
- That a large new song can fail on the 0x2EE0-byte radio heap.
- How the Radio Tower 2F script turns `getbuenaspassword` into the answer menu.
- Adding a seventh skin or a ninth marking icon.
- Which events stop a radio song started before closing the Pokégear; see
  [encounter-mechanics.md](encounter-mechanics.md#not-verified).
