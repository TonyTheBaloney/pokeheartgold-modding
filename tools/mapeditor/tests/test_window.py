# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-27
"""The main window driven like a user would, on a copy of the checkout
(docs/gen4map/CHANGE-0004-map-editor.md part 1).

Run: QT_QPA_PLATFORM=offscreen tools/mapeditor/.venv/bin/python -m unittest discover -s tools/mapeditor/tests"""

import os
import sys
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QFormLayout, QMessageBox  # noqa: E402

from mapeditor import project  # noqa: E402
from mapeditor.canvas import TILE  # noqa: E402
from mapeditor.project import CELL  # noqa: E402
from mapeditor.window import MainWindow  # noqa: E402
from test_editor import Checkout  # noqa: E402


class WindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.co = Checkout()
        self.windows = []

    def tearDown(self):
        for w in self.windows:
            w.undo.setClean()
            w.close()
        self.co.close()

    def window(self, name="Cherrygrove"):
        w = MainWindow(project.open_repo(self.co.root), name)
        w.show()
        self.windows.append(w)
        return w

    def read(self, rel):
        with open(os.path.join(self.co.root, rel), encoding="utf-8") as f:
            return f.read()

    def item(self, w, section, index):
        return next(it for it in w.view.event_items if (it.section, it.index) == (section, index))

    def field(self, form, key):
        for i in range(form.form.rowCount()):
            label = form.form.itemAt(i, QFormLayout.ItemRole.LabelRole)
            if label and label.widget() and label.widget().text() == key:
                return form.form.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
        raise KeyError(key)

    def nudge(self, w):
        """Move warp 0 one tile east, an undoable edit."""
        ev = w.doc.events("warp_events")[0]
        w.move_events([("warp_events", 0, (ev["x"], ev["y"]), (ev["x"] + 1, ev["y"]))])
        self.assertFalse(w.undo.isClean())

    def edit_field(self, form, key, text):
        e = self.field(form, key)
        e.setText(text)
        e.editingFinished.emit()

    # B1
    def test_failed_save_keeps_the_map_open(self):
        w = self.window()
        self.nudge(w)
        with mock.patch.object(QMessageBox, "question", return_value=QMessageBox.Save), \
                mock.patch.object(QMessageBox, "critical") as critical, \
                mock.patch.object(project.MapDoc, "save", side_effect=OSError("disk full")):
            w.open_map("Violet")
        critical.assert_called_once()
        self.assertEqual(w.doc.folder, "Cherrygrove")
        self.assertFalse(w.undo.isClean())

    # B2
    def test_dragging_a_selection_moves_every_selected_event(self):
        w = self.window()
        a, b = self.item(w, "warp_events", 0), self.item(w, "warp_events", 1)
        start = [(it.ev["x"], it.ev["y"]) for it in (a, b)]
        a.setSelected(True)
        b.setSelected(True)
        w.view.centerOn(a)
        vp = w.view.viewport()
        p0 = w.view.mapFromScene(a.pos() + a.boundingRect().center())
        p1 = p0 + QPoint(int(2 * TILE * w.view.transform().m11()), 0)
        QTest.mousePress(vp, Qt.LeftButton, Qt.NoModifier, p0)
        for t in range(1, 6):
            QTest.mouseMove(vp, p0 + (p1 - p0) * (t / 5))
        QTest.mouseRelease(vp, Qt.LeftButton, Qt.NoModifier, p1)
        ws = w.doc.events("warp_events")
        self.assertEqual([(ws[i]["x"], ws[i]["y"]) for i in (0, 1)], [(x + 2, y) for x, y in start])
        self.assertEqual(w.undo.count(), 1)
        w.undo.undo()
        self.assertEqual([(ws[i]["x"], ws[i]["y"]) for i in (0, 1)], start)

    # B3
    def test_editing_a_field_keeps_the_form(self):
        w = self.window()
        self.item(w, "warp_events", 0).setSelected(True)
        before = self.field(w.event_form, "dest_warp_id")
        self.edit_field(w.event_form, "dest_warp_id", "3")
        self.assertEqual(w.doc.events("warp_events")[0]["dest_warp_id"], 3)
        self.assertIs(self.field(w.event_form, "dest_warp_id"), before)   # not deleted and rebuilt
        w.undo.undo()
        self.assertEqual(before.text(), str(w.doc.events("warp_events")[0]["dest_warp_id"]))
        self.edit_field(w.header_form, "weather", "WEATHER_RAIN")
        self.assertEqual(w.doc.data["weather"], "WEATHER_RAIN")

    # B4
    def test_neighbour_cells_cant_be_painted(self):
        w = self.window()
        own = set(w.doc.own_cells())
        other = next(c for c in w.view.cells if c not in own)
        x, y = other[0] * CELL + 3, other[1] * CELL + 3
        before = w.doc.tile(x, y)
        w._set_tool("collision")
        w.view.centerOn(x * TILE, y * TILE)
        pos = w.view.mapFromScene(x * TILE + TILE / 2, y * TILE + TILE / 2)
        button = Qt.RightButton if before[0] else Qt.LeftButton
        QTest.mouseClick(w.view.viewport(), button, Qt.NoModifier, pos)
        self.assertEqual(w.doc.tile(x, y), before)
        self.assertEqual(w.undo.count(), 0)

    # B5
    def test_shared_land_data_counts_maps(self):
        doc = project.MapDoc(project.open_repo(self.co.root), "Cherrygrove_Pokecenter_1F")
        land = doc.cell_land(0, 0)
        users = doc.land_users(land)
        self.assertGreater(len(users), 20)
        self.assertIn("Cherrygrove_Pokecenter_1F", users)

    # B6
    def test_header_area_change_redraws_and_layout_is_read_only(self):
        w = self.window()
        cell = next(iter(w.view.cells.values()))
        cell._terrain_image()
        self.edit_field(w.header_form, "area_data", str(int(w.doc.data["area_data"]) + 1))
        self.assertIsNone(cell._terrain)
        self.assertTrue(w._3d_stale)
        self.assertTrue(self.field(w.header_form, "layout").isReadOnly())

    # S1
    def test_undo_back_to_saved_is_clean(self):
        w = self.window()
        self.nudge(w)
        self.assertTrue(w.windowTitle().startswith("Cherrygrove *"))
        w.undo.undo()
        self.assertFalse(w.windowTitle().startswith("Cherrygrove *"))
        with mock.patch.object(QMessageBox, "question") as question:
            w.open_map("Violet")
        question.assert_not_called()

    # S2
    def test_unknown_constant_is_refused(self):
        w = self.window()
        self.item(w, "object_events", 0).setSelected(True)
        old = w.doc.events("object_events")[0]["flag"]
        with mock.patch.object(QMessageBox, "warning") as warning:
            self.edit_field(w.event_form, "flag", "FLAG_NO_SUCH_FLAG_X")
        warning.assert_called_once()
        self.assertEqual(w.doc.events("object_events")[0]["flag"], old)
        self.assertEqual(self.field(w.event_form, "flag").text(), old)
        self.assertEqual(w.undo.count(), 0)

    # S3
    def test_new_object_gets_an_id_define(self):
        w = self.window()
        w._add_event("object_events", 16 * CELL + 4, 12 * CELL + 4)
        local_id = w.doc.events("object_events")[-1]["local_id"]
        w.save()
        self.assertRegex(self.read("data/maps/Cherrygrove/ids.h"), r"#define %s\s+6\b" % local_id)
        self.assertEqual(project.open_repo(self.co.root).event_defines(w.doc.map).eval(local_id), 6)

    # S4
    def test_events_stay_on_the_map(self):
        w = self.window()
        ev = w.doc.events("warp_events")[0]
        start = (ev["x"], ev["y"])
        x0, y0, _, _ = w.doc.bounds()
        outside = (x0 * CELL - 5, y0 * CELL - 5)
        with mock.patch.object(w.statusBar(), "showMessage") as msg:
            w.move_events([("warp_events", 0, start, outside)])
        msg.assert_called()
        self.assertEqual((ev["x"], ev["y"]), start)
        self.assertEqual(w.undo.count(), 0)

    # S5
    def test_zoom_actions_are_limited(self):
        w = self.window()
        for _ in range(60):
            w.view.zoom(1.25)
        self.assertLessEqual(w.view.transform().m11(), 8)
        for _ in range(60):
            w.view.zoom(0.8)
        self.assertGreaterEqual(w.view.transform().m11(), 0.05)

    # S9
    def test_save_asks_before_overwriting_outside_changes(self):
        w = self.window()
        self.nudge(w)
        path = os.path.join(self.co.root, "data/maps/Cherrygrove/map.json")
        time.sleep(0.01)
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n")
        outside = self.read("data/maps/Cherrygrove/map.json")
        with mock.patch.object(QMessageBox, "question", return_value=QMessageBox.Cancel) as question:
            w.save()
        question.assert_called_once()
        self.assertEqual(self.read("data/maps/Cherrygrove/map.json"), outside)
        self.assertFalse(w.undo.isClean())
        with mock.patch.object(QMessageBox, "question", return_value=QMessageBox.Save):
            w.save()
        self.assertNotEqual(self.read("data/maps/Cherrygrove/map.json"), outside)
        self.assertTrue(w.undo.isClean())


class RoundTripTest(unittest.TestCase):
    """Opening and saving maps without edits changes no file."""

    def test_save_unchanged(self):
        co = Checkout()
        try:
            repo = project.open_repo(co.root)
            for folder, _, _ in project.map_list(repo):
                d = project.MapDoc(repo, folder)
                d.dirty = True
                for cx, cy in d.own_cells():
                    d.chunk(cx, cy).dirty = True
                d.save()
            import subprocess
            for rel in ("data/maps", "data/layouts", "data/landdata"):
                r = subprocess.run(["diff", "-r", "-q", "-x", "*.nsbmd", "-x", "*.bdhc",
                                    os.path.join(project.ROOT, rel), os.path.join(co.root, rel)],
                                   capture_output=True, text=True)
                self.assertEqual(r.stdout, "", rel)
        finally:
            co.close()


if __name__ == "__main__":
    unittest.main()
