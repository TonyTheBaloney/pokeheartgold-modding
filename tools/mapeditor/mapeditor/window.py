# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Main window: map list | map view | properties (event, header, tiles)."""

import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QUndoStack
from PySide6.QtWidgets import (QCompleter, QDockWidget, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
                               QScrollArea, QSpinBox, QTabWidget, QVBoxLayout, QWidget)

from . import commands as C
from . import project
from .canvas import MapView, behavior_color
from .project import CELL

# map.json key -> constant prefix offered as completions
COMPLETIONS = {
    "graphics_id": "SPRITE_", "movement_type": "MOVEMENT_TYPE_", "facing_dir": "DIR_",
    "trainer_type": "OBJECT_TYPE_", "flag": "FLAG_", "dest_map": "MAP_", "var": "VAR_",
    "type": "BG_TYPE_", "player_facing_dir": "BG_DIR_", "music_day": "SEQ_", "music_night": "SEQ_",
    "region_map_section": "MAPSEC_", "weather": "WEATHER_", "map_type": "MAP_TYPE_",
    "battle_scene": "BATTLE_BG_", "camera_type": "CAMERA_TYPE_",
}
# header keys shown but not editable here, with the reason
READ_ONLY = {"layout": "the layout can't be changed while the map is open: edit map.json and reopen"}
SECTION_NAMES = {"object_events": "Object", "warp_events": "Warp", "coord_events": "Trigger", "bg_events": "Sign/BG"}


def parse_value(text, old):
    """Text from a field -> JSON value of the same kind as the old one where possible."""
    t = text.strip()
    if isinstance(old, bool):
        return t.lower() in ("1", "true", "yes")
    try:
        return int(t, 0)
    except ValueError:
        pass
    if t.startswith(("[", "{")):
        try:
            return json.loads(t)
        except ValueError:
            pass
    return t


def show_value(v):
    return json.dumps(v) if isinstance(v, (list, dict, bool)) else str(v)


class FieldForm(QWidget):
    """A form of key -> line edit; calls on_edit(key, value) when a field is changed.
    on_edit returns False to refuse the value, which puts the old text back."""

    def __init__(self, repo, on_edit, read_only=None):
        super().__init__()
        self.repo, self.on_edit = repo, on_edit
        self.read_only = read_only or {}
        self.form = QFormLayout(self)
        self.form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.values = {}
        self.edits = {}
        self.title = None
        self._completers = {}

    def _completer(self, prefix):
        if prefix not in self._completers:
            c = QCompleter(project.constant_names(self.repo, prefix), self)
            c.setCaseSensitivity(Qt.CaseInsensitive)
            c.setFilterMode(Qt.MatchContains)
            self._completers[prefix] = c
        return self._completers[prefix]

    def set_fields(self, title, fields):
        keys = [k for k, _ in fields]
        if title == self.title and keys == list(self.edits):
            # same rows: update the texts in place, so the field being edited (which may be
            # the one whose signal got us here) isn't deleted and keeps the focus
            self.values = dict(fields)
            for key, value in fields:
                if self.edits[key].text() != show_value(value):
                    self.edits[key].setText(show_value(value))
            return
        while self.form.rowCount():
            self.form.removeRow(0)
        self.title, self.values, self.edits = title, dict(fields), {}
        if title:
            self.form.addRow(QLabel("<b>%s</b>" % title))
        for key, value in fields:
            edit = QLineEdit(show_value(value))
            if key in self.read_only:
                edit.setReadOnly(True)
                edit.setToolTip(self.read_only[key])
            elif key in COMPLETIONS:
                edit.setCompleter(self._completer(COMPLETIONS[key]))
            edit.editingFinished.connect(lambda k=key, e=edit: self._finished(k, e))
            self.form.addRow(key, edit)
            self.edits[key] = edit

    def _finished(self, key, edit):
        if edit.isReadOnly():
            return
        old = self.values.get(key)
        new = parse_value(edit.text(), old)
        if new == old:
            return
        if self.on_edit(key, new) is False:
            edit.setText(show_value(old))
        else:
            self.values[key] = new

    def check(self, key, value):
        """An error message if value isn't one of the field's constants, else None.
        Numbers are always accepted; fields whose constants aren't known aren't checked."""
        if key not in COMPLETIONS or not isinstance(value, str):
            return None
        names = project.constant_names(self.repo, COMPLETIONS[key])
        if names and value not in names:
            return "%s is not a %s* constant" % (value, COMPLETIONS[key])
        return None


class MainWindow(QMainWindow):
    def __init__(self, repo, start_map=None):
        super().__init__()
        self.repo = repo
        self.doc = None
        self.undo = QUndoStack(self)
        self.undo.cleanChanged.connect(lambda clean: self._update_title())
        self.behaviors = project.behavior_names(repo.root)

        self.view = MapView(self)
        self.view3d = None            # created on first use (needs OpenGL)
        self._3d_stale = True
        self.center = QTabWidget()
        self.center.addTab(self.view, "Map")
        self.center.addTab(QWidget(), "3D")
        self.center.currentChanged.connect(self._center_tab_changed)
        self.setCentralWidget(self.center)
        self.view.hovered.connect(self._hovered)
        self.view.stroke.connect(self._stroke)
        self.view.picked.connect(self._pick_behavior)
        self.view.context.connect(self._context_menu)
        self.view.scene().selectionChanged.connect(self._selection_changed)

        self._build_map_list()
        self._build_properties()
        self._build_actions()
        self.status = QLabel()
        self.statusBar().addWidget(self.status, 1)
        self.resize(1500, 950)
        self._update_title()
        if start_map:
            self.open_map(start_map)

    # --- layout of the window -------------------------------------------------------

    def _build_map_list(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        self.map_filter = QLineEdit(placeholderText="Filter maps...")
        self.map_list = QListWidget()
        lay.addWidget(self.map_filter)
        lay.addWidget(self.map_list)
        for folder, name, mid in project.map_list(self.repo):
            it = QListWidgetItem(folder)
            it.setToolTip("%s (%d)" % (name, mid))
            it.setData(Qt.UserRole, folder)
            self.map_list.addItem(it)
        self.map_filter.textChanged.connect(self._filter_maps)
        self.map_list.itemActivated.connect(lambda it: self.open_map(it.data(Qt.UserRole)))
        self.map_list.itemDoubleClicked.connect(lambda it: self.open_map(it.data(Qt.UserRole)))
        dock = QDockWidget("Maps", self)
        dock.setWidget(w)
        dock.setObjectName("maps")
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def _filter_maps(self, text):
        t = text.lower()
        for i in range(self.map_list.count()):
            it = self.map_list.item(i)
            it.setHidden(t not in it.text().lower() and t not in it.toolTip().lower())

    def _build_properties(self):
        self.tabs = QTabWidget()
        self.event_form = FieldForm(self.repo, self._event_field_edited)
        self.header_form = FieldForm(self.repo, self._header_field_edited, READ_ONLY)
        for form, name in ((self.event_form, "Event"), (self.header_form, "Header")):
            area = QScrollArea()
            area.setWidgetResizable(True)
            area.setWidget(form)
            self.tabs.addTab(area, name)
        self.tabs.addTab(self._build_tiles_tab(), "Tiles")
        dock = QDockWidget("Properties", self)
        dock.setWidget(self.tabs)
        dock.setObjectName("properties")
        dock.setMinimumWidth(360)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def _build_tiles_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(QLabel("Collision tool: left click blocks, right click opens.\n"
                             "Behavior tool: left click paints the behavior below,\nright click picks it from the map."))
        size = QHBoxLayout()
        size.addWidget(QLabel("Brush size"))
        self.brush_size = QSpinBox(minimum=1, maximum=8, value=1)
        self.brush_size.valueChanged.connect(lambda v: setattr(self.view, "brush_size", v))
        size.addWidget(self.brush_size)
        lay.addLayout(size)
        self.behavior_filter = QLineEdit(placeholderText="Filter behaviors...")
        self.behavior_list = QListWidget()
        for value, name in sorted(self.behaviors.items()):
            it = QListWidgetItem("%02X  %s" % (value, name.replace("TILE_BEHAVIOR_", "")))
            it.setData(Qt.UserRole, value)
            it.setBackground(behavior_color(value))
            it.setForeground(Qt.black)
            self.behavior_list.addItem(it)
        self.behavior_list.currentItemChanged.connect(
            lambda it, _: it and setattr(self.view, "brush_behavior", it.data(Qt.UserRole)))
        self.behavior_filter.textChanged.connect(self._filter_behaviors)
        lay.addWidget(self.behavior_filter)
        lay.addWidget(self.behavior_list, 1)
        self.tile_info = QLabel()
        self.tile_info.setWordWrap(True)
        lay.addWidget(self.tile_info)
        return w

    def _filter_behaviors(self, text):
        t = text.lower()
        for i in range(self.behavior_list.count()):
            it = self.behavior_list.item(i)
            it.setHidden(t not in it.text().lower())

    def _build_actions(self):
        tb = self.addToolBar("Main")
        tb.setObjectName("main")
        file_menu = self.menuBar().addMenu("&File")
        edit_menu = self.menuBar().addMenu("&Edit")
        view_menu = self.menuBar().addMenu("&View")

        save = QAction("Save", self, shortcut=QKeySequence.Save, triggered=self.save)
        reload_ = QAction("Reload map", self, shortcut="F5", triggered=lambda: self.doc and self.open_map(self.doc.folder, force=True))
        quit_ = QAction("Quit", self, shortcut=QKeySequence.Quit, triggered=self.close)
        file_menu.addActions([save, reload_])
        file_menu.addSeparator()
        file_menu.addAction(quit_)
        undo = self.undo.createUndoAction(self, "Undo")
        undo.setShortcut(QKeySequence.Undo)
        redo = self.undo.createRedoAction(self, "Redo")
        redo.setShortcut(QKeySequence.Redo)
        delete = QAction("Delete event", self, shortcut=QKeySequence.Delete, triggered=self.delete_selected)
        edit_menu.addActions([undo, redo, delete])
        tb.addActions([save, undo, redo])
        tb.addSeparator()

        group = QActionGroup(self)
        for key, name, shortcut in (("select", "Select / move events", "1"), ("collision", "Paint collision", "2"),
                                    ("behavior", "Paint behavior", "3")):
            a = QAction(name, self, checkable=True, shortcut=shortcut)
            a.triggered.connect(lambda _=False, k=key: self._set_tool(k))
            group.addAction(a)
            tb.addAction(a)
            if key == "select":
                a.setChecked(True)
        tb.addSeparator()
        for key, name in (("terrain", "Terrain (3D)"), ("behavior", "Behavior colors"), ("collision", "Collision"),
                          ("grid", "Grid"), ("props", "Prop markers"), ("events", "Events"), ("cells", "Cell labels")):
            a = QAction(name, self, checkable=True, checked=self.view.layers[key])
            a.toggled.connect(lambda on, k=key: self._toggle(k, on))
            view_menu.addAction(a)
            tb.addAction(a)
        view_menu.addSeparator()
        view_menu.addAction(QAction("Zoom in", self, shortcut=QKeySequence.ZoomIn, triggered=lambda: self.view.zoom(1.25)))
        view_menu.addAction(QAction("Zoom out", self, shortcut=QKeySequence.ZoomOut, triggered=lambda: self.view.zoom(0.8)))

    def _set_tool(self, key):
        self.view.tool = key
        self.view.setDragMode(MapView.RubberBandDrag if key == "select" else MapView.NoDrag)
        if key != "select":
            self.tabs.setCurrentIndex(2)

    def _toggle(self, key, on):
        self.view.layers[key] = on
        if self.doc is None:
            return
        if key == "props":
            self.view.rebuild_props()
        elif key == "events":
            self.view.rebuild_events()
            self._show_event(None)
        else:
            self.view.refresh_tiles()
            self.view.viewport().update()

    # --- 3D view ----------------------------------------------------------------------

    def _center_tab_changed(self, index):
        if index == 1:
            self._show_3d()

    def _show_3d(self):
        if self.view3d is None:
            from .view3d import Map3DView
            self.view3d = Map3DView()
            self.center.blockSignals(True)
            self.center.removeTab(1)
            self.center.insertTab(1, self.view3d, "3D")
            self.center.setCurrentIndex(1)
            self.center.blockSignals(False)
        if self.doc is not None and self._3d_stale:
            self.view3d.show_doc(self.doc, self.view.renderer, sorted(self.view.cells))
            self._3d_stale = False
        self.statusBar().showMessage("3D: left drag turns, right drag pans, wheel zooms", 5000)

    # --- opening and saving -----------------------------------------------------------

    def _update_title(self):
        # every edit goes through the undo stack, so it alone says whether there is
        # anything to save (MapDoc's dirty flags stay set after undoing back)
        name = self.doc.folder if self.doc else "no map"
        dirty = self.doc is not None and not self.undo.isClean()
        self.setWindowTitle("%s%s - HGSS map editor" % (name, " *" if dirty else ""))

    def _confirm_discard(self):
        if self.doc is None or self.undo.isClean():
            return True
        r = QMessageBox.question(self, "Unsaved changes", "Save changes to %s?" % self.doc.folder,
                                 QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if r == QMessageBox.Save:
            return self.save()
        return r == QMessageBox.Discard

    def open_map(self, folder, force=False):
        if self.doc and self.doc.folder == folder and not force:
            return
        if not self._confirm_discard():
            return
        try:
            doc = project.MapDoc(self.repo, folder)
        except (project.ProjectError, Exception) as e:  # bad data should not close the editor
            QMessageBox.warning(self, "Can't open %s" % folder, str(e))
            return
        self.doc = doc
        self.undo.clear()
        self.view.set_doc(doc)
        self._3d_stale = True
        if self.center.currentIndex() == 1:
            self._show_3d()
        self.header_form.set_fields(doc.folder, doc.header_fields())
        self.event_form.set_fields("", [])
        self._update_title()
        x0, y0, x1, y1 = doc.bounds()
        self.status.setText("%s: layout %s, cells %d,%d to %d,%d" % (doc.map.name, doc.layout_name, x0, y0, x1, y1))

    def save(self):
        """True if everything was written."""
        if self.doc is None:
            return True
        try:
            try:
                self.doc.save()
            except project.ChangedOnDisk as e:
                r = QMessageBox.question(
                    self, "Files changed outside the editor",
                    "These files were changed since %s was opened:\n\n%s\n\nOverwrite them with the editor's "
                    "version? (Cancel, then Reload map, keeps theirs and drops your edits.)"
                    % (self.doc.folder, "\n".join(e.paths)), QMessageBox.Save | QMessageBox.Cancel)
                if r != QMessageBox.Save:
                    return False
                self.doc.save(force=True)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))
            return False
        self.undo.setClean()
        self._update_title()
        self.statusBar().showMessage("Saved %s" % self.doc.folder, 3000)
        return True

    def closeEvent(self, e):
        if self._confirm_discard():
            e.accept()
        else:
            e.ignore()

    # --- edits ------------------------------------------------------------------------

    def _changed(self, kind, arg):
        if kind == "tiles":
            self.view.refresh_tiles(arg)
        elif kind == "events":
            sel = arg if arg is not None else self.view.selected_event()
            self.view.rebuild_events(select=sel)
            self._show_event(sel)
        elif kind == "header":
            self.header_form.set_fields(self.doc.folder, self.doc.header_fields())
            if arg == "area_data":   # every cell is drawn with the map's area
                self.view.refresh_terrain()
                self._3d_stale = True
                if self.center.currentIndex() == 1:
                    self._show_3d()
        self._update_title()

    def _stroke(self, tiles):
        name = "Paint collision" if self.view.tool == "collision" else "Paint behavior"
        self.undo.push(C.PaintTiles(self.doc, self._changed, tiles, name))
        lands = {self.doc.cell_land(x // CELL, y // CELL) for x, y in tiles}
        shared = {n: self.doc.land_users(n) for n in lands if len(self.doc.land_users(n)) > 1}
        if shared:
            self.statusBar().showMessage("Shared land data: this also changed %s" % "; ".join(
                "%04d in %d maps (%s)" % (n, len(users), ", ".join(users[:4]) + (", ..." if len(users) > 4 else ""))
                for n, users in sorted(shared.items())), 10000)

    def move_events(self, moves):
        """[(section, index, old_xy, new_xy)] from a drag; refused if any lands off the map."""
        off = [new for _, _, _, new in moves if not self.doc.on_map(*new)]
        if off:
            self.view.rebuild_events(select=self.view.selected_event())   # put them back
            self.statusBar().showMessage("Can't move events to %d, %d: not on %s" % (off[0] + (self.doc.folder,)), 5000)
            return
        self.undo.push(C.MoveEvents(self.doc, self._changed, moves))

    def _refuse(self, key, value, form):
        error = form.check(key, value)
        if error:
            QMessageBox.warning(self, "Can't set %s" % key, error)
        return error is not None

    def _event_field_edited(self, key, value):
        sel = self.view.selected_event()
        if not sel or self._refuse(key, value, self.event_form):
            return False
        self.undo.push(C.SetEventField(self.doc, self._changed, sel[0], sel[1], key, value))

    def _header_field_edited(self, key, value):
        if self._refuse(key, value, self.header_form):
            return False
        self.undo.push(C.SetHeaderField(self.doc, self._changed, key, value))

    def _add_event(self, section, x, y):
        if not self.doc.on_map(x, y):
            self.statusBar().showMessage("Can't add an event at %d, %d: not on %s" % (x, y, self.doc.folder), 5000)
            return
        self.undo.push(C.AddEvent(self.doc, self._changed, section, x, y))

    def delete_selected(self):
        sel = self.view.selected_event()
        if sel:
            self.undo.push(C.RemoveEvent(self.doc, self._changed, *sel))

    def _context_menu(self, x, y, global_pos):
        menu = QMenu(self)
        for section, name in SECTION_NAMES.items():
            a = menu.addAction("Add %s here (%d, %d)" % (name.lower(), x, y), lambda s=section: self._add_event(s, x, y))
            a.setEnabled(self.doc.on_map(x, y))
        if self.view.selected_event():
            menu.addSeparator()
            menu.addAction("Delete selected event", self.delete_selected)
        menu.exec(global_pos)

    # --- selection and status -----------------------------------------------------------

    def _selection_changed(self):
        self._show_event(self.view.selected_event())

    def _show_event(self, sel):
        if self.doc is None or sel is None or sel[1] >= len(self.doc.events(sel[0])):
            self.event_form.set_fields("No event selected", [])
            return
        section, index = sel
        ev = self.doc.events(section)[index]
        self.event_form.set_fields("%s %d" % (SECTION_NAMES[section], index), list(ev.items()))
        self.tabs.setCurrentIndex(0)

    def _pick_behavior(self, value):
        for i in range(self.behavior_list.count()):
            it = self.behavior_list.item(i)
            if it.data(Qt.UserRole) == value:
                self.behavior_list.setCurrentItem(it)
                self.behavior_list.scrollToItem(it)
                return

    def _hovered(self, x, y):
        t = self.doc.tile(x, y) if self.doc else None
        if t is None:
            self.tile_info.setText("")
            return
        c, b, a = t
        cx, cy = x // CELL, y // CELL
        land = self.doc.cell_land(cx, cy)
        shared = len(self.doc.land_users(land))
        text = ("tile %d, %d  (cell %d,%d, land data %04d%s)  %s  %s  attr %02X" % (
            x, y, cx, cy, land, ", shared by %d maps" % shared if shared > 1 else "",
            "blocked" if c else "open", self.behaviors.get(b, "%02X" % b), a))
        self.statusBar().showMessage(text)
        self.tile_info.setText(text)
