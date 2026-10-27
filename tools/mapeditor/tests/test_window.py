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
from PySide6.QtGui import QColor  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QFormLayout, QMessageBox  # noqa: E402

from mapeditor import project  # noqa: E402
from mapeditor.canvas import TILE  # noqa: E402
from mapeditor.project import CELL  # noqa: E402
from mapeditor.window import MainWindow  # noqa: E402
from test_editor import Checkout  # noqa: E402


class WindowCase(unittest.TestCase):
    """A fresh copy of the checkout per test, and helpers to drive the window."""

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


class WindowTest(WindowCase):

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


class SpriteTest(WindowCase):
    """Objects drawn as their overworld sprites (CHANGE-0004 part 2)."""

    def objects(self, w):
        return [it for it in w.view.event_items if it.section == "object_events"]

    def test_frame_for_facing(self):
        from mapeditor.sprites import frame_for
        self.assertEqual([frame_for(16, f) for f in range(4)], [0, 4, 8, 12])
        self.assertEqual([frame_for(17, f) for f in range(4)], [0, 4, 8, 12])
        self.assertEqual([frame_for(8, f) for f in range(4)], [0, 2, 4, 6])
        self.assertEqual([frame_for(n, 3) for n in (1, 7)], [0, 0])

    def test_objects_are_drawn_as_sprites(self):
        w = self.window()
        objs = self.objects(w)
        self.assertEqual(len(objs), 6)
        for it in objs:
            self.assertIsNotNone(it.sprite, it.ev["graphics_id"])
            self.assertEqual((it.sprite.width(), it.sprite.height()), (32, 32))
            self.assertEqual(it.shape().boundingRect(), it.shape().boundingRect().intersected(
                it.boundingRect()))   # clicks hit the tile, drawing covers the sprite
        by_facing = {it.ev["facing_dir"]: it for it in objs}
        west, east = by_facing["DIR_WEST"].sprite, by_facing["DIR_EAST"].sprite
        self.assertNotEqual(west, east)
        img = w.view.sprites.image("SPRITE_GSBOY1", "DIR_WEST")   # frame 9 is frame 13 mirrored
        self.assertEqual(img.flipped(Qt.Orientation.Horizontal), w.view.sprites.image("SPRITE_GSBOY1", "DIR_EAST"))

    def test_var_sprites_are_boxes_with_a_reason(self):
        w = self.window("DragonsDen")
        var = [it for it in self.objects(w) if str(it.ev["graphics_id"]).startswith("SPRITE_VAR_")]
        self.assertTrue(var)
        for it in var:
            self.assertIsNone(it.sprite)
            self.assertIn("VAR_OBJ_", it.toolTip())

    def test_sprites_follow_edits_and_the_toggle(self):
        w = self.window()
        it = next(i for i in self.objects(w) if i.ev["facing_dir"] == "DIR_SOUTH")
        index = it.index
        it.setSelected(True)
        self.assertFalse(w.event_form.preview.isHidden())
        self.edit_field(w.event_form, "facing_dir", "DIR_NORTH")
        it = next(i for i in self.objects(w) if i.index == index)
        self.assertEqual(it.sprite, w.view.sprites.image(it.ev["graphics_id"], "DIR_NORTH"))
        w._toggle("sprites", False)
        self.assertTrue(all(i.sprite is None for i in self.objects(w)))
        w._toggle("sprites", True)
        self.assertTrue(all(i.sprite is not None for i in self.objects(w)))

    def test_graphics_id_completions_have_pictures(self):
        from PySide6.QtCore import Qt as _Qt
        w = self.window()
        self.item(w, "object_events", 0).setSelected(True)
        model = self.field(w.event_form, "graphics_id").completer().model()
        row = model.stringList().index("SPRITE_GSBOY1")
        self.assertFalse(model.data(model.index(row), _Qt.DecorationRole).isNull())

    def test_poses(self):
        from mapeditor.sprites import N, S, W, E, movement, pose
        self.assertEqual([pose("MOVEMENT_TYPE_WANDER_UP_DOWN", "DIR_SOUTH", 16, t) for t in (0, 1, 2, 3, 16)],
                         [(N, 0), (N, 1), (N, 2), (N, 3), (S, 0)])
        self.assertEqual([pose("MOVEMENT_TYPE_LOOK_LEFT_RIGHT", "DIR_SOUTH", 16, t) for t in (0, 1, 8)],
                         [(W, 0), (W, 0), (E, 0)])
        self.assertEqual(movement("MOVEMENT_TYPE_PATH_WEST_EAST_SOUTH_NORTH_2"), ("walk", (W, E, S, N)))
        self.assertEqual([pose("MOVEMENT_TYPE_BACK_AND_FORTH", "DIR_WEST", 16, t)[0] for t in (0, 16)], [W, E])
        self.assertEqual([pose("MOVEMENT_TYPE_FACE_LEFT", "DIR_EAST", 16, t) for t in (0, 5)], [(E, 0), (E, 0)])
        self.assertEqual([pose("MOVEMENT_TYPE_NONE", "DIR_EAST", 8, t) for t in (0, 2)], [(E, 0), (E, 1)])

    def test_animation_plays_and_stops(self):
        w = self.window()
        self.item(w, "object_events", 0).setSelected(True)
        self.edit_field(w.event_form, "movement_type", "MOVEMENT_TYPE_WANDER_AROUND")
        self.assertTrue(w.view._clock.isActive())
        it = self.item(w, "object_events", 0)
        g = it.ev["graphics_id"]
        seen = set()
        for _ in range(64):
            w.view._advance()
            seen.add(self.item(w, "object_events", 0).sprite.cacheKey())
        frames = {w.view.sprites.image(g, f, s).cacheKey() for f in range(4) for s in range(4)}
        self.assertEqual(seen, frames & seen)
        self.assertGreaterEqual(len(seen), 12)     # 4 directions x walk cycle (stand frames repeat)
        w._toggle("animate", False)
        self.assertFalse(w.view._clock.isActive())
        self.assertEqual(self.item(w, "object_events", 0).sprite, w.view.sprites.image(g, it.ev["facing_dir"]))

    def test_sprites_in_3d(self):
        w = self.window()
        sprites = w._sprites_3d()
        self.assertEqual(len(sprites), 6)
        for x, y, z, img in sprites:
            self.assertEqual(img.width(), 32)
        w._toggle("sprites", False)
        self.assertEqual(w._sprites_3d(), [])

    def test_billboards_draw(self):
        from PySide6.QtGui import QImage, QOffscreenSurface, QOpenGLContext, QVector3D
        from PySide6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat
        from mapeditor.view3d import Camera, SceneGL, default_format
        ctx = QOpenGLContext()
        ctx.setFormat(default_format())
        surf = QOffscreenSurface()
        surf.setFormat(ctx.format())
        surf.create()
        if not ctx.create() or not ctx.makeCurrent(surf):
            self.skipTest("no OpenGL 3.3 context")
        fmt = QOpenGLFramebufferObjectFormat()
        fmt.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
        fbo = QOpenGLFramebufferObject(200, 200, fmt)
        fbo.bind()
        red = QImage(32, 32, QImage.Format_RGBA8888)
        red.fill(QColor(255, 0, 0))
        scene = SceneGL()
        scene.init(ctx)
        cam = Camera()
        cam.target, cam.distance, cam.pitch, cam.yaw = QVector3D(0, 16, 0), 120, 5, 35
        mvp = cam.matrix(1.0)
        scene.draw(mvp, 200, 200)
        scene.draw_sprites(mvp, cam.yaw, [(0.0, 0.0, 0.0, red)])
        img = fbo.toImage()
        scene.release_sprites()
        fbo.release()
        ctx.doneCurrent()
        self.assertEqual(img.pixelColor(100, 100).name(), "#ff0000")   # faces the camera at any yaw
        self.assertNotEqual(img.pixelColor(100, 20).name(), "#ff0000")

    def test_missing_sprite_table_keeps_boxes(self):
        os.remove(os.path.join(self.co.root, "asm/overlay_01_sprite_data.s"))
        w = self.window()
        self.assertTrue(all(i.sprite is None and i.sprite_note for i in self.objects(w)))


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
