#!/usr/bin/env python3
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-23
"""Run: python3 tools/sound/test_sound.py   (about a minute: it packs the whole archive)"""

import hashlib
import json
import math
import os
import shutil
import struct
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbnk  # noqa: E402
import sdat  # noqa: E402
import sseq  # noqa: E402
import swar  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SOUND = os.path.join(ROOT, "sound")
SOUND_DATA = os.path.join(SOUND, "sound_data.json")
HEADER = os.path.join(ROOT, "include/constants/sndseq.h")
RETAIL_SHA1 = "1ea1ac174ea25f28a2446bee1b8b7be4d4ca1264"  # heartgold.us/filesystem.sha1 (same in SoulSilver)


def notes_of(sseq_bytes):
    """Per track: sorted (tick, key, velocity, length), the way the sound driver plays them."""
    cmds, start = sseq.parse_sseq(sseq_bytes)
    starts, by_off = sseq.track_starts(cmds, start)
    out = []
    for tr in sorted(starts):
        events, _, loop = sseq.play_track(cmds, by_off, starts[tr], start)
        out.append((sorted((t, c.op, c.args[0], c.args[1]) for t, c in events if c.op < 0x80 and not c.prefix), loop))
    return out


def midi_bytes(tracks, division=96, tempo_bpm=150, loop=None):
    """A format-1 MIDI file. tracks: list of (channel, program, [(start, key, vel, length)]) in quarter/division ticks."""
    meta = [(0, b"\xFF\x51\x03" + round(60_000_000 / tempo_bpm).to_bytes(3, "big"))]
    if loop:
        meta += [(loop[0], b"\xFF\x06\x09loopStart"), (loop[1], b"\xFF\x06\x07loopEnd")]
    mtracks = [meta]
    for ch, prog, notes in tracks:
        evs = [(0, bytes([0xC0 | ch, prog])), (0, bytes([0xB0 | ch, 7, 100]))]
        for t, k, v, n in notes:
            evs += [(t, bytes([0x90 | ch, k, v])), (t + n, bytes([0x80 | ch, k, 0]))]
        mtracks.append(evs)
    return sseq.write_midi(mtracks, division)


class Archive(unittest.TestCase):
    def test_pack_is_retail(self):
        tmp = tempfile.mkdtemp()
        try:
            out = os.path.join(tmp, "a.sdat")
            sdat.pack(SOUND_DATA, out, os.path.join(tmp, "a.d"), HEADER)
            with open(out, "rb") as f:
                self.assertEqual(hashlib.sha1(f.read()).hexdigest(), RETAIL_SHA1)
        finally:
            shutil.rmtree(tmp)

    def test_header_matches(self):
        with open(HEADER) as f:
            self.assertEqual(f.read(), sdat.header_text(sdat.load_doc(SOUND_DATA)))


class Formats(unittest.TestCase):
    """Every retail sequence, bank and 8-bit wave archive survives a round trip."""

    @classmethod
    def setUpClass(cls):
        cls.doc = sdat.load_doc(SOUND_DATA)

    def files(self, key):
        return sorted({e["file"] for e in self.doc[key] if e is not None})

    def read(self, rel):
        with open(os.path.join(SOUND, rel), "rb") as f:
            return f.read()

    def test_sequences_reassemble(self):
        for rel in self.files("sequences"):
            data = self.read(rel)
            cmds, _ = sseq.parse_sseq(data)
            self.assertEqual(sseq.build_sseq(b"".join(c.encode() for c in cmds)), data, rel)

    def test_sequences_through_midi(self):
        for rel in self.files("sequences")[::10]:  # a sample: the full run takes a while
            data = self.read(rel)
            try:
                again = sseq.midi_to_sseq(sseq.sseq_to_midi(data))
            except sseq.SseqError:
                continue  # no notes
            a = [n for n in notes_of(data) if n[0]]
            b = [n for n in notes_of(again) if n[0]]
            loop = a[0][1]
            clip = (lambda ns: [(t, k, v, max(1, min(n, loop[1] - t))) for t, k, v, n in ns if t < loop[1]]) if loop else (lambda ns: ns)
            self.assertEqual([sorted(clip(x[0])) for x in a], [x[0] for x in b], rel)

    def test_banks_through_json(self):
        for rel in self.files("banks"):
            a = sbnk.parse_sbnk(self.read(rel))
            self.assertEqual(sbnk.parse_sbnk(sbnk.build_sbnk(json.loads(sbnk.dump_json(a)))), a, rel)

    def test_pcm8_wave_archives_through_wav(self):
        tmp = tempfile.mkdtemp()
        try:
            for rel in self.files("waveArchives"):
                data = self.read(rel)
                waves = swar.parse_swar(data)
                if not waves or any(w["format"] != 0 for w in waves) or any(w["timer"] != swar.TIMER_CLOCK // w["rate"] for w in waves):
                    continue
                swar.extract(os.path.join(SOUND, rel), tmp)
                stem = os.path.splitext(os.path.basename(rel))[0]
                self.assertEqual(swar.build_bytes(os.path.join(tmp, stem + ".json")), data, rel)
        finally:
            shutil.rmtree(tmp)


class Adpcm(unittest.TestCase):
    def test_sine(self):
        s = [round(12000 * math.sin(i * 2 * math.pi * 440 / 22050)) for i in range(4000)]
        back = swar.adpcm_decode(swar.adpcm_encode(s), len(s))
        err = sum((a - b) ** 2 for a, b in zip(s, back)) / sum(a * a for a in s)
        self.assertGreater(10 * math.log10(1 / err), 25)


class NewSong(unittest.TestCase):
    """A new song from MIDI, with its own bank and wave archive from a WAV, packed into
    a copy of the archive the way docs/modding/music.md describes."""

    def test_new_song(self):
        tmp = tempfile.mkdtemp()
        try:
            base = os.path.join(tmp, "sound")
            shutil.copytree(SOUND, base)
            os.makedirs(os.path.join(base, "songs"), exist_ok=True)
            os.makedirs(os.path.join(base, "samples"), exist_ok=True)

            # a sample: one second of a decaying 440 Hz tone, looped from 0.5 s
            rate = 22050
            tone = [round(16000 * math.exp(-i / 20000) * math.sin(i * 2 * math.pi * 440 / rate)) for i in range(rate)]
            with wave.open(os.path.join(base, "samples/tone.wav"), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(rate)
                w.writeframes(b"".join(struct.pack("<h", v) for v in tone))
            with open(os.path.join(base, "wave_archives/WAVE_ARC_TEST.json"), "w") as f:
                json.dump({"waves": [{"file": "../samples/tone.wav", "format": "adpcm", "loopStart": rate // 2}]}, f)
            with open(os.path.join(base, "banks/BANK_TEST.json"), "w") as f:
                json.dump({"instruments": [
                    {"program": 0, "type": "pcm", "archive": 0, "sample": 0, "key": 69},
                    {"program": 1, "type": "psg", "duty": 3, "key": 69},
                ]}, f)
            melody = [(i * 48, 60 + (i * 5) % 12, 100, 40) for i in range(16)]
            bass = [(i * 192, 36 + (i % 2) * 7, 90, 180) for i in range(4)]
            with open(os.path.join(base, "songs/test.mid"), "wb") as f:
                f.write(midi_bytes([(0, 0, melody), (1, 1, bass)], loop=(0, 768)))

            doc = sdat.load_doc(os.path.join(base, "sound_data.json"))
            doc["waveArchives"].append({"name": "WAVE_ARC_TEST", "file": "wave_archives/WAVE_ARC_TEST.json"})
            doc["banks"].append({"name": "BANK_TEST", "file": "banks/BANK_TEST.json",
                                 "waveArchives": ["WAVE_ARC_TEST", None, None, None]})
            # music goes in an empty slot below SEQ_GS_P_START (see docs/modding/music.md)
            self.assertIsNone(doc["sequences"][4])
            doc["sequences"][4] = {"name": "SEQ_TEST", "file": "songs/test.mid", "bank": "BANK_TEST",
                                   "volume": 100, "channelPriority": 64, "playerPriority": 64,
                                   "player": "PLAYER_FIELD"}
            with open(os.path.join(base, "sound_data.json"), "w") as f:
                f.write(sdat.dump_json(doc))
            sdat.write_header(os.path.join(base, "sound_data.json"), os.path.join(tmp, "sndseq.h"))
            out = os.path.join(tmp, "new.sdat")
            dep = os.path.join(tmp, "new.d")
            sdat.pack(os.path.join(base, "sound_data.json"), out, dep, os.path.join(tmp, "sndseq.h"))

            with open(out, "rb") as f:
                back, files = sdat.read_sdat(f.read())
            seq = back["sequences"][4]
            self.assertEqual(seq["name"], "SEQ_TEST")
            self.assertEqual(seq["bank"], "BANK_TEST")
            with open(os.path.join(tmp, "sndseq.h")) as f:
                self.assertRegex(f.read(), r"#define SEQ_TEST +4\n")

            # the sequence plays the MIDI's notes (MIDI ticks 96/quarter -> 48)
            tracks = notes_of(files[seq["file"]])
            played = [n for n, _ in tracks if n]
            self.assertEqual(played[0], sorted((t // 2, k, v, n // 2) for t, k, v, n in melody))
            self.assertEqual(played[1], sorted((t // 2, k, v, n // 2) for t, k, v, n in bass))
            self.assertEqual(tracks[0][1], (0, 384))  # loops back to the start after 2 bars

            bank = sbnk.parse_sbnk(files[back["banks"][-1]["file"]])
            self.assertEqual([i["type"] for i in bank["instruments"]], ["pcm", "psg"])
            wav = swar.parse_swar(files[back["waveArchives"][-1]["file"]])
            self.assertEqual((wav[0]["format"], wav[0]["rate"], wav[0]["loop"]), (2, rate, 1))
            decoded, loop = swar.decode_swav(wav[0])
            self.assertEqual(loop, rate // 2 - (rate // 2) % 8)  # moved to an 8-sample boundary
            err = sum((a - b) ** 2 for a, b in zip(tone, decoded)) / sum(a * a for a in tone)
            self.assertGreater(10 * math.log10(1 / err), 25)

            with open(dep) as f:
                deps = f.read()
            for src in ("songs/test.mid", "banks/BANK_TEST.json", "wave_archives/WAVE_ARC_TEST.json", "samples/tone.wav"):
                self.assertIn(os.path.join(base, src) if src != "samples/tone.wav" else "tone.wav", deps)
        finally:
            shutil.rmtree(tmp)

    def test_bad_midi_is_reported(self):
        with self.assertRaises(sseq.SseqError):
            sseq.midi_to_sseq(b"not a midi")


if __name__ == "__main__":
    unittest.main()
