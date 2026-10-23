# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Undoable edits. Each command changes the MapDoc and tells the window what
to refresh through `changed(kind)` ("tiles", "events", "header")."""

from PySide6.QtGui import QUndoCommand


class _Cmd(QUndoCommand):
    def __init__(self, doc, changed, text):
        super().__init__(text)
        self.doc, self.changed = doc, changed


class PaintTiles(_Cmd):
    """One brush stroke, already painted: {(x, y): (old, new)}, each (collision, behavior, attr)."""

    def __init__(self, doc, changed, tiles, text="Paint tiles"):
        super().__init__(doc, changed, text)
        self.old = {xy: o for xy, (o, n) in tiles.items()}
        self.new = {xy: n for xy, (o, n) in tiles.items()}
        self._first = True

    def _apply(self, values):
        for (x, y), (c, b, a) in values.items():
            self.doc.set_tile(x, y, collision=c, behavior=b, attr=a)
        self.changed("tiles", list(values))

    def redo(self):
        if self._first:  # the stroke already painted while dragging
            self._first = False
            self.changed("tiles", list(self.new))
            return
        self._apply(self.new)

    def undo(self):
        self._apply(self.old)


class MoveEvent(_Cmd):
    def __init__(self, doc, changed, section, index, old_xy, new_xy):
        super().__init__(doc, changed, "Move event")
        self.section, self.index, self.old, self.new = section, index, old_xy, new_xy

    def redo(self):
        self.doc.move_event(self.section, self.index, *self.new)
        self.changed("events", None)

    def undo(self):
        self.doc.move_event(self.section, self.index, *self.old)
        self.changed("events", None)


class SetEventField(_Cmd):
    def __init__(self, doc, changed, section, index, key, value):
        super().__init__(doc, changed, "Set %s" % key)
        self.section, self.index, self.key, self.new = section, index, key, value
        self.old = doc.events(section)[index].get(key)

    def redo(self):
        self.doc.set_event_field(self.section, self.index, self.key, self.new)
        self.changed("events", None)

    def undo(self):
        self.doc.set_event_field(self.section, self.index, self.key, self.old)
        self.changed("events", None)


class AddEvent(_Cmd):
    def __init__(self, doc, changed, section, x, y, template=None):
        super().__init__(doc, changed, "Add event")
        self.section, self.x, self.y, self.template = section, x, y, template
        self.index = None
        self.event = None

    def redo(self):
        self.index = self.doc.add_event(self.section, self.x, self.y, self.event or self.template, self.index)
        self.event = self.doc.events(self.section)[self.index]
        self.changed("events", (self.section, self.index))

    def undo(self):
        self.doc.remove_event(self.section, self.index)
        self.changed("events", None)


class RemoveEvent(_Cmd):
    def __init__(self, doc, changed, section, index):
        super().__init__(doc, changed, "Delete event")
        self.section, self.index = section, index
        self.event = None

    def redo(self):
        self.event = self.doc.remove_event(self.section, self.index)
        self.changed("events", None)

    def undo(self):
        self.doc.add_event(self.section, self.event["x"], self.event["y"], self.event, self.index)
        self.changed("events", (self.section, self.index))


class SetHeaderField(_Cmd):
    def __init__(self, doc, changed, key, value):
        super().__init__(doc, changed, "Set %s" % key)
        self.key, self.new = key, value
        self.old = doc.data.get(key)

    def redo(self):
        self.doc.set_header_field(self.key, self.new)
        self.changed("header", None)

    def undo(self):
        self.doc.set_header_field(self.key, self.old)
        self.changed("header", None)
