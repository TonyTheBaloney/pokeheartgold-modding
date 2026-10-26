# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
"""msgenc JSON text banks (files/msgdata/msg/msg_NNNN[_CODE].json)."""

import json
import re
import struct
from dataclasses import dataclass


@dataclass
class TextBank:
    path: str
    key: int
    messages: list  # list of dicts: {"id": ..., "en_US": str | [str]}

    @property
    def ids(self):
        return [m.get("id") for m in self.messages]

    def get(self, msg_id):
        for m in self.messages:
            if m.get("id") == msg_id:
                return m
        return None

    @staticmethod
    def text_of(message, lang="en_US"):
        t = message.get(lang, "")
        return "".join(t) if isinstance(t, list) else str(t)


def load(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return TextBank(path, d.get("key"), d.get("messages", []))


# --- line width ----------------------------------------------------------

CHARMAP = "tools/msgenc/charmap.txt"
MESSAGE_FONT = "files/graphic/font/font_00000001.bin"  # FONT_MESSAGE, the dialogue font
DIALOG_WIDTH = 216  # DIALOG_BOX_W (27 tiles) in src/dialog_box.c
# {STRVAR_1 K, ...} labels -> the bank of names a slot with that label holds
SLOT_BANKS = {0: "msg_0237", 1: "msg_0237", 4: "msg_0279", 5: "msg_0720", 6: "msg_0750",
              13: "msg_0443", 14: "msg_0730", 15: "msg_0735", 17: "msg_0044"}
NAME_PX = 7 * 6  # PLAYER_NAME_LENGTH letters of 6 px (K 3: player, rival, trainer)


class Widths:
    """Pixel width of text in the dialogue font: glyph widths from the font file's
    width table (character code c is glyph c - 1); the font has no letter spacing."""

    def __init__(self, charmap_path, font_path):
        self.chars = {}
        with open(charmap_path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.rstrip("\r\n")
                if "=" not in line or line.startswith("//"):
                    continue
                code, ch = line.split("=", 1)
                if not ch.startswith("{"):
                    self.chars[ch] = int(code, 16)
        with open(font_path, "rb") as f:
            d = f.read()
        start, count = struct.unpack_from("<II", d, 4)
        self.glyphs = d[start:start + count]
        self.slots = {}  # K -> px added for a {STRVAR_n K, ...}

    def add_slot_widths(self, banks, item_names=()):
        """Count each placeholder as the longest name its label can hold: the widest
        message in SLOT_BANKS[K] (`banks` maps a bank name to its TextBank), the widest
        item name for K 8, NAME_PX for K 3. Other labels (numbers ...) count as 0."""
        self.slots[3] = NAME_PX
        for k, base in SLOT_BANKS.items():
            if base in banks:
                self.slots[k] = max((self.width(TextBank.text_of(m)) for m in banks[base].messages), default=0)
        if item_names:
            self.slots[8] = max(self.width(n) for n in item_names)

    def width(self, value):
        return max(px for _, px in self.lines(value))

    def char(self, code):
        if 0 < code <= len(self.glyphs):
            return self.glyphs[code - 1]
        return self.glyphs[428 - 1]  # drawn as "?" (GetGlyphWidth_VariableWidth)

    def lines(self, value):
        """[(line, px)] for each line of a message (split at \\n, \\r and \\f).
        Codes add nothing, except {CURSOR_X n} (moves to x = n) and raw {XXXX} codes;
        {STRVAR_n K, ...} counts as the longest name for K (add_slot_widths), else 0."""
        out = []
        for line in re.split(r"[\n\r\f]", value):
            x = 0
            for m in re.finditer(r"\{([^}]*)\}|(.)", line, re.S):
                if m.group(2) is not None:
                    x += self.char(self.chars.get(m.group(2), 0))
                    continue
                parts = m.group(1).split(" ", 1)
                if parts[0].startswith("STRVAR_") and len(parts) > 1:
                    k = parts[1].split(",")[0].strip()
                    x += self.slots.get(int(k), 0) if k.isdigit() else 0
                elif parts[0] == "CURSOR_X" and len(parts) > 1 and parts[1].strip().isdigit():
                    x = int(parts[1])
                elif re.fullmatch(r"[0-9A-Fa-f]{4}", parts[0]):
                    x += self.char(int(parts[0], 16))
            out.append((line, x))
        return out
