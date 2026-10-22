# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Run: QT_QPA_PLATFORM=offscreen tools/mapeditor/.venv/bin/python -m unittest discover -s tools/mapeditor/tests

Works on a copy of the files the editor touches, so the checkout is never changed."""

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from mapeditor import project  # noqa: E402

COPY = ["include", "asm/macros", "data/maps", "data/layouts", "data/landdata",
        "src/data/map_headers.h", "files/fielddata/encountdata", "files/msgdata/msg", "tools/mapkit/script_config.json"]


class Checkout:
    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="mapeditor-test-")
        for rel in COPY:
            src, dst = os.path.join(project.ROOT, rel), os.path.join(self.root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.isdir(src):  # the editor never reads the models
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns("*.nsbmd", "*.bdhc"))
            else:
                shutil.copy2(src, dst)

    def close(self):
        shutil.rmtree(self.root)


class ProjectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.co = Checkout()

    @classmethod
    def tearDownClass(cls):
        cls.co.close()

    def doc(self, name="Cherrygrove"):
        return project.MapDoc(project.open_repo(self.co.root), name)

    def test_open(self):
        d = self.doc()
        self.assertEqual(d.layout_name, "Overworld")
        self.assertEqual(d.own_cells(), [(16, 12), (17, 12)])
        self.assertIsNotNone(d.tile(16 * 32, 12 * 32))
        self.assertEqual(len(d.events("warp_events")), 5)

    def test_tile_edit_saves_permissions(self):
        d = self.doc()
        x, y = 16 * 32 + 3, 12 * 32 + 4
        c, b, a = d.tile(x, y)
        d.set_tile(x, y, collision=1 - c, behavior=0x02)
        d.save()
        d2 = self.doc()
        self.assertEqual(d2.tile(x, y), (1 - c, 0x02, a))
        d2.set_tile(x, y, collision=c, behavior=b)
        d2.save()

    def test_event_edits_save_map_json(self):
        d = self.doc()
        ev = d.events("object_events")[0]
        old = (ev["x"], ev["y"])
        d.move_event("object_events", 0, old[0] + 1, old[1])
        i = d.add_event("bg_events", 520, 400)
        d.save()
        d2 = self.doc()
        self.assertEqual(d2.events("object_events")[0]["x"], old[0] + 1)
        self.assertEqual(d2.events("bg_events")[i]["type"], "BG_TYPE_SIGNPOST")
        d2.remove_event("bg_events", i)
        d2.move_event("object_events", 0, *old)
        d2.save()

    def test_behavior_names(self):
        names = project.behavior_names(self.co.root)
        self.assertEqual(names[0x02], "TILE_BEHAVIOR_TALL_GRASS")
        self.assertEqual(names[0xFF], "TILE_BEHAVIOR_NONE")


class UndoTest(unittest.TestCase):
    """The Qt commands against a MapDoc, without showing a window."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])
        cls.co = Checkout()

    @classmethod
    def tearDownClass(cls):
        cls.co.close()

    def test_paint_move_and_field_undo(self):
        from PySide6.QtGui import QUndoStack
        from mapeditor import commands as C
        d = project.MapDoc(project.open_repo(self.co.root), "Cherrygrove")
        log = []
        changed = lambda kind, arg: log.append(kind)  # noqa: E731
        stack = QUndoStack()
        x, y = 16 * 32 + 5, 12 * 32 + 5
        before = d.tile(x, y)
        after = (1 - before[0], before[1], before[2])
        d.set_tile(x, y, collision=after[0])           # the view paints during the stroke
        stack.push(C.PaintTiles(d, changed, {(x, y): (before, after)}))
        self.assertEqual(d.tile(x, y), after)
        stack.undo()
        self.assertEqual(d.tile(x, y), before)
        stack.redo()
        self.assertEqual(d.tile(x, y), after)

        ev = d.events("warp_events")[0]
        start = (ev["x"], ev["y"])
        stack.push(C.MoveEvent(d, changed, "warp_events", 0, start, (start[0] + 2, start[1])))
        stack.push(C.SetEventField(d, changed, "warp_events", 0, "dest_warp_id", 7))
        self.assertEqual((ev["x"], ev["dest_warp_id"]), (start[0] + 2, 7))
        stack.undo()
        stack.undo()
        self.assertEqual((ev["x"], ev["y"]), start)
        self.assertNotEqual(ev["dest_warp_id"], 7)

        n = len(d.events("object_events"))
        stack.push(C.AddEvent(d, changed, "object_events", 530, 400))
        self.assertEqual(len(d.events("object_events")), n + 1)
        stack.push(C.RemoveEvent(d, changed, "object_events", n))
        stack.undo()
        self.assertEqual(d.events("object_events")[n]["x"], 530)
        stack.undo()
        self.assertEqual(len(d.events("object_events")), n)
        self.assertIn("tiles", log)
        self.assertIn("events", log)

    def test_window_opens(self):
        from mapeditor.window import MainWindow
        w = MainWindow(project.open_repo(self.co.root), "Cherrygrove")
        self.assertEqual(len(w.view.cells), 12)
        self.assertGreater(len(w.view.event_items), 10)
        w.undo.clear()
        w.close()


class TerrainTest(unittest.TestCase):
    """Drawing the game's models (reads the checkout, writes nothing)."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_top_down_cell(self):
        from mapeditor.terrain import CELL_PX, TerrainRenderer
        doc = project.MapDoc(project.open_repo(), "Cherrygrove")
        r = TerrainRenderer(project.ROOT)
        chunk = doc.chunk(17, 12)
        img = r.render_cell(chunk.number, doc.area_for_cell(17, 12), chunk.props, doc.cell_altitude(17, 12))
        self.assertEqual(r.errors, [])
        self.assertEqual((img.width(), img.height()), (CELL_PX, CELL_PX))
        drawn = sum(1 for y in range(0, CELL_PX, 8) for x in range(0, CELL_PX, 8) if img.pixelColor(x, y).alpha())
        self.assertGreater(drawn, 0.95 * (CELL_PX // 8) ** 2)   # the town covers its whole cell

    def test_3d_scene_renders(self):
        from PySide6.QtGui import QOffscreenSurface, QOpenGLContext, QVector3D
        from PySide6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat
        from mapeditor.terrain import TerrainRenderer
        from mapeditor.view3d import Camera, SceneGL, build_batches, default_format
        ctx = QOpenGLContext()
        ctx.setFormat(default_format())
        surf = QOffscreenSurface()
        surf.setFormat(ctx.format())
        surf.create()
        if not ctx.create() or not ctx.makeCurrent(surf):
            self.skipTest("no OpenGL 3.3 context")
        fmt = QOpenGLFramebufferObjectFormat()
        fmt.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
        fbo = QOpenGLFramebufferObject(320, 240, fmt)
        fbo.bind()
        doc = project.MapDoc(project.open_repo(), "Cherrygrove")
        batches = build_batches(doc, TerrainRenderer(project.ROOT), doc.own_cells())
        self.assertGreater(sum(b.count for b in batches.values()), 3000)
        scene = SceneGL()
        scene.init(ctx)
        scene.set_batches(batches)
        cam = Camera()
        cam.target = QVector3D(17 * 512, 0, 12.5 * 512)
        scene.draw(cam.matrix(320 / 240), 320, 240)
        img = fbo.toImage()
        scene.release()
        fbo.release()
        ctx.doneCurrent()
        background = img.pixelColor(0, 0)
        centre = img.pixelColor(160, 120)
        self.assertNotEqual(centre, background)


if __name__ == "__main__":
    unittest.main()
