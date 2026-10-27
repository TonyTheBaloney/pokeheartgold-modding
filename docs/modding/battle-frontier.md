<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# The Battle Frontier

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The Battle Frontier has five facilities: the **Battle Tower**, **Factory**, **Hall**,
**Castle** and **Arcade**. They share one pool of opponent trainers and one pool of
Pokémon sets (the Hall has its own sets). Each facility picks trainers by your streak,
turns sets into Pokémon, and gives Battle Points (BP) for each round of 7 battles
(10 in the Hall). BP are spent at the Exchange Service Corner, on move tutors and on
scratch cards.

The data a hacker edits is in three places:

- **binary archives** in `files/a/2/0/` (trainers and sets). They are not converted
  to JSON; [§13](#unpacking-the-archives) shows how to unpack and repack them.
- **C tables** (trainer ranges, banned species, BP rewards).
- **raw byte tables** in `asm/frontier_script_commands_data.s` and
  `asm/battle_castle_data.s` (Factory and Hall ranges, Castle costs, Arcade odds).

The scripts that run *inside* a facility (between battles) are a separate script system,
and they are only in compiled form (`files/a/1/8/2`). So some flow (when BP are given,
when the Tower Tycoon is marked beaten) can't be read here. This guide says so where it
matters.

| pokeemerald (from memory, see [Not verified](#not-verified)) | here |
|---|---|
| `gBattleFrontierTrainers` | `files/a/2/0/2`, one member per trainer |
| `gBattleFrontierMons` | `files/a/2/0/3` (16-byte sets); Hall sets in `files/a/2/0/4` |
| `gFrontierBannedSpecies` | `sBattleFrontierBanlist`, `src/pokemon.c:4050` |
| BP award tables in `frontier_util.c` | one table per facility, [§8](#8-battle-points) |
| facility scripts in `data/maps/*/scripts.inc` | lobby: `data/maps/*/scripts.pory`; inside: compiled `files/a/1/8/2` |

## Where things are

| What | File |
|---|---|
| opponent trainers (class + list of set ids) | `files/a/2/0/2` (315 members), read by `FrontierTrainer_Load`, `src/frontier/frontier_trainers.c:93` |
| Pokémon sets (Tower, Factory, Castle, Arcade) | `files/a/2/0/3` (951 members), format `FrontierMonSet`, `src/frontier/frontier_trainers.c:49` |
| Battle Hall sets | `files/a/2/0/4` (478 members), same format |
| older trainers and sets, for links with a "version 0" partner | `files/a/1/2/8`, `files/a/1/2/9` (`BattleTower_GetMonSetNarc`, `src/frontier/battle_tower_setup.c:379`) |
| trainer names | `files/msgdata/msg/msg_0027.json`, entry = trainer id |
| trainer intro / win / lose lines | `files/msgdata/msg/msg_0724.json`, entries `id*3`, `id*3+1`, `id*3+2` |
| set → Pokémon (IVs, EVs, nature, ability) | `FrontierMon_Generate`, `src/frontier/frontier_trainers.c:113`; Tower: `BattleTower_GenerateFrontierMon`, `src/frontier/battle_tower_setup.c:208` |
| Tower trainer choice and Palmer | `FrontierFieldSystem_GetRandomFrontierTrainerID`, `src/frontier_opponents.c:217` |
| Castle / Arcade trainer choice | `sBattleCastleTrainerRanges`, `src/frontier/battle_castle_setup.c:43`; `sBattleArcadeTrainerRanges`, `src/frontier/battle_arcade_setup.c:41` |
| Factory trainers, rentals, set ranges | `src/frontier/battle_factory_setup.c`; tables at `asm/frontier_script_commands_data.s:224`-`267` |
| Hall trainers, sets, levels | `src/frontier/battle_hall_setup.c`, `src/frontier/battle_hall_data.c`; tables at `asm/frontier_script_commands_data.s:268`-`532` |
| banned species | `sBattleFrontierBanlist`, `src/pokemon.c:4050`; count in `include/pokemon.h:31` |
| party checks (bans, species and item clause) | `PartyIsValidForFrontier`, `src/frontier_field_system.c:115` |
| BP (saved value, add/spend) | `FrontierData.battlePoints`, `src/frontier_data.c:32`; `FrontierData_BattlePointAction`, `src/frontier_data.c:228` |
| Exchange Service Corner | `BattleFrontier_EventScript_Attendant1` / `Attendant2`, `data/maps/BattleFrontier/scripts.pory:369` / `:673` |
| BP move tutors | `sTutorMoves`, `src/field/scrcmd_move_tutor.c:38`; script `files/fielddata/script/scr_seq/scr_seq_0002.s` |
| Castle CP costs | `asm/battle_castle_data.s:57`-`175`; `src/frontier/battle_castle_opponent_app.c:114` |
| Arcade events | `sBattleArcadeEventFuncs`, `src/frontier/battle_arcade_data.c:109`; odds in `asm/battle_arcade_game_board_data.s` |
| what is saved | `FrontierSave` (`include/save_frontier.h:6`), save chunk 19 ([save-data.md](save-data.md#chunks)) |

## 1. How the code is organised

A challenge has two halves.

**The lobby** is a normal field map with normal scripts in
`data/maps/<Map>/scripts.pory`: the Tower (`BattleTower`, `BattleTower_Elevator`) and
the four buildings `BattleFrontier_BattleFactory`, `_BattleHall`, `_BattleCastle`,
`_BattleArcade`. They check your party, pick the challenge type and save. Then they call
`launchfrontier(N)` (`ScrCmd_LaunchFrontier`, `src/scrcmd_c.c:4156`), which starts the
Frontier application with frontier map `N`:

| `N` | where it's called | facility |
|---:|---|---|
| 3 | `data/maps/BattleFrontier_BattleFactory/scripts.pory:199` | Factory |
| 5, 6 | `data/maps/BattleTower_Elevator/scripts.pory:43`, `:51` | Tower |
| 9 | `data/maps/BattleFrontier_BattleHall/scripts.pory:342` | Hall |
| 11 | `data/maps/BattleFrontier_BattleCastle/scripts.pory:257` | Castle |
| 15 | `data/maps/BattleFrontier_BattleArcade/scripts.pory:260` | Arcade |

**Inside the facility** a second, smaller script engine runs: `FrontierScriptContext`
(`src/frontier/frontier_script_context.c`). Each frontier map names a script file and a
message bank in `sFrontierMapParams` (`src/frontier/frontier_map_params.c:56`). The
script file is a member of `files/a/1/8/2` (11 members), loaded by
`FrontierSystem_LoadMapScripts` (`src/frontier/frontier_system.c:110`). The commands are
`gFrontierCommandTable` (`src/frontier/frontier_script_commands_ext.c:198`), plus one
"action" command per facility that switches on a number: `FrtCmd_TowerAction`
(`src/frontier/frontier_script_commands_misc.c:31`), and the `*_ACTION_*` switches in
`src/frontier/frontier_cmd_factory.c`, `frontier_cmd_hall.c`, `frontier_cmd_castle.c`,
`frontier_cmd_arcade.c`.

`files/a/1/8/2` is a prebuilt binary. There is no source or disassembly for it in this
repository. So the order of calls (record the win, then give BP, then raise the Hall
rank...) is decided by code you can't edit as text. The C functions those scripts call
are all readable.

**Code by facility:**

| Facility | Data while you play | Setup, trainers, battle | Script actions |
|---|---|---|---|
| Tower | `FrontierFieldSystem` (`src/frontier_field_system.c`) | `src/frontier/battle_tower_setup.c`, `src/frontier_opponents.c` | `src/scrcmd_9.c` (lobby), `frontier_script_commands_misc.c` (inside) |
| Factory | `src/frontier/battle_factory_data.c` | `battle_factory_setup.c`; rental screen `battle_factory_app*.c` | `frontier_cmd_factory.c` |
| Hall | `battle_hall_data.c` | `battle_hall_setup.c`; board `battle_hall_app*.c` | `frontier_cmd_hall.c`; lobby `src/scrcmd_battle_hall.c` |
| Castle | `battle_castle_challenge.c` | `battle_castle_setup.c`; CP screens `battle_castle_party_app.c`, `battle_castle_opponent_app.c` | `frontier_cmd_castle.c`; lobby `src/scrcmd_battle_castle.c` |
| Arcade | `battle_arcade_data.c` | `battle_arcade_setup.c`; board `battle_arcade_game_board.c` | `frontier_cmd_arcade.c` |

Shared helpers: `src/frontier/frontier_trainers.c` (load a trainer, turn a set into a
Pokémon), `src/frontier_data.c` (BP, Tower records), `src/frontier_save.c` (records),
`src/frontier_stat_ids.c` (which record slot holds what).

## 2. The facilities at a glance

| | Tower | Factory | Hall | Castle | Arcade |
|---|---|---|---|---|---|
| your Pokémon | 3 (single), 4 (double), 2 (multi) (`NumMonsForTowerMode`, `src/frontier_field_system.c:40`) | 3 rentals; 2 in multi | 1 (single), 2 (double) (`BattleHall_GetPartySize`, `battle_hall_setup.c:336`) | 3; 2 in multi | 3; 2 in multi |
| level | yours above 50 drop to 50 (`battle_tower_setup.c:302`); foes 50 | 50 or 100 ("open level", `BattleFactory_GetMonLevel`, `battle_factory_setup.c:323`) | yours; foes scale ([§10](#10-battle-hall-types-and-ranks)) | above 50 drop to 50 (`battle_castle_challenge.c:156`); foes 50 (`battle_castle_setup.c:213`) | above 50 drop to 50 (`battle_arcade_data.c:165`); foes 50 (`battle_arcade_setup.c:219`) |
| held items | yours | from the set | yours | removed; rent with CP (`battle_castle_challenge.c:154`) | removed (`battle_arcade_data.c:163`); events give some |
| foe sets from | trainer's list | id ranges, not the trainer | `files/a/2/0/4` by type and rank | trainer's list | trainer's list |
| round | 7 battles | 7 | 10 (`data->round = data->winStreak / 10`, `battle_hall_data.c:131`) | 7 | 7 |
| Brain (single only) | Palmer 305/306, battles 21 and 49 | Thorton 309/310, 21 and 49 | Argenta 307/308, 50 and 170 | Darach 313/314, 21 and 49 | Dahlia 311/312, 21 and 49 |

The four facility types are `FRONTIER_CHALLENGE_SINGLE`, `_DOUBLE`, `_MULTI`,
`_LINK_MULTI` (`include/frontier_save_access.h:15`). The Tower has its own modes,
`TOWER_MODE_SINGLE` ... `TOWER_MODE_6` (`include/scrcmd_9.h:8`): single, double, multi
with an AI partner, link, Wi-Fi, Wi-Fi practice, and mode 6 (a link mode whose records go
in the per-friend rows of the save).

## 3. Trainers and sets

### Trainers: `files/a/2/0/2`

One member per trainer, all `u16` (`FrontierTrainerEntry`,
`src/frontier/frontier_trainers.c:42`):

| Offset | Field |
|---|---|
| 0 | trainer class (`TRAINERCLASS_*`) |
| 2 | number of set ids, `n` |
| 4 | `n` set ids into `files/a/2/0/3` |

Members with an odd `n` end with one `0x0000` so their size stays a multiple of 4.
`FrontierTrainer_Load` also fills the name from `msg_0027` entry `id` and the intro line
`id * 3` of `msg_0724` (`frontier_trainers.c:93`-`109`). The battle reads the win and
lose lines from entries `id * 3 + 1` and `id * 3 + 2` (`src/battle/battle_system.c:1391`).
The trainer's sprite comes from its class through `sFrontierTrainerClassSprites`
(`frontier_trainers.c:245`); a class not in that list gets sprite 3.

What the 315 trainers are (dumped from the archive):

| Ids | Who | Set ids used | Sets each |
|---|---|---|---|
| 0-99 | regular, easiest | 1-150 | 19-75 |
| 100-119 | | 151-250 | 48-50 |
| 120-139 | | 251-350 | 28-50 |
| 140-159 | | 351-486 | 26-68 |
| 160-179 | | 487-622 | 23-50 |
| 180-199 | | 623-758 | 17-68 |
| 200-219 | | 759-894 | 25-68 |
| 220-299 | hardest | 251-950 | 28-100 |
| 300-304 | Cheryl, Marley, Riley, Buck, Mira (Tower multi partners) | 220-949 | 53-69 |
| 305, 306 | Palmer, silver and gold | 469, 476, 481 / 948, 949, 950 | 3 |
| 307, 308 | Argenta | none (Hall sets, [§10](#10-battle-hall-types-and-ranks)) | 0 |
| 309, 310 | Thorton | none (set ranges, [§9](#9-battle-factory-rental-pools)) | 0 |
| 311, 312 | Dahlia | 365, 387, 462 / 766, 887, 938 | 3 |
| 313, 314 | Darach | 362, 381, 426, 498, 517, 562 / 634, 720, 770, 856, 927, 941 | 6 |

The Brains also exist in `files/poketool/trainer/trainers.json` (entries 707-711,
`TRAINER_TOWER_TYCOON_PALMER`... in `include/constants/trainers.h:712`). Those entries
are placeholders (one level 5 Rattata each). Nothing in the Frontier reads them, so
editing them changes nothing here.

### Sets: `files/a/2/0/3` and `files/a/2/0/4`

Every member is 16 bytes (`FrontierMonSet`, `frontier_trainers.c:49`). Set 0 is empty.

| Offset | Size | Field |
|---|---|---|
| 0 | u16 | species |
| 2 | 4 × u16 | moves |
| 10 | u8 | EV mask: bit 0 HP, 1 Atk, 2 Def, 3 Speed, 4 Sp. Atk, 5 Sp. Def |
| 11 | u8 | nature (0-24) |
| 12 | u16 | held item |
| 14 | u16 | form |

Example, set 469 (Palmer's Rhyperior): Rock Wrecker, Earthquake, Crunch, Roar; EV mask
`0x06` (Atk, Def); nature 3 (Adamant); Focus Band.

What a set becomes (`FrontierMon_Generate`, `frontier_trainers.c:113`-`184`; the Tower's
copy is `BattleTower_GenerateFrontierMon`, `battle_tower_setup.c:208`):

- **EVs:** 510 split evenly over the stats in the mask, at most 255 each. Two stats get
  255 each; three get 170.
- **Nature:** a random personality is rolled until it has the set's nature and is
  **not shiny**.
- **Ability:** the second ability if the species has one and the personality is odd,
  else the first.
- **Friendship:** 255, or 0 if the set knows Frustration.
- **IVs:** one number for all six stats, from the caller ([§4](#4-how-opponents-are-chosen)).
- **Item:** the set's item. If the trainer can't avoid duplicate items in 50 tries, the
  Tower and Castle/Arcade code use a fixed list instead: Bright Powder, Lum Berry,
  Leftovers, Quick Claw (`sFrontierMonItems`, `frontier_trainers.c:111`;
  `gBattleTowerReplacementItems`, `asm/frontier_script_commands_data.s:147`).
- **Level:** set when the Pokémon is built (`FrontierMon_ToPokemon`,
  `frontier_trainers.c:186`). The special values 120 and 121 mean 50 and 100.

## 4. How opponents are chosen

### IVs by trainer id

The Tower, Castle and Arcade give the opponent's Pokémon an IV that depends only on the
trainer id (`GetFrontierTrainerIVs`, `src/frontier_field_system.c:726`; the same table
again in `FrontierTrainer_GetMonIv`, `frontier_trainers.c:443`):

| Trainer id | 0-99 | 100-119 | 120-139 | 140-159 | 160-179 | 180-199 | 200-219 | 220+ (incl. Brains) |
|---|---|---|---|---|---|---|---|---|
| IV | 3 | 6 | 9 | 12 | 15 | 18 | 21 | 31 |

### Battle Tower

The 7 trainers of a round are picked when the round starts
(`FrontierFieldSystem_SetRandomFrontierTrainers`, `src/frontier_field_system.c:367`),
14 in multi and link modes. Each comes from
`FrontierFieldSystem_GetRandomFrontierTrainerID` (`src/frontier_opponents.c:217`):

- The **bracket** is the number of rounds already won in this streak (`currentRound`,
  read from the save in `FrontierFieldSystem_New`, `src/frontier_field_system.c:292`).
- Battles 1-6 of a round pick from `FrontierTrainerDifficultyBracket[bracket]`
  (`src/frontier_opponents.c:45`); battle 7 picks from
  `FrontierTrainerBracketBosses[bracket]` (`:122`). No trainer appears twice in a round.
- Bracket 7 and up: any trainer 200-299, with no special 7th battle (`:237`).
- **Palmer:** in single mode, battle 7 of bracket 2 (battle 21) is trainer 305 and
  battle 7 of bracket 6 (battle 49) is trainer 306 (`:219`-`226`).

| Bracket (round) | Battles | Battles 1-6 | Battle 7 |
|---:|---|---|---|
| 0 | 1-7 | 0-99 | 100-119 |
| 1 | 8-14 | 80-119 | 120-139 |
| 2 | 15-21 | 100-139 | 140-159 (single: Palmer 305) |
| 3 | 22-28 | 120-159 | 160-179 |
| 4 | 29-35 | 140-179 | 180-199 |
| 5 | 36-42 | 160-199 | 200-219 |
| 6 | 43-49 | 180-219 | 220-239 (single: Palmer 306) |
| 7+ | 50+ | 200-299 | 200-299 |

The trainer's Pokémon are picked from **its own set list** by
`BattleTower_PickTrainerMonSets` (`src/frontier/battle_tower_setup.c:82`): random sets
until there are enough with **different species**. For the first 50 tries it also skips
sets whose item another of its Pokémon already holds; after 50 failed tries it allows
duplicates and replaces every item with the fixed list above. In multi and link modes the
second opponent also avoids the first one's species and items
(`src/frontier/frontier_save_data_helpers.c:19`-`24`). The opponents' AI flags are 7 for
every Tower battle (`battle_tower_setup.c:313`).

The multi partners (trainers 300-304) are generated by
`FrontierFieldSystem_GenerateStatTrainers` (`src/frontier_field_system.c:511`), avoiding
your species and items.

**Wi-Fi modes** don't use the archive: they fight trainers from a downloaded Battle Room,
or the sample room built into the ROM when nothing was downloaded
(`BattleTower_GetRoomTrainer`, `battle_tower_setup.c:178`; sample data
`gBattleTowerSampleTrainers` / `gBattleTowerSampleMons`,
`asm/frontier_script_commands_data.s:150`-`223`).

**Link with an old game.** In link modes, if either player's profile reports version 0,
the Tower uses `files/a/1/2/8` (307 trainers), `files/a/1/2/9` (951 sets) and `msg_0723`
instead (`BattleTower_UsesNewSetNarcs`, `battle_tower_setup.c:400`). An edit to
`a/2/0/2` / `a/2/0/3` doesn't reach those battles.

### Battle Castle and Battle Arcade

Both use the same round ranges as the Tower, as C tables: `sBattleCastleTrainerRanges`
(`src/frontier/battle_castle_setup.c:43`) and `sBattleArcadeTrainerRanges`
(`src/frontier/battle_arcade_setup.c:41`). Rows are `{ min, max, lastBattleMin,
lastBattleMax }` per round (0-7, capped at 7). The trainer is `min + random % (max - min)`,
so **`max` itself is never picked** (`battle_castle_setup.c:78`). The Brains replace
battles 21 and 49 of a single challenge (`battle_castle_setup.c:61`-`66`,
`battle_arcade_setup.c:60`-`63`).

Their Pokémon come from the trainer's set list through `FrontierTrainer_GenerateMons`
(`frontier_trainers.c:510`) and `FrontierTrainer_PickMonSets` (`:471`). This picker
**never** allows two sets with the same species **or the same item**, and it compares
`ITEM_NONE` too, so two item-less sets also count as a clash (`:484`). The 50-try limit
only drops the "partner's species and items" exclusion.

AI flags: Castle rounds 0-1 get 0, rounds 2-3 get 1, later rounds and Darach get 7
(`BattleCastle_GetTrainerAIFlags`, `battle_castle_setup.c:277`). See
[trainers.md](trainers.md#ai-flags) for what the flags do.

### Battle Factory

The Factory ignores the trainers' set lists. Trainers are picked like the Castle's, from
`gBattleFactoryRoundTrainerRanges` (`asm/frontier_script_commands_data.s:228`, same
numbers as the Castle table), with Thorton at battles 21 and 49
(`BattleFactory_GetRandomTrainerId`, `src/frontier/battle_factory_setup.c:56`). Their
Pokémon are drawn from a **range of set ids** chosen by the trainer id and level mode
(`BattleFactory_GetTrainerSetRange`, `:101`). Your rentals are drawn from a range chosen
by the round ([§9](#9-battle-factory-rental-pools)). The opponents avoid your rentals'
species and items, and that rule is never relaxed (`BattleFactory_PickSetIds`, `:134`).

AI flags: rounds 0-1 get 0, rounds 2-3 get 1, later rounds and Thorton get 7
(`BattleFactory_GetTrainerAIFlags`, `:375`).

### Battle Hall

The Hall uses its own sets (`files/a/2/0/4`) and picks trainers by class. See
[§10](#10-battle-hall-types-and-ranks).

## 5. Frontier Brains

| Brain | Facility | Trainer ids | When | Team | IVs | AI |
|---|---|---|---|---|---|---|
| Palmer | Tower, single | 305 / 306 | battle 21 / 49 (`src/frontier_opponents.c:219`) | 3 of his 3 sets | 31 | 7 |
| Thorton | Factory, single | 309 / 310 | battle 21 / 49 (`battle_factory_setup.c:64`) | 3 sets from ranges rows 8 / 9: sets 351-486 IV 12, sets 759-950 IV 31 | per row | 7 |
| Argenta | Hall, single | 307 / 308 | streak battle 50 / 170 (`battle_hall_setup.c:108`) | 1 Hall set ([§10](#10-battle-hall-types-and-ranks)) at your level | 31 (`battle_hall_setup.c:354`) | 7 |
| Darach | Castle, single | 313 / 314 | battle 21 / 49 | 3 of his 6 sets (each species twice) | 31 | 7 |
| Dahlia | Arcade, single | 311 / 312 | battle 21 / 49 | 3 of her 3 sets | 31 | 7 |

Teams dumped from the archive: Palmer silver Rhyperior, Milotic, Dragonite; gold
Heatran, Cresselia, Regigigas. Dahlia silver Medicham, Ludicolo, Dusknoir; gold Blaziken,
Togekiss, Zapdos. Darach silver Empoleon, Staraptor, Houndoom; gold Empoleon, Gallade,
Entei.

Their sets are **shared** with regular trainers. For example set 948 (Heatran) is also
in trainer 234's list. Changing a Brain's set changes it for those trainers too; adding
new sets is safer ([§13](#change-the-brain-teams)).

**Palmer and the prints.** Whether Palmer was beaten is set by the in-facility script
through `TOWER_ACTION_SET_PALMER_DEFEATED`
(`src/frontier/frontier_script_commands_misc.c:70`). Back in the lobby,
`VAR_BATTLE_TOWER_PRINT_PROGRESS` (`include/constants/vars.h:92`) decides the Silver /
Gold Print messages (`data/maps/BattleTower/scripts.pory:1117`-`1144`), and
`battletoweraction(48, ...)` gives the Ability / Great Ability Ribbons
(`FrontierFieldSystem_TryGivePalmerRibbons`, `src/frontier_field_system.c:609`).

## 6. Rules: banned species, levels, clauses

**Banned species.** `sBattleFrontierBanlist` (`src/pokemon.c:4050`) has 18 species:
Mewtwo, Mew, Lugia, Ho-Oh, Celebi, Kyogre, Groudon, Rayquaza, Jirachi, Deoxys, Dialga,
Palkia, Giratina, Phione, Manaphy, Darkrai, Shaymin, Arceus.
`IsPokemonBannedFromBattleFrontier` (`:4071`) also bans the Spiky-eared Pichu
(`:4077`). The same list is used by:

- the Frontier party checks (`PartyIsValidForFrontier`,
  `src/frontier_field_system.c:137`; Hall: `src/scrcmd_battle_hall.c:222`);
- the party menu's "can't enter" marks (`src/party_menu.c:1782`, `:1801`, `:1820`);
- link battle rulesets, which ban the non-mythical ones (`src/battle_regulation.c:134`,
  `:247`).

When you don't have enough eligible Pokémon, `msgboxfrontierbannedspecies(base, ...)`
prints message `base + n` of the map's text, where `n` is the number of banned species
you have **seen** in the Pokédex. The message lists them (`ScrCmd_MsgBoxFrontierBannedSpecies`,
`src/field/scrcmd_message.c:118`; `Frontier_NewBannedSpeciesMessageFormat`,
`src/frontier_opponents.c:133`). So each lobby has 19 such messages: Tower `91`-`109`
(`data/maps/BattleTower/scripts.pory:250`), Hall from 37, Castle and Arcade from 9.

**Species and item clause.** `PartyIsValidForFrontier` (`src/frontier_field_system.c:115`)
checks that the party has enough eggless, unbanned Pokémon with different species and
different held items (`ITEM_NONE` may repeat). After you choose,
`FrontierFieldSystem_PartyHasDuplicateSpeciesOrItems` (`:335`) returns 1 for a repeated
species and 2 for a repeated item. The Hall's lobby check is different: every Pokémon
must be **level 30 or higher**, and for two Pokémon it looks for two eligible Pokémon of
the **same** species (`BattleHall_DoesPartyContainEligibleMons`,
`src/scrcmd_battle_hall.c:200`).

**Levels.** There is no level cap on entry for the Tower, Castle or Arcade: Pokémon above
50 are set to the level 50 experience for the challenge (table in [§2](#2-the-facilities-at-a-glance)).
The Factory's level mode is 0 (level 50) or 1 (open level, 100), and rentals and
opponents are built at that level.

## 7. Streaks, records and what is saved

Frontier records live in `FrontierSave` (`include/save_frontier.h:6`): 112 `u16`
`stats`, 32 × 32 `rowStats` (per-friend rows for link records) and the Tower data. It is
save chunk 19 ([save-data.md](save-data.md#chunks)). `FrontierSave_SetStat` caps every
value at 9999 (`src/frontier_save.c:59`). Each facility's stat ids come from small
functions in `src/frontier_stat_ids.c` (for example `BattleFactory_GetWinStreakStat`).

| Facility | Saved per type |
|---|---|
| Tower | stat `2 * mode` = best streak, `2 * mode + 1` = current streak (`FrontierFieldSystem_RecordSetLost` / `_RecordSetWon`, `src/frontier_field_system.c:430` / `:463`); round count per mode in `FrontierData.towerRounds` (`src/frontier_data.c:45`) |
| Factory | current and best streak, current and best trade count, per type and level mode (`src/frontier_stat_ids.c`) |
| Hall | current and best streak, rank of each type cell, last species; per-species streaks in an extra save chunk (`FrontierSpeciesRecords_*`, `src/frontier_save.c:131`) |
| Castle | current and best streak, CP, CP spent, 3 ranks |
| Arcade | current and best streak |

The current round is always `streak / 7` (Hall: `/ 10`) when a challenge starts, for
example `data->round = data->winStreak / 7` (`src/frontier/battle_factory_data.c:114`).
Facilities raise it by one after each completed round, up to 8 (Hall: 18)
(`BattleFactory_CompleteRound`, `battle_factory_data.c:402`;
`BattleHallData_EndRound`, `battle_hall_data.c:315`).

**Tower trophies.** `BattleTower_ClaimRecordMilestone`
(`src/frontier_field_support.c:293`) looks at stat 0 (best single streak). At 20, 50
and 100 it returns 1, 2, 3 once each. The lobby script then puts the Bronze, Silver or
Gold trophy in the player's room by clearing `FLAG_HIDE_PLAYERS_ROOM_*_TROPHY`
(`data/maps/BattleTower/scripts.pory:114`-`140`).

**Ribbons.** Double, multi, link and Wi-Fi Tower modes give their Ability ribbon at a 50
streak, or at Wi-Fi rank 5 (`FrontierFieldSystem_CheckRibbonStreak`,
`src/frontier_field_system.c:683`; `FrontierFieldSystem_TryGiveOtherTowerRibbons`, `:622`).

## 8. Battle Points

BP is one `u16` in `FrontierData` (`src/frontier_data.c:32`), changed only through
`FrontierData_BattlePointAction` (`:228`). It caps at 9999 and stops at 0. The actions
are the enum at `:217`: 0 get, 1 set, 5 add, 6 subtract.

### Earning BP

| Facility | Function | Single / double, by round | Multi / link | Brain battle |
|---|---|---|---|---|
| Tower | `FrontierFieldSystem_AwardTowerBattlePoints`, `src/frontier_field_system.c:529` | `RegularBattlePointRewards` `{0,3,3,4,4,5,5,7}`, 7 after | link: `LinkBattlePointRewards` `{0,8,9,11,12,14,15,18}`, 18 after | 20 if Palmer was beaten in this round |
| Tower Wi-Fi | same | `WifiBattlePointRewards[rank]` `{0,3,4,5,6,7,8,9,10,10,10,0}` (rank 1-10) | | |
| Factory | `BattleFactory_GetWonBattlePoints`, `battle_factory_data.c:547` | `{0,5,5,5,5,7,7,8,9}`, 9 after | `{0,10,11,12,13,16,17,19,21}`, 21 after | 20 at streak 21 / 49 |
| Hall | `BattleHallData_GetWonBattlePoints`, `battle_hall_data.c:346` | `{0,1,1,1,2,2,2,3,3,3,4,4,6,6,8,8,10,10,12}`, 12 after | link multi: `{0,6,6,6,8,8,8,10,10,10,12,12,14,15,17,17,20,20,23}`; multi always 12 | 20 at streak 50 / 170 |
| Castle | `BattleCastleData_GetRoundTableValue`, `battle_castle_challenge.c:685` | `{0,3,3,4,4,5,5,7,7}`, 7 after | `{0,8,9,11,12,14,15,18,18}`, 18 after | 20 at 21 / 49 |
| Arcade | `BattleArcadeData_GetRoundTableValue`, `battle_arcade_data.c:1021` | `{0,2,2,2,2,4,4,5,6}`, 6 after (`asm/frontier_script_commands_data.s:133`) | `{0,7,8,9,10,13,14,16,17}`, 17 after (`:137`) | 20 at 21 / 49 |

The tables are indexed by the facility's round. Entry 0 is 0, which suggests the scripts
ask for BP after the round counter has gone up (so the first round pays entry 1). That
order is in the compiled scripts and wasn't checked. Only the Tower function adds BP
itself (`src/frontier_field_system.c:555`). The other four return the amount to the
frontier script (for example `FACTORY_ACTION_GET_WON_BATTLE_POINTS`,
`src/frontier/frontier_cmd_factory.c:354`), which presumably passes it to
`FrtCmd_GiveBattlePoints` (`src/frontier/frontier_script_commands_ext.c:883`). The Castle
and Arcade functions are named "round table value" in this repository because their use
isn't visible in C. Their numbers and the 20 at the Brain battles match the other BP
tables.

The tables are declared with more entries than they fill (`[12]`, `[20]`), so the extra
entries are 0. Rounds past the last entry use the constant in the code ("9 after").

**Hall total-streak prizes.** An attendant in the Hall lobby
(`BattleFrontier_BattleHall_EventScript_Attendant3`,
`data/maps/BattleFrontier_BattleHall/scripts.pory:796`) adds up the streaks of every
species (`ScrCmd_BufferBattleHallStreak`, `src/scrcmd_battle_hall.c:401`). For each
milestone of `battleHallWinStreakBP` (`:56`) you haven't claimed, it gives BP: 1 at 10,
3 at 30, 5 at 50 and every 50 up to 450, 10 per 100 up to 1000, 30 per 200 from 1200 to 1800,
50 at 2000 and every 500 up to 9500, then 100-1000 per 10000 up to 100000.
`VAR_BATTLE_HALL_WIN_STREAK_LEVEL` remembers how many were claimed.

### Spending BP

| Where | What | Price set in |
|---|---|---|
| Exchange Service Corner, left attendant | vitamins 1 BP, Rare Candy 48, Power items 16, Toxic/Flame Orb 16, White/Power Herb 32, Bright Powder, Focus Band, Focus Sash, Choice Band/Scarf, Scope Lens, Muscle Band, Razor Claw/Fang 48 | `BattleFrontier_EventScript_Attendant1`, `data/maps/BattleFrontier/scripts.pory:369` |
| Exchange Service Corner, right attendant | 18 TMs, 32-80 BP | `BattleFrontier_EventScript_Attendant2`, `:673` |
| Move tutors (3 NPCs) | moves, 32-64 BP | `sTutorMoves` `cost`, `src/field/scrcmd_move_tutor.c:38` |
| Scratch-off cards | 1 BP a card | `files/fielddata/script/scr_seq/scr_seq_0263.s:52` |

Each prize in the exchange script is a block of three `setvar`s:

```
_0618:
    setvar(VAR_SPECIAL_x8004, 50)    // item id (50 = ITEM_RARE_CANDY)
    setvar(VAR_SPECIAL_x8005, 48)    // count for the bag-space check only
    setvar(VAR_SPECIAL_x8006, 48)    // price in BP
    goto(_09F3)
```

The menu lines come from `menuitemadd(text, help, n)` above them. The purchase is at
`_09F3` (`scripts.pory:607`): it checks BP and bag space, takes the BP and gives **one**
item (`giveitem(VAR_SPECIAL_x8004, 1, ...)`, `:657`), whatever `x8005` says. The item ids
are plain numbers; look them up in `include/constants/items.h`.

## 9. Battle Factory rental pools

All Factory Pokémon come from `files/a/2/0/3`, by id range. A range is a
`BattleFactorySetRange` (`include/frontier/battle_factory_setup.h:12`), 8 bytes:
`u16 maxTrainerId, u16 minSetId, u16 maxSetId, u8 iv, u8 hasNextTier`. The tables are
raw bytes in `asm/frontier_script_commands_data.s`.

**Rentals** (6 to choose from) use row `round` (0-7) of
`gBattleFactoryLevel50SetRanges` (`:252`) or `gBattleFactoryOpenLevelRentalRanges`
(`:244`) (`BattleFactory_GetRentalSetRange`, `battle_factory_setup.c:124`).
**Opponents** use the first row whose `maxTrainerId` is above the trainer id, in
`gBattleFactoryLevel50SetRanges` or `gBattleFactoryOpenLevelTrainerSetRanges` (`:260`).
Each table has 10 rows (decoded):

| Row | `maxTrainerId` | Level 50: sets, IV | Open, rentals: sets, IV | Open, opponents: sets, IV |
|---:|---:|---|---|---|
| 0 | 100 | 1-150, 0 | 351-486, 0 | 351-486, 0 |
| 1 | 120 | 151-250, 4 | 487-622, 4 | 487-622, 4 |
| 2 | 140 | 251-350, 8 | 623-758, 8 | 623-758, 8 |
| 3 | 160 | 351-486, 12 | 759-894, 12 | 759-894, 12 |
| 4 | 180 | 487-622, 16 | 623-950, 16 | 351-950, 16 |
| 5 | 200 | 623-758, 20 | 623-950, 20 | 351-950, 20 |
| 6 | 220 | 759-894, 24 | 623-950, 24 | 351-950, 24 |
| 7 | 300 | 351-950, 31 | 351-950, 31 | 351-950, 31 |
| 8 | 310 | 351-486, 12 | 351-486, 12 | 351-486, 12 |
| 9 | 311 | 759-950, 31 | 759-950, 31 | 759-950, 31 |

Rows 0-6 have `hasNextTier` = 1; rows 7-9 have 0. Rows 8 and 9 are Thorton (309 < 310,
310 < 311). The Level 50 table serves both rentals and opponents.

**Picking** (`BattleFactory_PickSetIds`, `battle_factory_setup.c:134`): set id =
`maxSetId - random % (maxSetId - minSetId + 1)`, until the sets have different species
and different items (`ITEM_NONE` included) and avoid the excluded ones. The set's IV is
the row's `iv`.

**Trades push rentals up a tier.** With a trade count `t` above 0, the last *k* of the 6
rentals come from the **next row** (with that row's IV), where *k* is the first index of
`gBattleFactoryTradeCountTiers` `{6, 13, 20, 27, 34}` (`:224`) with `t <=` that value,
or 5 above 34 (`battle_factory_setup.c:148`-`163`). So 1-6 trades give 0, 7-13 give 1,
... 35+ give 5. Only rows with `hasNextTier` do this. The trade count is saved per type
and level mode (`BattleFactory_GetTradeCountStat`, `src/frontier_stat_ids.c`).

## 10. Battle Hall types and ranks

**The board.** `gBattleHallCellTypes` (`src/frontier/frontier_link_lobby.c:190`) maps the
board cursor to a type: cells 0-16 are the 17 types, entries 17-19 are `0xFE`, `0xFE` and
`TYPE_MYSTERY`. Any cursor of 17 or more is stored as cell 17
(`BattleHallData_ReadAppResult`, `battle_hall_data.c:199`). Each of the 18 cells has a
rank 0-10 kept in 4 bits (`HALL_CELL_COUNT`, `include/frontier/battle_hall_data.h:13`).
A won battle raises the chosen cell by one (`HALL_ACTION_RAISE_TYPE_RANK`,
`src/frontier/frontier_cmd_hall.c:225`). When all 17 type cells are at 10, they all drop
back to 9 (`BattleHallData_ResetMaxedRanks`, `battle_hall_data.c:413`). In the multi
type every cell is rank 9 (`battle_hall_data.c:134`).

**Trainers** (`BattleHall_PickTrainerClasses`, `battle_hall_setup.c:71`): a class is
picked, 8 in 12 times from the rank's 8 classes (`gBattleHallRankTrainerClasses`,
`asm/frontier_script_commands_data.s:297`) and 4 in 12 from the cell's 4 classes
(`gBattleHallCellTrainerClasses`, `:285`). Then `BattleHall_PickTrainerIds` (`:97`) finds
an unused trainer 0-299 of that class in **`gBattleHallTrainerClasses`** (`:310`, 300
entries). That table is a copy of the trainers' classes and differs from `a/2/0/2` for 11
trainers (Bird Keeper vs `BIRD_KEEPER_GS`, Scientist vs Super Nerd). The name and sprite
still come from `a/2/0/2`. Argenta replaces streak battles 50 and 170 of a single
challenge (`:108`-`115`).

**Sets** (`BattleHall_PickSetIds`, `battle_hall_setup.c:158`): from `files/a/2/0/4`,
starting at a random id in the rank's range and walking forward to the first set that has
the **cell's type** and isn't your species. The Hall does not read the sets' types from
the archive. It uses two tables that must agree with it: `gBattleHallSetSpecies`
(`asm/frontier_script_commands_data.s:350`, 477 entries, index = set id - 1) and
`gBattleHallSetTypes` (`:412`, two types per set). The species table matches the archive
for all 477 sets.

| Rank | 0-1 | 2-4 | 5-7 | 8-9 (10 counts as 9) |
|---|---|---|---|---|
| Hall set ids (`gBattleHallRankSetRanges`, `:280`) | 1-154 | 1-270 | 155-375 | 271-477 |
| IV (`gBattleHallRankIVs`, `:275`) | 8, 10 | 12, 14, 16 | 18, 20, 22 | 24, 26 |
| AI flags (`BattleHall_GetTrainerAIFlags`, `battle_hall_setup.c:394`) | 0 | 0 (rank 2), 1 | 1, 7 (rank 7) | 7 |

Argenta (`matron` 1 or 2) instead uses rank = your level / 10 and the range
`gBattleHallMatronSetRanges` (`:268`: 1-154, 155-270, 271-375) that contains your
species' own set, or 376-477 (`gBattleHallGoldMatronSetRange`, `:272`) for the gold
battle. Her Pokémon have IV 31 and your level.

**Opponent level** (`BattleHallData_CalcOpponentLevel`, `battle_hall_data.c:447`). With
your level `L` (the higher of your two in doubles, `BattleHall_GetPartyLevel`, `:424`)
and the cell's rank `r`:

```
level = ceil( L - 3*sqrt(L)  +  r*L / (5*sqrt(L))  +  (cells with a rank, counting this one, - 1) / 2 )
```

capped at `L` and at 100. If `L / (5*sqrt(L))` is below 1, the middle term is just `r`.
In multi it is `L`. Opponents are made from one set each and rerolled until not shiny
(`BattleHall_RerollPersonality`, `battle_hall_setup.c:312`).

## 11. Battle Castle CP

Castle Points are a saved stat per challenge type (`BattleCastle_GetPointsStat`).

- **Start of a challenge:** with no streak, CP and CP spent are set to 0 and the three
  ranks to 1 (`battle_castle_challenge.c:100`-`112`). Every new challenge then adds
  **10 CP** (`:125`).
- **After each battle** (`BattleCastleData_CalcPointsEarned`, `:448`;
  `CASTLE_ACTION_AWARD_POINTS`, `src/frontier/frontier_cmd_castle.c:276`):

| For | CP |
|---|---|
| each of your Pokémon still standing | 3 |
| ... at full HP | +3 |
| ... at half HP or more (not full) | +2 |
| ... below half | +1 |
| ... with no status | +1 |
| PP used in the battle: ≤5 / ≤10 / ≤15 | 8 / 6 / 4 (once) |
| each opponent you raised a level | 7 |

The total is at least 1, and CP caps at 9999 (`BattleCastle_AddPoints`, `:537`).

- **Spending** (`BattleCastle_SpendPoints`, `src/frontier/battle_castle_setup.c:347`):

| Action | CP | Where |
|---|---|---|
| check an opponent | 1 | `CASTLE_CP_CHECK`, `battle_castle_opponent_app.c:115` |
| see its stats / moves | 2 / 5 | `CASTLE_CP_STATS`, `CASTLE_CP_MOVES`, `:116`-`117` |
| raise the info rank | 50 | `CASTLE_CP_RANK_UP`, `:118` |
| opponent level +5 / -5 | 1 / 15 | `BattleCastleOpponentApp_GetLevelChangeCost`, `:1666` |
| restore HP / PP / all | 10 / 8 / 12 | `gBattleCastlePartyAppHealCosts`, `asm/battle_castle_data.s:57` |
| raise heal rank (to 2 / 3) | 100 / 100 | `gBattleCastlePartyAppRankUpCosts`, `:72` |
| raise rental rank (to 2 / 3) | 100 / 150 | `gBattleCastlePartyAppRentalRankUpCosts`, `:75` |
| rent an item | 5-20 | `gBattleCastleRentalItems` / `ItemCosts`, `:139` / `:145` (27 items) |
| rent a berry | 2 or 5 | `gBattleCastleRentalBerries` / `BerryCosts`, `:158` / `:165` (32 berries) |

How many items and berries are offered depends on the rental rank:
`gBattleCastlePartyAppItemCounts` (`:64`, 12 / 12 / 27) and
`gBattleCastlePartyAppBerryCounts` (`:54`, 8 / 8 / 32), indexed by rank - 1
(`battle_castle_party_app.c:1959`-`1962`). The level +5 / -5 comments are at
`battle_castle_opponent_app.c:100`-`103`.

## 12. Battle Arcade events

Before each battle the game board picks an event. `BattleArcade_ApplyEvent`
(`src/frontier/battle_arcade_data.c:741`) runs `sBattleArcadeEventFuncs[event]` (`:109`).
Events 0-8 act on the **opponent's** party, 9-17 on **yours**:

| Ids | Effect |
|---|---|
| 0 / 9 | HP to 80% (`BattleArcade_Event_LowerHp`, `:755`) |
| 1-5 / 10-14 | poison, paralysis, burn, sleep, freeze |
| 6 / 15 | all hold a berry: from 8, 20 or 10 berries by round <3, <6, 6+ (`:906`) |
| 7 / 16 | all hold an item: from 11, 13 or 11 items (`:929`) |
| 8 / 17 | +3 levels (`:952`) |
| 18-23 | weather or field for the battle: sun 1001, rain 1, sandstorm 7, hail 4, fog 9, Trick Room 1002 (`:969`-`991`) |
| 24 / 25 | board cursor faster / slower |
| 26 | random flag (`ctx->randomFlag`) |
| 27 | swap parties (handled in `battle_arcade_setup.c`, `ARCADE_EVENT_SWAP_PARTIES`) |
| 28-31 | nothing |

The item lists are `gBattleArcadeBerries_Rank0/3/6` and `gBattleArcadeItems_Rank0/3/6`
(`asm/frontier_script_commands_data.s:77`-`111`). Event colour is 0 for 0-8, 1 for 9-17,
2 for 18-26, 3 for 27+ (`BattleArcade_GetEventColor`, `battle_arcade_setup.c:311`).

**Which events appear.** `gBattleArcadeEventRoundFlags`
(`asm/battle_arcade_game_board_data.s:62`, one byte per event, one bit per round 0-6)
decides which events are in the pool, and `gBattleArcadeEventStreakFlags` (`:14`) limits
events 24-29 and 31 by streak. The colour of each of the 16 panels is drawn with
`gBattleArcadeEventColorOdds` (`:37`, 5 rows of 4). The row comes from a score of your
last battle: `gBattleArcadeEventColorThresholds` `{21, 16, 10, 5}` (`:9`,
`BattleArcadeGameBoard_CountEventColors`, `src/frontier/battle_arcade_game_board.c:1126`).
The score is `BattleArcade_GetWonBattlePoints` (`battle_arcade_data.c:478`), which
despite its name **is not BP**. It is `gBattleArcadeStatusedMonPoints[n]` (8, 6, 4, 0)
plus `gBattleArcadeFaintedMonPoints[n]` (6, 4, 2, 0) plus a bonus by turns taken (<3:
10, <5: 6, <7: 4, <9: 2) from `gBattleArcadeRankBattlePoints`
(`asm/frontier_script_commands_data.s:61`-`75`; called with `setup->totalTurns` in
`src/frontier/frontier_cmd_arcade.c:74`). The board's starting cursor speed depends on
the round (`gBattleArcadeRoundCursorSpeeds`, `:67`).

## 13. How-tos

### Unpacking the archives

The three archives have no extension and no JSON form. The build's `nitroarc` unpacks
and repacks them byte for byte (checked for `a/2/0/2`, `3` and `4`):

```sh
NARC=build/heartgold.us/tools/nitroarc/nitroarc
mkdir -p /tmp/bf && cp files/a/2/0/3 /tmp/bf/sets.narc
$NARC -xf /tmp/bf/sets.narc                 # -> /tmp/bf/sets.narc.d/00000.bin ... 00950.bin
# ... edit or add members ...
cd /tmp/bf && ls sets.narc.d | sort > order.txt
$NARC -cf /path/to/repo/files/a/2/0/3 -T order.txt sets.narc.d
```

Unpack a copy, never the file in `files/`. Members are read by number, so add new ones
at the end (`00951.bin`). See [graphics.md](graphics.md) for more on `nitroarc`.

### Change a set

A set is 16 little-endian bytes. This writes set 481 (Palmer's Dragonite) with new
moves and item:

```python
import struct
SPECIES_DRAGONITE, ITEM_CHOICE_BAND = 149, 220          # from include/constants/*.h
MOVE_OUTRAGE, MOVE_EXTREME_SPEED, MOVE_EARTHQUAKE, MOVE_FIRE_PUNCH = 200, 245, 89, 7
data = struct.pack('<5HBBHH', SPECIES_DRAGONITE,
                   MOVE_OUTRAGE, MOVE_EXTREME_SPEED, MOVE_EARTHQUAKE, MOVE_FIRE_PUNCH,
                   0b001010,     # EVs: Atk + Speed
                   3,            # nature: Adamant
                   ITEM_CHOICE_BAND, 0)
open('/tmp/bf/sets.narc.d/00481.bin', 'wb').write(data)
```

Check each number in `include/constants/species.h`, `moves.h` and `items.h` before
using it. The comments above are not a reference. Set 481 is also in other trainers'
lists; see the next recipe to avoid that.

### Add sets, or give a trainer new sets

1. Append the new sets to `a/2/0/3` as `00951.bin`, `00952.bin`...
2. In `a/2/0/2`, rewrite the trainer's member: class, count, ids, plus a `0` if the
   count is odd:

```python
import struct
ids = [951, 952, 953]
open('/tmp/bf/tr.narc.d/00305.bin', 'wb').write(
    struct.pack('<%dH' % (2 + len(ids) + len(ids) % 2), 97, len(ids), *ids, *([0] * (len(ids) % 2))))
# 97 = TRAINERCLASS_TOWER_TYCOON
```

Rules from the pickers ([§4](#4-how-opponents-are-chosen)):

- A Tower trainer needs at least as many **different species** as Pokémon it fields
  (3 in singles, 4 in doubles), or the loop in `BattleTower_PickTrainerMonSets` never
  ends.
- A Castle or Arcade trainer needs that many sets with different species **and different
  items** (`FrontierTrainer_PickMonSets`, `frontier_trainers.c:471`). Two sets with no
  item clash.
- The Factory picks by id range, so new sets beyond 950 are never rentals or Factory
  opponents unless you change the ranges.
- Linked Tower battles against a "version 0" partner use `a/1/2/8` / `a/1/2/9`.

**A new trainer** (id 315 and up) also needs a name at the end of `msg_0027.json`, three
lines at the end of `msg_0724.json`, and a range that can pick it: the Tower's tables in
`src/frontier_opponents.c:45` / `:122`, the Castle / Arcade C tables, the Factory's
`gBattleFactoryRoundTrainerRanges`. The Hall's search is fixed to trainers 0-299
(`HALL_TRAINER_COUNT_TOTAL`, `battle_hall_setup.c:40`).

### Change the Brain teams

| Brain | Edit |
|---|---|
| Palmer, Dahlia, Darach | the set list of trainer 305/306, 311/312, 313/314 in `a/2/0/2` (recipe above). Each needs at least 3 different species; Dahlia and Darach also 3 different items. |
| Thorton | rows 8 and 9 of `gBattleFactoryLevel50SetRanges` **and** `gBattleFactoryOpenLevelTrainerSetRanges` (`asm/frontier_script_commands_data.s:252`, `:260`): `minSetId`, `maxSetId`, `iv`. Keep enough different species and items in the range to also avoid all 3 of your rentals, since that rule is never dropped. |
| Argenta | the ranges at `asm/frontier_script_commands_data.s:268`-`274`, or the Hall sets inside them (and their rows in `gBattleHallSetSpecies` / `gBattleHallSetTypes`). |

The byte tables are little-endian. For example row 8 of the Level 50 table is
`0x36, 0x01, 0x5F, 0x01, 0xE6, 0x01, 0x0C, 0x00` = trainer < 310, sets 351-486, IV 12,
no next tier. To give Thorton (silver) a fixed trio, append three sets as 951-953 and
change that row (and the same row of the open-level table) to
`0x36, 0x01, 0xB7, 0x03, 0xB9, 0x03, 0x1F, 0x00` (sets 951-953, IV 31). With only three
sets, a rental of the same species or item would hang the picker, so give them species and
items that can't be rented.

The Brain's battle numbers are in C: `src/frontier_opponents.c:219`-`226` (Tower),
`battle_factory_setup.c:64`-`70`, `battle_castle_setup.c:61`-`66`,
`battle_arcade_setup.c:59`-`64`, `battle_hall_setup.c:108`-`115`. Changing them also
needs the matching BP checks (`winStreak == 21 || winStreak == 49` in each
`Get*BattlePoints` / round-value function) and the Factory's `FACTORY_ACTION_GET_BRAIN_BATTLE`
(`frontier_cmd_factory.c:361`).

### Change the banned species

To unban one, remove it from `sBattleFrontierBanlist` (`src/pokemon.c:4050`) and lower
`NUM_BANNED_BATTLE_FRONTIER` (`include/pokemon.h:31`). To ban more:

```diff
 // include/pokemon.h
-#define NUM_BANNED_BATTLE_FRONTIER 18
+#define NUM_BANNED_BATTLE_FRONTIER 19
 // src/pokemon.c, sBattleFrontierBanlist
     SPECIES_ARCEUS,
+    SPECIES_GARCHOMP,
 };
 // src/frontier_opponents.c:142 - one string slot per banned species, plus the count
-    messageFormat = MessageFormat_New_Custom(19, 14, HEAP_ID_FIELD1);
+    messageFormat = MessageFormat_New_Custom(NUM_BANNED_BATTLE_FRONTIER + 1, 14, HEAP_ID_FIELD1);
```

Then add one more "not eligible" message after the last one in each lobby's text
(Tower `msg_0096_D31R0201_00109`, Hall from 37, Castle and Arcade from 9), because the
message number is `base + species seen`. The new message must list one more
`{STRVAR_1 ...}` name. Shifting the messages after it renumbers them, so check the
scripts that use those ids. The list is also used by link battle rulesets
(`src/battle_regulation.c:134`). Arceus and the Spiky-eared Pichu check
(`src/pokemon.c:4077`) are separate.

### Change BP rewards

Edit the tables in [§8](#8-battle-points). They are plain C arrays, except the Arcade's,
which are bytes at `asm/frontier_script_commands_data.s:133` / `:137`. Also change the
"after the table" constant in the same function (for example `round >= 8 ? 9 :` in
`battle_factory_data.c:552`), and the 20 for the Brain battles. Prices are in the
exchange script, `sTutorMoves` and `scr_seq_0263.s` ([§8](#spending-bp)).

### Change rental pools

Edit the rows of `gBattleFactoryLevel50SetRanges` / `gBattleFactoryOpenLevelRentalRanges`
([§9](#9-battle-factory-rental-pools)), or the sets in those id ranges. A range needs at
least 6 different species with 6 different items, or the rental picker never finishes.
Keep in mind that the Level 50 table is also the opponents' table, and that trades pull
the last rentals from the next row.

## Checklist

- [ ] new sets appended at the end of `a/2/0/3` (or `a/2/0/4` plus both Hall tables)
- [ ] trainer members: class, count, ids, padding to 4 bytes
- [ ] enough different species (and items, for Castle/Arcade/Factory) for every picker
- [ ] names and lines in `msg_0027` / `msg_0724` for new trainers; a range that reaches them
- [ ] banlist count, message format size, one more message per lobby
- [ ] BP tables, their "after" constants and Brain-battle 20s
- [ ] repack with `nitroarc -cf ... -T order.txt`, then `make release`

## Not verified

- Nothing in this guide was tried in the game. No change was built.
- Only the unpack/repack of `files/a/2/0/2`, `3` and `4` with `nitroarc` was run, and
  it gave identical files. The Python snippets were not run against a real edit; check
  the constant values they use.
- The in-facility scripts (`files/a/1/8/2`) weren't read. When BP are given, which
  round index is used, how Palmer's defeat is recorded and how the Hall rank goes up are
  inferred from the C functions they call.
- That the Castle and Arcade "round table values" are the BP rewards is inferred from
  their numbers, not from a script.
- The trainer and set summaries ([§3](#3-trainers-and-sets), [§5](#5-frontier-brains))
  were dumped from the archives with a small script; species names come from
  `include/constants/species.h`.
- The meaning of `TOWER_MODE_6`, of "version 0" partners, and of the Hall board's cells
  17-19 wasn't traced.
- The pokeemerald names in the first table are from memory of that project, not checked
  against its code.
- The "picker never finishes" warnings come from reading the loops; no hang was
  produced.
- The Thorton row example and the banned-species diff weren't built.
