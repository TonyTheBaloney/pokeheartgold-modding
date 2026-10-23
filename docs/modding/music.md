<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-23 -->

# Music and sound

> AI-generated, local to this fork. Do not upstream.

All music, sound effects and cries are in one Nintendo sound archive (SDAT). It used
to be a binary file; it is now built from `sound/`, the way pokeemerald builds its
sound data from `sound/`. Unchanged files give back the retail archive byte for byte
(both versions pass `make`'s checksums).

| pokeemerald | here |
|---|---|
| `sound/songs/midi/*.mid` + `midi.cfg`, built by `mid2agb` | `.mid` files named in `sound/sound_data.json`, converted by `tools/sound/sseq.py` |
| `sound/song_table.inc` (song → music player) | `"sequences"` in `sound/sound_data.json` (sequence → bank, volume, player) |
| `include/constants/songs.h` (`MUS_*`, `SE_*`) | `include/constants/sndseq.h` (`SEQ_*`), written by `tools/sound/sdat.py header` |
| `sound/voicegroups/*.inc` (program → instrument) | banks: `sound/banks/*.sbnk`, or a `.json` you write |
| `sound/direct_sound_samples/*.wav` | wave archives: `sound/wave_archives/*.swar`, or a `.json` listing `.wav` files |
| `"music": "MUS_..."` in `map.json` | `"music_day"`, `"music_night"` in `map.json` |

What the DS adds: up to 16 tracks per song, sampled instruments with envelopes plus
square-wave (PSG) and noise channels, and a bank can split an instrument across key
ranges or give each key its own sound (drum sets).

## What's in `sound/`

```
sound/sound_data.json        the index: every sequence, bank, wave archive, player, group
sound/sequences/*.sseq       1231 songs, sound effects and cries (binary)
sound/banks/*.sbnk           561 instrument banks (binary)
sound/wave_archives/*.swar   561 sample sets (binary)
```

`sound_data.json` has one entry per line. Each list is in id order: a sequence's
`SEQ_*` value is its position in `"sequences"`, and `null` keeps an empty slot's id.

```json
{"name": "SEQ_GS_T_WAKABA", "file": "sequences/SEQ_GS_T_WAKABA.sseq", "bank": "BANK_BGM_FIELD1",
 "volume": 80, "channelPriority": 30, "playerPriority": 64, "player": "PLAYER_FIELD"}
```

| Field | Meaning |
|---|---|
| `file` | the sequence; several entries can share one file (a few unused ids point at Route 29's song) |
| `bank` | the instrument bank its program numbers refer to |
| `volume` | 0-127 |
| `channelPriority` | which notes lose a hardware channel first when all 16 are busy (music uses 30) |
| `playerPriority` | which sequence wins a player |
| `player` | `PLAYER_FIELD` for map music, `PLAYER_BGM` for other music (battles, events), `PLAYER_ME` for jingles, `PLAYER_SE_*` for sound effects |

A bank entry lists the (up to 4) wave archives its instruments take samples from.

The binary files can't be read as text, but the tools can show them:

```sh
python3 tools/sound/sseq.py dump sound/sequences/SEQ_GS_T_WAKABA.sseq      # every command
python3 tools/sound/sseq.py to-midi sound/sequences/SEQ_GS_T_WAKABA.sseq new_bark.mid
python3 tools/sound/sbnk.py to-json sound/banks/BANK_BGM_FIELD1.sbnk         # its instruments
python3 tools/sound/swar.py extract sound/wave_archives/WAVE_ARC_BGM_FIELD1.swar out/   # WAVs + JSON
```

## Changing which music plays

| Where | How |
|---|---|
| a map | `music_day`, `music_night` in `data/maps/<Map>/map.json` ([maps-and-warps.md](maps-and-warps.md#map-header-top-of-mapjson)); chosen in `FieldBGM_GetForMapHeader` (`src/field_bgm.c`). Surfing plays `SEQ_GS_NAMINORI` instead |
| a script | `playbgm(SEQ_X)`; `fadeoutbgm`, `resetbgm` and friends in `asm/macros/script.inc` |
| a trainer | eyes-meet and battle music tables, see [trainer-classes.md](trainer-classes.md) |
| a wild battle, evolution, ... | the `SEQ_*` in the C code that plays it (`grep -rn SEQ_GS_VS_ src`) |

## Adding a song

### 1. The MIDI

Put it in `sound/songs/` (any name). The conversion (`tools/sound/sseq.py from-midi`)
keeps:

- notes, with velocity and length;
- program changes (the program number picks an instrument in the song's bank);
- volume (CC7), pan (CC10), expression (CC11), modulation (CC1), pitch bend, and
  bend range (RPN 0);
- tempo changes;
- a loop: MIDI markers or text events `loopStart` and `loopEnd` (or `[` and `]`).
  Without `loopEnd`, the loop ends at the last note. Without `loopStart`, the song
  plays once.

Each MIDI channel with notes becomes one track (at most 16). Channel 10 is not drums
by itself; drums are a drum-set instrument in the bank. Time is converted to 48 ticks
per quarter note, so anything finer than a 1/192 note is rounded.

To see how the game's songs are written, convert one to MIDI (`sseq.py to-midi`) and
open it in a MIDI editor.

### 2. Its entry

Replace a `null` in `"sequences"` **between `SEQ_PV_END` (3) and `SEQ_DUMMY` (1000)**
with the new entry:

```json
{"name": "SEQ_MY_TOWN", "file": "songs/my_town.mid", "bank": "BANK_BGM_FIELD1",
 "volume": 100, "channelPriority": 30, "playerPriority": 64, "player": "PLAYER_FIELD"}
```

Don't add songs at the end of the list. `Sound_SetCurrentBGM` (`src/sound_system.c:60`)
treats any id above `SEQ_GS_P_START` (1217) as a GB Sounds track, and the ids 4-999
are all free.

The bank decides how the song sounds. Reuse a bank whose instruments fit
(`sbnk.py to-json` lists them; `BANK_BGM_FIELD1` is the town and route bank), and use
its program numbers in the MIDI. For your own instruments, see
[New instruments](#new-instruments).

### 3. The constant

```sh
python3 tools/sound/sdat.py header sound/sound_data.json include/constants/sndseq.h
```

This writes `#define SEQ_MY_TOWN 4`. The build stops if `sndseq.h` is out of date
with `sound_data.json`.

### 4. Use it, and build

Set `"music_day": "SEQ_MY_TOWN"` on a map (or `playbgm` it), then `make release`. The
MIDI is converted during the build; changing it rebuilds the archive.

## New instruments

### Samples: a wave archive

List WAV files in a JSON file and point a wave archive entry at it:

```json
{
    "waves": [
        {"file": "../samples/flute.wav", "format": "adpcm"},
        {"file": "../samples/strings.wav", "format": "adpcm", "loopStart": 11025}
    ]
}
```

| Field | Meaning |
|---|---|
| `file` | a WAV (8/16/24/32-bit PCM, any rate, stereo is mixed to mono), relative to the JSON file |
| `format` | `adpcm` (4 bits a sample, what the game uses for music; default), `pcm8` (what it uses for cries), `pcm16` |
| `loopStart` | sample where the loop starts; it loops to the end. Default: the WAV's own loop (`smpl` chunk), else none. `"loop": false` ignores a WAV loop |
| `rate` | use this sample rate instead of the WAV's (at most 65535) |

The loop start moves to the nearest 4-byte boundary below it (8 samples for ADPCM).
The ADPCM encoder runs in Python, so a long sample takes a few seconds to build.

```json
{"name": "WAVE_ARC_MY_TOWN", "file": "wave_archives/WAVE_ARC_MY_TOWN.json"}
```

Wave archives and banks can go at the end of their lists; nothing in the code checks
their ids.

### Instruments: a bank

A bank is pokeemerald's voicegroup: an instrument for each program number.

```json
{
    "instruments": [
        {"program": 0, "type": "pcm", "archive": 0, "sample": 0, "key": 72},
        {"program": 1, "type": "pcm", "archive": 0, "sample": 1, "key": 60, "release": 100},
        {"program": 2, "type": "psg", "duty": 3, "key": 69},
        {"program": 3, "type": "keySplit", "regions": [
            {"upTo": 59, "type": "pcm", "archive": 0, "sample": 2, "key": 48},
            {"upTo": 127, "type": "pcm", "archive": 0, "sample": 3, "key": 72}]},
        {"program": 4, "type": "drumSet", "first": 36, "keys": [
            {"type": "pcm", "archive": 1, "sample": 0, "key": 60},
            {"type": "pcm", "archive": 1, "sample": 1, "key": 60, "pan": 40}]}
    ]
}
```

| Field | Meaning |
|---|---|
| `type` | `pcm` (a sample), `psg` (square wave; `duty` 0-7 = 12.5%-87.5%), `noise`, `keySplit` (up to 8 key ranges, each up to and including `upTo`), `drumSet` (one instrument per key from `first`) |
| `archive`, `sample` | which of the bank's wave archives (0-3), and which sample in it |
| `key` | the MIDI note at which the sample plays at its recorded pitch (60 = middle C) |
| `attack`, `decay`, `sustain`, `release` | envelope, 0-127; default 127, 127, 127, 120 |
| `pan` | 0 left, 64 centre, 127 right |

```json
{"name": "BANK_MY_TOWN", "file": "banks/BANK_MY_TOWN.json",
 "waveArchives": ["WAVE_ARC_MY_TOWN", "WAVE_ARC_BASIC", null, null]}
```

A bank can mix your wave archive with the game's (here `WAVE_ARC_BASIC` is archive 1).
To start from a game bank, `sbnk.py to-json` it and edit the result.

## Limits

| Limit | Value | Where |
|---|---|---|
| tracks per song | 16 | the format |
| ids for new music | 4-999 (below `SEQ_GS_P_START`) | `src/sound_system.c:60` |
| sequence size on `PLAYER_FIELD` | 15,500 bytes (largest retail: 14,668); the build checks every player with its own heap | `"heapSize"` in `sound_data.json` |
| sound heap (bank + samples + sequence loaded at once) | 0xBEAE0 = 781,024 bytes, shared with sound effects and cries | `SND_HEAP_SIZE`, `include/sound.h` |
| wave archives per bank | 4 | the format |
| hardware channels | 16: PSG only on 8-13, noise only on 14-15; music players may use the channels in their `"channels"` mask | the DS |
| sample rate | 65535 Hz | the format |

The GB Sounds item plays a Game Boy version of 136 songs (`src/sound_gb.c`); a new song
has none, so it plays normally with GB Sounds on.

## The tools

| Command | Does |
|---|---|
| `sdat.py pack sound/sound_data.json OUT.sdat` | build the archive (the build runs this) |
| `sdat.py unpack ARCHIVE.sdat DIR` | split an archive into `sound/`'s layout |
| `sdat.py header sound/sound_data.json include/constants/sndseq.h` | write the constants |
| `sseq.py from-midi / to-midi / dump` | sequences |
| `sbnk.py build / to-json` | banks |
| `swar.py build / extract` | wave archives |
| `python3 tools/sound/test_sound.py` | checks: the archive rebuilds byte for byte; every sequence, bank and 8-bit wave archive round-trips; a new song from MIDI, WAV, bank and wave archive packs and plays the right notes |

How the formats were checked: every retail sequence disassembles and reassembles
byte for byte, and plays the same notes after a trip through MIDI; every bank gives
the same instruments after a trip through JSON; every 8-bit wave archive comes back
byte for byte from WAV. The command set and its defaults come from the sound driver's
source (`subprojects/NitroSDK-4.2.30001/libraries/snd/src/ARM7/snd_seq.c`).

## Not verified

- No new song has been played in game yet; the checks are on the files.
- How much room a custom bank has: it must fit the sound heap together with what the
  game keeps loaded (sound effects, cries). The game's largest wave archive is 431 KB;
  staying under that is probably safe.
- The MIDI conversion ignores sustain pedal, portamento and other controllers.
