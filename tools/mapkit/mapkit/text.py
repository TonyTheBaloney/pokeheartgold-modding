# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
"""msgenc JSON text banks (files/msgdata/msg/msg_NNNN[_CODE].json)."""

import json
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
