<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Save data

> AI-generated, local to this fork. Do not upstream.

A HeartGold/SoulSilver save is 42 fixed-size **chunks** packed into a 140 KiB
region of the cartridge's 512 KiB flash, plus six **extra chunks** (Hall of
Fame, Battle Frontier records, battle videos) in fixed sectors after it. The
main region is full to the sector: **35 of 35 sectors** are used, with 2,520
bytes of slack in block 0 and 3,312 in block 1. Any change to a chunk's size
moves everything after it, so **existing save files stop loading**. There is no
version field to migrate them.

`python3 tools/savemap/savemap.py [build/heartgold.us]` prints the current
layout from a build (sizes read from the compiled game, like pokeemerald's
"Saveblock Size" check). SoulSilver's layout is identical.

Code: `src/save.c` (layout, reading, writing), `src/save_arrays.c` (the chunk
tables), `include/constants/save_arrays.h` (chunk ids, `SAVE_PAGE_MAX`).

## Flash layout

The flash is 4 Mbit (512 KiB), in two halves of 64 sectors (4 KiB each). Each
half holds a complete copy of the save; the game writes the copy that is
**not** the last good one, so a failed write leaves the other intact.

| Sectors (in each half) | Contents |
|---|---|
| 0-34 | main save: block 0 (bytes `0x00000`-`0x0F627`), block 1 (`0x0F700`-`0x21A0F`), free to `0x22FFF` |
| 35-37 | extra 0: Hall of Fame (10,928 bytes) |
| 38 | extra 1: Battle Frontier species records (2,976 bytes) |
| 39-46 | extras 2-5: four saved battle videos (7,504 bytes each, two sectors each) |
| 47-63 | **unused** (68 KiB per half) |

The second half starts at flash offset `0x40000`. Hall of Fame is written to
both halves; the Frontier records and battle videos are "keyed": each save
goes to one half, alternating, with the key and last half kept in the main
save (`SAVE_MISC`, `extraChunkKeys`).

## How the main save is built

1. Each chunk's size comes from its `*_sizeof` function, rounded up to 4 bytes,
   **plus 4 bytes** whose first two hold a CRC-16 of the chunk
   (`GetSaveChunkSizePlusCRC`; checked by `SaveSubstruct_AssertCRC`).
2. Chunks are packed in id order. Block 0 is chunks 0-40; block 1 is the PC
   (chunk 41). Each block ends with a 16-byte footer (`struct SaveChunkFooter`:
   save count, size, magic `0x20060623`, block, CRC), and block 1 starts on the
   next 256-byte boundary.
3. Each block is counted in whole sectors, and the total must fit
   `SAVE_PAGE_MAX` (35): block 0 = 16, block 1 = 19 (`SaveData_InitSlotSpecs`
   asserts this at boot).
4. The whole region is also kept in RAM: `SaveData.dynamic_region` (140 KiB,
   `HEAP_ID_1`) for the whole game, and loading reads both copies into two more
   140 KiB buffers (`HEAP_ID_3`).

PC boxes are saved incrementally: each box is exactly one sector (30 × 136 bytes
+ 16 padding = 4,096), and only boxes marked modified are written
(`boxModifiedFlag`, one bit per box).

## Chunks

Sizes are as compiled (before the +4 CRC rounding); offsets are within the
save region.

| # | Chunk | Block | Bytes | Offset | Holds |
|---|---|---|---|---|---|
| 0 | `SAVE_SYSINFO` | 0 | 92 | `0x00000` | RTC offset and setup, DS MAC address, birthday, Wi-Fi profile ID |
| 1 | `SAVE_PLAYERDATA` | 0 | 44 | `0x00060` | options, player profile (name, ID, money, badges), coins, play time |
| 2 | `SAVE_PARTY` | 0 | 1456 | `0x00090` | party (6 × `Pokemon`, 236 bytes each) |
| 3 | `SAVE_BAG` | 0 | 1948 | `0x00644` | bag: 8 pockets, 486 item slots |
| 4 | `SAVE_FLAGS` | 0 | 1100 | `0x00DE4` | event vars and flags |
| 5 | `SAVE_LOCAL_FIELD_DATA` | 0 | 128 | `0x01234` | current, previous and entrance positions, warps |
| 6 | `SAVE_POKEDEX` | 0 | 832 | `0x012B8` | Pokédex seen/caught bits, form and language data |
| 7 | `SAVE_DAYCARE` | 0 | 480 | `0x015FC` | Day-Care Pokémon, egg |
| 8 | `SAVE_PALPAD` | 0 | 2176 | `0x017E0` | Pal Pad friends |
| 9 | `SAVE_MISC` | 0 | 736 | `0x02064` | apricorn trees, berry pots, gym puzzle state, rival name, extra-chunk keys, ... |
| 10 | `SAVE_MAP_OBJECTS` | 0 | 5120 | `0x02348` | saved overworld objects |
| 11 | `SAVE_LINK_BATTLE_RULESET` | 0 | 32 | `0x0374C` | link battle rules |
| 12 | `SAVE_DRESSUP_DATA` | 0 | 2100 | `0x03770` | Dress-up (fashion) data |
| 13 | `SAVE_MAILBOX` | 0 | 1120 | `0x03FA8` | PC mailbox |
| 14 | `SAVE_FRIEND_GROUP` | 0 | 264 | `0x0440C` | friend group |
| 15 | `SAVE_TRAINER_CARD` | 0 | 1568 | `0x04518` | Trainer Card (signature, ...) |
| 16 | `SAVE_GAMESTATS` | 0 | 448 | `0x04B3C` | game statistics counters |
| 17 | `SAVE_SEAL_CASE` | 0 | 368 | `0x04D00` | Ball Capsule seals |
| 18 | `SAVE_CHATOT` | 0 | 1004 | `0x04E74` | Chatot's recorded cry |
| 19 | `SAVE_UNK_19` | 0 | 5672 | `0x05264` | Battle Frontier (`Save_Frontier`) |
| 20 | `SAVE_SPECIAL_RIBBONS` | 0 | 14 | `0x06890` | special ribbons |
| 21 | `SAVE_ROAMER` | 0 | 104 | `0x068A4` | roaming Pokémon |
| 22 | `SAVE_GTS` | 0 | 248 | `0x06910` | GTS deposit |
| 23 | `SAVE_UNK_23` | 0 | 3016 | `0x06A0C` | `SaveBlock23` (record mixing lists) |
| 24 | `SAVE_RANKINGS` | 0 | 3744 | `0x075D8` | rankings |
| 25 | `SAVE_UNK_25` | 0 | 2240 | `0x0847C` | friend roster |
| 26 | `SAVE_WIFI_HISTORY` | 0 | 4088 | `0x08D40` | Wi-Fi trade history (countries) |
| 27 | `SAVE_MYSTERY_GIFT` | 0 | 5760 | `0x09D3C` | Mystery Gift cards/events |
| 28 | `SAVE_UNK_28` | 0 | 1672 | `0x0B3C0` | Pal Park migration (`MigratedPokemon`) |
| 29 | `SAVE_POKEATHLON_FRIENDSHIP_RECORDS` | 0 | 40 | `0x0BA4C` | Pokéathlon friendship records |
| 30 | `SAVE_EASY_CHAT` | 0 | 8 | `0x0BA78` | easy chat words |
| 31 | `SAVE_UNK_31` | 0 | 64 | `0x0BA84` | Wii message |
| 32 | `SAVE_PLAZA_SURVEY` | 0 | 8 | `0x0BAC8` | Wi-Fi Plaza survey |
| 33 | `SAVE_FOLLOW_MON` | 0 | 8 | `0x0BAD4` | following Pokémon |
| 34 | `SAVE_POKEGEAR` | 0 | 1624 | `0x0BAE0` | Pokégear (phone contacts, map, ...) |
| 35 | `SAVE_SAFARI_ZONE` | 0 | 1532 | `0x0C13C` | Safari Zone layout |
| 36 | `SAVE_PHOTO_ALBUM` | 0 | 4756 | `0x0C73C` | photo album |
| 37 | `SAVE_POKEATHLON` | 0 | 2944 | `0x0D9D4` | Pokéathlon |
| 38 | `SAVE_APRICORN_BOX` | 0 | 128 | `0x0E558` | Apricorn Box |
| 39 | `SAVE_POKEWALKER` | 0 | 308 | `0x0E5DC` | Pokéwalker |
| 40 | `SAVE_TRAINER_HOUSE` | 0 | 3840 | `0x0E714` | Trainer House |
| 41 | `SAVE_PCSTORAGE` | 1 | 74492 | `0x0F700` | PC: 18 boxes × 30 `BoxPokemon` (136 bytes), box names, wallpapers |

## What's in the chunks modders touch most

**Vars and flags** (`SAVE_FLAGS`, 1,100 bytes, `include/save_vars_flags.h`):
368 vars (`NUM_VARS` = `0x170`, ids `0x4000`-`0x416F`) and 2,912 flags
(`NUM_FLAGS`). Not saved: temporary flags (`0x4000`+, 64, kept in RAM in
`src/save_vars_flags.c`) and special vars (`0x8000`-`0x800D`).

| Flag range | Use (`include/constants/flags.h`) |
|---|---|
| `0x001`-`0x040` | map-temporary flags (`MAPTEMP_FLAG_BASE`, 64) |
| `0x041`-`0x31F` | story and event flags |
| `0x320`-`0x406` | hidden items (`HIDDEN_ITEMS_FLAG_BASE` = 800, 231) |
| `0x407`-`0x54F` | more event flags |
| `0x550`-`0xA9F` | trainers defeated (`TRAINER_FLAG_BASE`, by trainer id) |
| `0xAA0`-`0xB5F` | daily flags (`DAILY_FLAG_BASE`, 192, reset each day) |

1,137 flags are still named `FLAG_UNK_*` and 251 vars `VAR_UNK_*`. Many are
used by scripts or code under that name; which ones are truly free hasn't been
checked yet. Reusing a free one costs nothing; adding more grows the chunk.

**Pokédex** (`SAVE_POKEDEX`, 832 bytes, `include/pokedex.h`): bit arrays sized by
`NUM_DEX_FLAG_WORDS` = ceil((493 + 8) / 32) = 16 words each for caught, seen and
seen-gender ×2, plus per-species caught languages (`ROUND_UP(493, 4)` bytes) and
form/Unown order lists.

**Bag** (`SAVE_BAG`, 1,948 bytes): 486 slots of 4 bytes (item id, quantity):
Items 165, Medicine 40, Balls 24, TMs/HMs 101, Berries 64, Mail 12, Battle
items 30, Key items 50 (`NUM_BAG_*` in `include/constants/items.h`).

**Player** (`SAVE_PLAYERDATA`, 44 bytes, `include/player_data.h`): options,
`PlayerProfile` (name of 7 characters + terminator, trainer ID, money, gender,
language, Johto and Kanto badges as 8-bit masks, game-clear and National Dex
bits), coins, play time.

**Party and PC**: the party is `PARTY_SIZE` (6) full `Pokemon` (236 bytes:
`BoxPokemon` plus battle stats); the PC (74,492 bytes) is 18 boxes of 30
`BoxPokemon` (136 bytes, encrypted with the personality value), then the current
box, modified flags, box names (20 characters), wallpapers and `0x11` bytes of
filler.

## What common mods cost

| Change | Save effect |
|---|---|
| Use an unused `FLAG_UNK_*` / `VAR_UNK_*` | none |
| More flags or vars (`NUM_FLAGS`, `NUM_VARS`) | `SAVE_FLAGS` grows (1 byte per 8 flags, 2 per var); block 0 has 2,520 bytes of slack |
| Bigger bag pockets (`NUM_BAG_*`) | 4 bytes per slot in `SAVE_BAG` |
| New items | none (ids are 16-bit) unless pockets grow |
| New species | `SAVE_POKEDEX` grows with `NATIONAL_DEX_COUNT` (bits plus a byte per species for languages); also species-indexed archives and the Frontier species records (extra chunk 1) |
| More PC boxes (`NUM_BOXES`) | 4,096 bytes per box in block 1 (only 3,312 free: needs `SAVE_PAGE_MAX` raised); `boxModifiedFlag` has 32 bits |
| Bigger party (`PARTY_SIZE`) | 236 bytes per slot in block 0, and many screens assume 6 |
| A new chunk | add an id before `SAVE_PCSTORAGE` in `constants/save_arrays.h` (keep `SAVE_BLOCK_NUM` last) and a row in `gSaveChunkHeaders` in the same order |

**Raising `SAVE_PAGE_MAX`.** The extra chunks are placed at
`SAVE_PAGE_MAX + n`, so they move with it; they end at sector `SAVE_PAGE_MAX +
12`, which must stay within the half's 64 sectors. That allows up to 52 (17
more sectors, 68 KiB). Each sector also costs 4 KiB of `HEAP_ID_1` for the
whole game and 8 KiB of `HEAP_ID_3` while loading; check those heaps have room.
Moving the extra chunks loses saved Hall of Fame and battle videos too.

**Compatibility.** The game finds chunks by computed offset and checks each
block's footer (size, magic, CRC), so a save from a different layout fails
those checks and is treated as corrupted. Start a new game after any layout change, or
keep the layout by only reusing unused space (free flags and vars, `filler`
and `dummy` fields).
