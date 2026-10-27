# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""The map view: layout cells drawn top-down (behavior colors, collision,
grid), props as markers and events as draggable boxes, objects as their
overworld sprites. One scene unit is one pixel; a tile is TILE pixels, and a
sprite texel is one pixel too (a 32x32 NPC is two tiles wide)."""

import colorsys
import zlib

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsScene, QGraphicsView

from .project import CELL
from .sprites import SpriteImages, pose
from .terrain import TerrainRenderer

TILE = 16

# Colors for behaviors that matter most when reading a map; the rest get a stable hashed color.
BEHAVIOR_COLORS = {
    0x00: QColor(236, 236, 228),                     # normal ground
    0x02: QColor(96, 176, 72), 0x03: QColor(56, 136, 48),     # tall / very tall grass
    0x06: QColor(150, 120, 80),                      # headbutt tree
    0x08: QColor(170, 150, 120),                     # cave floor
    0x10: QColor(90, 140, 220), 0x15: QColor(60, 110, 210),   # river / sea
    0x11: QColor(40, 60, 160), 0x13: QColor(120, 170, 255),   # whirlpool / waterfall
    0x16: QColor(150, 190, 230), 0x17: QColor(170, 210, 235),  # puddle / shallow water
    0x20: QColor(200, 240, 250), 0x21: QColor(230, 210, 150),  # ice / sand
    0xFF: QColor(60, 60, 60),                        # none
}
EVENT_COLORS = {
    "object_events": QColor(40, 120, 230),
    "warp_events": QColor(200, 40, 200),
    "coord_events": QColor(40, 170, 70),
    "bg_events": QColor(230, 170, 20),
}
EVENT_LABELS = {"object_events": "O", "warp_events": "W", "coord_events": "T", "bg_events": "S"}


def behavior_color(b):
    if b in BEHAVIOR_COLORS:
        return BEHAVIOR_COLORS[b]
    h = (zlib.crc32(bytes([b])) % 360) / 360.0
    r, g, bl = colorsys.hsv_to_rgb(h, 0.45, 0.92)
    return QColor(int(r * 255), int(g * 255), int(bl * 255))


class CellItem(QGraphicsItem):
    """One layout cell (32x32 tiles). Images are cached and rebuilt when its land data changes."""

    def __init__(self, view, cx, cy):
        super().__init__()
        self.view, self.cx, self.cy = view, cx, cy
        self.setPos(cx * CELL * TILE, cy * CELL * TILE)
        self.setZValue(0)
        self._behavior = self._collision = None
        self._terrain = None

    def boundingRect(self):
        return QRectF(0, 0, CELL * TILE, CELL * TILE)

    def invalidate(self, terrain=False):
        self._behavior = self._collision = None
        if terrain:
            self._terrain = None
        self.update()

    def _terrain_image(self):
        if self._terrain is None:
            v = self.view
            chunk = v.doc.chunk(self.cx, self.cy)
            self._terrain = v.renderer.render_cell(chunk.number, v.doc.area_for_cell(self.cx, self.cy), chunk.props,
                                                   v.doc.cell_altitude(self.cx, self.cy))
        return self._terrain

    def _images(self):
        chunk = self.view.doc.chunk(self.cx, self.cy)
        if self._behavior is None:
            beh = QImage(CELL, CELL, QImage.Format_RGB32)
            col = QImage(CELL, CELL, QImage.Format_ARGB32)
            col.fill(Qt.transparent)
            for ty in range(CELL):
                for tx in range(CELL):
                    c, b, a = chunk.tile(tx, ty)
                    beh.setPixelColor(tx, ty, behavior_color(b))
                    if c:
                        col.setPixelColor(tx, ty, QColor(220, 30, 30, 110))
            self._behavior, self._collision = beh, col
        return self._behavior, self._collision

    def paint(self, p, option, widget=None):
        v = self.view
        size = CELL * TILE
        if v.doc.chunk(self.cx, self.cy) is None:
            return
        beh, col = self._images()
        target = QRectF(0, 0, size, size)
        if v.layers["terrain"]:
            p.fillRect(target, QColor(24, 24, 28))
            p.drawImage(target, self._terrain_image())
            if v.layers["behavior"]:
                p.setOpacity(0.5)
                p.drawImage(target, beh)
                p.setOpacity(1.0)
        elif v.layers["behavior"]:
            p.drawImage(target, beh)
        else:
            p.fillRect(target, QColor(236, 236, 228))
        if v.layers["collision"]:
            p.drawImage(target, col)
        if v.layers["grid"] and v.transform().m11() * TILE >= 6:
            p.setPen(QPen(QColor(0, 0, 0, 40), 0))
            for i in range(1, CELL):
                p.drawLine(i * TILE, 0, i * TILE, size)
                p.drawLine(0, i * TILE, size, i * TILE)
        if v.doc.cell_map(self.cx, self.cy) != v.doc.map.id:
            p.fillRect(target, QColor(0, 0, 0, 110))  # another map's cell
        p.setPen(QPen(QColor(0, 0, 0, 160), 0))
        p.drawRect(target)
        if v.layers["cells"]:
            p.setFont(QFont("monospace", 9))
            p.drawText(QPointF(4, 12), "cell %d,%d  land %04d" % (self.cx, self.cy, v.doc.cell_land(self.cx, self.cy)))


class PropItem(QGraphicsItem):
    def __init__(self, cx, cy, index, prop, tx, ty):
        super().__init__()
        self.info = (cx, cy, index, prop)
        self.setPos(tx * TILE, ty * TILE)
        self.setZValue(5)
        self.setToolTip("prop %d in cell %d,%d: model %d\nposition %s\nrotation %s\nscale %s" % (
            index, cx, cy, prop["model"], prop["position"], prop["rotation"], prop["scale"]))

    def boundingRect(self):
        return QRectF(-5, -5, 10, 10)

    def paint(self, p, option, widget=None):
        p.setPen(QPen(QColor(90, 60, 20), 0))
        p.setBrush(QColor(240, 200, 120, 200))
        p.drawPolygon([QPointF(0, -5), QPointF(5, 0), QPointF(0, 5), QPointF(-5, 0)])


class EventItem(QGraphicsObject):
    """A draggable event. Dragging moves every selected event; the one under the mouse
    emits moved([(section, index, old_xy, new_xy)]) for all of them when dropped."""

    moved = Signal(list)

    def __init__(self, section, index, event, sprite=None, sprite_note=None):
        """sprite: QImage drawn for an object instead of its box; sprite_note: why an
        object has none (shown in the tooltip)."""
        super().__init__()
        self.section, self.index, self.ev = section, index, event
        self.sprite, self.sprite_note = sprite, sprite_note
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        # objects further south are drawn over those north of them, as in the game
        self.setZValue(10 + (event["y"] / 100000.0 if sprite is not None else 0))
        self.setPos(event["x"] * TILE, event["y"] * TILE)
        self.setToolTip(self.describe())
        self._start = None

    def describe(self):
        e = self.ev
        name = {"object_events": "%s  %s" % (e.get("local_id"), e.get("graphics_id")),
                "warp_events": "warp %d -> %s:%s" % (self.index, e.get("dest_map"), e.get("dest_warp_id")),
                "coord_events": "trigger %s == %s" % (e.get("var"), e.get("var_value")),
                "bg_events": "%s" % e.get("type")}[self.section]
        text = "%s  (%d, %d, elevation %s)\nscript: %s" % (name, e["x"], e["y"], e.get("elevation"), e.get("script"))
        if self.sprite_note:
            text += "\nsprite not shown: %s" % self.sprite_note
        return text

    def sprite_rect(self):
        """Where the sprite is drawn: centred on the tile, its bottom on the tile's bottom."""
        w, h = self.sprite.width(), self.sprite.height()
        return QRectF((TILE - w) / 2, TILE - h, w, h)

    def size(self):
        if self.section == "coord_events":
            return max(1, self.ev.get("width", 1)), max(1, self.ev.get("height", 1))
        return 1, 1

    def boundingRect(self):
        w, h = self.size()
        r = QRectF(-1, -1, w * TILE + 2, h * TILE + 2)
        return r.united(self.sprite_rect()) if self.sprite is not None else r

    def shape(self):
        # clicks select by the event's tiles, so a tall sprite doesn't cover the tile north of it
        path = QPainterPath()
        w, h = self.size()
        path.addRect(QRectF(0, 0, w * TILE, h * TILE))
        return path

    def paint(self, p, option, widget=None):
        w, h = self.size()
        color = EVENT_COLORS[self.section]
        if self.sprite is not None:
            p.drawImage(self.sprite_rect(), self.sprite)
            p.setBrush(Qt.NoBrush)
            if self.isSelected():
                p.setPen(QPen(QColor(255, 255, 0), 2))
            else:
                outline = QColor(color)
                outline.setAlpha(160)
                p.setPen(QPen(outline, 1))
            p.drawRect(QRectF(0, 0, TILE, TILE))
            return
        fill = QColor(color)
        fill.setAlpha(90 if self.section == "coord_events" else 200)
        p.setBrush(QBrush(fill))
        p.setPen(QPen(QColor(255, 255, 0) if self.isSelected() else color.darker(150), 2 if self.isSelected() else 1))
        p.drawRect(QRectF(0, 0, w * TILE, h * TILE))
        p.setPen(Qt.white)
        p.setFont(QFont("sans", 7, QFont.Bold))
        label = EVENT_LABELS[self.section]
        if self.section == "object_events" and self.sprite_note:
            label = "V" if self.sprite_note.startswith("set when") else "?"
        p.drawText(QRectF(0, 0, TILE, TILE), Qt.AlignCenter, label)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)   # updates the selection first
        for it in self.scene().selectedItems():
            if isinstance(it, EventItem):
                it._start = (it.ev["x"], it.ev["y"])
        self._start = (self.ev["x"], self.ev["y"])

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return QPointF(round(value.x() / TILE) * TILE, round(value.y() / TILE) * TILE)
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        items = {it for it in self.scene().selectedItems() if isinstance(it, EventItem)} | {self}
        moves = []
        for it in items:
            new = (int(round(it.x() / TILE)), int(round(it.y() / TILE)))
            if it._start is not None and new != it._start:
                moves.append((it.section, it.index, it._start, new))
            it._start = None
        if moves:
            self.moved.emit(sorted(moves))


ANIMATION_MS = 150   # one animation tick: a walk-cycle frame


class MapView(QGraphicsView):
    """Tools: "select" (events), "collision" (left: block, right: open), "behavior"
    (left: paint, right: pick). Emits hovered(x, y), stroke({xy: (old, new)}) after a
    stroke has been painted, picked(behavior)."""

    hovered = Signal(int, int)
    ticked = Signal()        # animated sprites changed frame
    stroke = Signal(dict)
    picked = Signal(int)
    context = Signal(int, int, object)   # tile x, y, global QPoint

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing, False)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setMouseTracking(True)
        self.setBackgroundBrush(QColor(40, 40, 46))
        self.doc = None
        self.tool = "select"
        self.brush_behavior = 0
        self.brush_size = 1
        self.layers = {"terrain": True, "behavior": False, "collision": True, "grid": True, "props": False,
                       "events": True, "sprites": True, "animate": True, "cells": False}
        self.renderer = None
        self.sprites = None
        self.tick = 0
        self._clock = QTimer(self)
        self._clock.setInterval(ANIMATION_MS)
        self._clock.timeout.connect(self._advance)
        self.cells = {}
        self.event_items = []
        self.prop_items = []
        self._stroke = None
        self._panning = None

    # --- content ----------------------------------------------------------------

    def set_doc(self, doc):
        self.doc = doc
        if doc is not None and (self.renderer is None or self.renderer.root != doc.repo.root):
            self.renderer = TerrainRenderer(doc.repo.root)
            self.sprites = SpriteImages(doc.repo.root)
        self.scene().clear()
        self.cells, self.event_items, self.prop_items = {}, [], []
        if doc is None:
            return
        x0, y0, x1, y1 = doc.bounds()
        # one ring of neighbouring cells for context (outdoor layouts)
        x0, y0 = max(0, x0 - 1), max(0, y0 - 1)
        x1, y1 = min(doc.width - 1, x1 + 1), min(doc.height - 1, y1 + 1)
        for cy in range(y0, y1 + 1):
            for cx in range(x0, x1 + 1):
                if doc.cell_land(cx, cy) is not None:
                    item = CellItem(self, cx, cy)
                    self.scene().addItem(item)
                    self.cells[(cx, cy)] = item
        self.scene().setSceneRect(QRectF(x0 * CELL * TILE, y0 * CELL * TILE,
                                         (x1 - x0 + 1) * CELL * TILE, (y1 - y0 + 1) * CELL * TILE).adjusted(-64, -64, 64, 64))
        self.rebuild_props()
        self.rebuild_events()
        own = doc.own_cells() or list(self.cells)
        cx, cy = sum(c[0] for c in own) / len(own), sum(c[1] for c in own) / len(own)
        self.centerOn((cx + 0.5) * CELL * TILE, (cy + 0.5) * CELL * TILE)

    def rebuild_props(self):
        for it in self.prop_items:
            self.scene().removeItem(it)
        self.prop_items = []
        if not self.layers["props"]:
            return
        for cx, cy, i, p, tx, ty in self.doc.props():
            if (cx, cy) in self.cells:
                it = PropItem(cx, cy, i, p, tx, ty)
                self.scene().addItem(it)
                self.prop_items.append(it)

    def rebuild_events(self, select=None):
        # no selectionChanged while the items are replaced: the selection would read as
        # empty for a moment and the window would clear the event form
        blocked = self.scene().blockSignals(True)
        try:
            for it in self.event_items:
                self.scene().removeItem(it)
            self.event_items = []
            if not self.layers["events"]:
                return
            for section in ("coord_events", "bg_events", "warp_events", "object_events"):
                for i, ev in enumerate(self.doc.events(section)):
                    sprite = note = None
                    if section == "object_events":
                        note = self.sprites.why_not(ev.get("graphics_id"))
                        if note is None and self.layers["sprites"]:
                            sprite = self.sprite_for(ev)
                    it = EventItem(section, i, ev, sprite, note)
                    it.moved.connect(self._event_moved)
                    self.scene().addItem(it)
                    self.event_items.append(it)
                    if select == (section, i):
                        it.setSelected(True)
                        self.ensureVisible(it)
        finally:
            self.scene().blockSignals(blocked)
        self._update_clock()

    # --- sprite animation ---------------------------------------------------------

    def sprite_for(self, ev):
        """The object's sprite now: its pose at the current tick, or standing facing
        facing_dir when animation is off."""
        g = ev.get("graphics_id")
        if not self.layers["animate"]:
            return self.sprites.image(g, ev.get("facing_dir"))
        facing, step = pose(ev.get("movement_type"), ev.get("facing_dir"), self.sprites.frames(g), self.tick)
        return self.sprites.image(g, facing, step)

    def _update_clock(self):
        run = self.layers["animate"] and any(it.sprite is not None for it in self.event_items)
        if run and not self._clock.isActive():
            self._clock.start()
        elif not run:
            self._clock.stop()

    def _advance(self):
        self.tick += 1
        changed = False
        for it in self.event_items:
            if it.sprite is not None:
                img = self.sprite_for(it.ev)
                if img is not None and img is not it.sprite:
                    it.sprite = img
                    it.update()
                    changed = True
        if changed:
            self.ticked.emit()

    def _event_moved(self, moves):
        self.window().move_events(moves)

    def refresh_terrain(self):
        """Redraw every cell's terrain (after the area changes)."""
        for it in self.cells.values():
            it.invalidate(terrain=True)

    def refresh_tiles(self, tiles=None):
        """Rebuild the cells whose land data changed (every cell sharing it)."""
        if tiles is None:
            for it in self.cells.values():
                it.invalidate()
            return
        numbers = {self.doc.cell_land(x // CELL, y // CELL) for x, y in tiles}
        for (cx, cy), it in self.cells.items():
            if self.doc.cell_land(cx, cy) in numbers:
                it.invalidate()

    def selected_event(self):
        for it in self.scene().selectedItems():
            if isinstance(it, EventItem):
                return it.section, it.index
        return None

    # --- mouse --------------------------------------------------------------------

    def tile_at(self, pos):
        s = self.mapToScene(pos)
        return int(s.x() // TILE), int(s.y() // TILE)

    def zoom(self, f):
        if 0.05 <= self.transform().m11() * f <= 8:
            self.scale(f, f)

    def wheelEvent(self, e):
        self.zoom(1.25 if e.angleDelta().y() > 0 else 0.8)

    def _brush_tiles(self, x, y):
        r = self.brush_size // 2
        return [(x + dx, y + dy) for dy in range(-r, self.brush_size - r) for dx in range(-r, self.brush_size - r)]

    def _paint_at(self, pos, button):
        x, y = self.tile_at(pos)
        changed = []
        for tx, ty in self._brush_tiles(x, y):
            cur = self.doc.tile(tx, ty)
            if cur is None or not self.doc.on_map(tx, ty):   # neighbours belong to other maps
                continue
            c, b, a = cur
            if self.tool == "collision":
                new = (0 if button == Qt.RightButton else 1, b, a)
            else:
                new = (c, self.brush_behavior, a)
            if new != cur:
                old = self._stroke[(tx, ty)][0] if (tx, ty) in self._stroke else cur
                self._stroke[(tx, ty)] = (old, new)
                self.doc.set_tile(tx, ty, collision=new[0], behavior=new[1], attr=new[2])
                changed.append((tx, ty))
        if changed:
            self.refresh_tiles(changed)

    def mousePressEvent(self, e):
        if e.button() == Qt.MiddleButton:
            self._panning = e.position()
            self.setCursor(Qt.ClosedHandCursor)
            return
        if self.doc and self.tool != "select" and e.button() in (Qt.LeftButton, Qt.RightButton):
            if self.tool == "behavior" and e.button() == Qt.RightButton:
                t = self.doc.tile(*self.tile_at(e.position().toPoint()))
                if t:
                    self.picked.emit(t[1])
                return
            self._stroke = {}
            self._stroke_button = e.button()
            self._paint_at(e.position().toPoint(), e.button())
            return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._panning is not None:
            d = e.position() - self._panning
            self._panning = e.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(d.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(d.y()))
            return
        if self.doc:
            self.hovered.emit(*self.tile_at(e.position().toPoint()))
        if self._stroke is not None:
            self._paint_at(e.position().toPoint(), self._stroke_button)
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._panning is not None and e.button() == Qt.MiddleButton:
            self._panning = None
            self.setCursor(Qt.ArrowCursor)
            return
        if self._stroke is not None:
            stroke, self._stroke = self._stroke, None
            if stroke:
                self.stroke.emit(stroke)
            return
        super().mouseReleaseEvent(e)

    def contextMenuEvent(self, e):
        if self.doc and self.tool == "select":
            x, y = self.tile_at(e.pos())
            self.context.emit(x, y, e.globalPos())
