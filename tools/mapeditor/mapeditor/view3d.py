# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""3D view of a map: its cells' terrain and props (NSBMD, via mapkit.nitro)
drawn with OpenGL, with an orbit camera.

The mesh is grouped into one vertex buffer per (texture, palette, wrap mode,
alpha, polygon mode). Like the DS: textures repeat or mirror per material
(GL_REPEAT / GL_MIRRORED_REPEAT / clamp), color 0 / alpha-0 texels are cut out,
polygons with alpha < 31 are blended, and in modulation mode the texture is
multiplied by the vertex color.
"""

import math
from array import array

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QMatrix4x4, QSurfaceFormat, QVector3D
from PySide6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram, QOpenGLTexture,
                              QOpenGLVertexArrayObject)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from .project import CELL
from .terrain import HALF

GL_TRIANGLES, GL_FLOAT = 0x0004, 0x1406
GL_DEPTH_TEST, GL_BLEND, GL_CULL_FACE = 0x0B71, 0x0BE2, 0x0B44
GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA = 0x0302, 0x0303
GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT = 0x4000, 0x0100
GL_LEQUAL = 0x0203

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 pos;
layout(location = 1) in vec2 uv;
layout(location = 2) in vec3 color;
uniform mat4 mvp;
out vec2 v_uv;
out vec3 v_color;
void main() {
    gl_Position = mvp * vec4(pos, 1.0);
    v_uv = uv;
    v_color = color;
}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 v_uv;
in vec3 v_color;
uniform sampler2D tex;
uniform bool textured;
uniform bool modulate;
uniform float alpha;
out vec4 frag;
void main() {
    vec4 c = vec4(v_color, 1.0);
    if (textured) {
        vec4 t = texture(tex, v_uv);
        if (t.a < 0.5) discard;
        c = modulate ? t * vec4(v_color, 1.0) : t;
    }
    frag = vec4(c.rgb, c.a * alpha);
}
"""


class Batch:
    def __init__(self, key, image, wrap, alpha, modulate):
        self.key, self.image, self.wrap, self.alpha, self.modulate = key, image, wrap, alpha, modulate
        self.data = array("f")
        self.count = 0
        self.vbo = self.vao = self.texture = None


def build_batches(doc, renderer, cells):
    """Triangles of the given layout cells -> {key: Batch}, positions in world units
    (x east, y up, z south; one tile = 16)."""
    batches = {}
    for cx, cy in cells:
        chunk = doc.chunk(cx, cy)
        if chunk is None:
            continue
        ox, oz = cx * CELL * 16 + HALF, cy * CELL * 16 + HALF
        try:
            items = renderer.cell_triangles(chunk.number, doc.area_for_cell(cx, cy), chunk.props,
                                            doc.cell_altitude(cx, cy))
        except Exception as e:  # draw the other cells; the error shows in renderer.errors
            renderer.errors.append(("land %04d" % chunk.number, str(e)))
            continue
        for tri, tkey, texset, off in items:
            mat = tri.material
            img = renderer._image(tkey, texset, mat) if mat else None
            alpha = (mat.alpha or 31) if mat else 31
            mode = (mat.poly_attr >> 4) & 3 if mat else 0
            if mode == 3:  # shadow volume polygons, not drawn as surfaces
                continue
            if img is not None:
                rs, rt = mat.repeat
                fs, ft = mat.flip
                # the renderer pre-mirrors flipped textures, so plain repeat covers a mirrored pair
                wrap = (rs, rt)
                key = (tkey, mat.texture, mat.palette, fs, ft, rs, rt, alpha, mode)
                w, h = img.width(), img.height()
            else:
                wrap = (False, False)
                key = ("color", alpha)
                w = h = 1
            b = batches.get(key)
            if b is None:
                b = batches[key] = Batch(key, img, wrap, alpha / 31.0, mode == 0)
            for (x, y, z), (u, v), (r, g, bl) in zip(tri.pos, tri.uv, tri.color):
                b.data.extend((x + off[0] + ox, y + off[1], z + off[2] + oz, u / w, v / h,
                               r / 255.0, g / 255.0, bl / 255.0))
            b.count += 3
    return batches


class Camera:
    def __init__(self):
        self.target = QVector3D(0, 0, 0)
        self.distance = 900.0
        self.yaw = 0.0        # degrees, 0 = looking north
        self.pitch = 50.0     # degrees above the horizon

    def matrix(self, aspect):
        proj = QMatrix4x4()
        proj.perspective(40.0, aspect, 4.0, 20000.0)
        p, y = math.radians(self.pitch), math.radians(self.yaw)
        eye = self.target + QVector3D(math.sin(y) * math.cos(p), math.sin(p), math.cos(y) * math.cos(p)) * self.distance
        view = QMatrix4x4()
        view.lookAt(eye, self.target, QVector3D(0, 1, 0))
        return proj * view


class SceneGL:
    """GL resources and drawing; call init/draw with a current context."""

    def __init__(self):
        self.program = None
        self.batches = {}

    def init(self, ctx):
        self.f = ctx.functions()
        self.program = QOpenGLShaderProgram()
        self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX_SHADER)
        self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAGMENT_SHADER)
        if not self.program.link():
            raise RuntimeError("shader link failed: %s" % self.program.log())

    def set_batches(self, batches):
        self.release()
        self.batches = batches
        for b in batches.values():
            b.vao = QOpenGLVertexArrayObject()
            b.vao.create()
            b.vao.bind()
            b.vbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
            b.vbo.create()
            b.vbo.bind()
            raw = b.data.tobytes()
            b.vbo.allocate(raw, len(raw))
            stride = 8 * 4
            for loc, size, offset in ((0, 3, 0), (1, 2, 12), (2, 3, 20)):
                self.program.enableAttributeArray(loc)
                self.program.setAttributeBuffer(loc, GL_FLOAT, offset, size, stride)
            b.vao.release()
            b.vbo.release()
            if b.image is not None:
                t = QOpenGLTexture(b.image.convertToFormat(QImage.Format_RGBA8888))
                t.setMinificationFilter(QOpenGLTexture.Nearest)
                t.setMagnificationFilter(QOpenGLTexture.Nearest)
                t.setWrapMode(QOpenGLTexture.DirectionS, QOpenGLTexture.Repeat if b.wrap[0] else QOpenGLTexture.ClampToEdge)
                t.setWrapMode(QOpenGLTexture.DirectionT, QOpenGLTexture.Repeat if b.wrap[1] else QOpenGLTexture.ClampToEdge)
                b.texture = t

    def release(self):
        for b in self.batches.values():
            if b.texture is not None:
                b.texture.destroy()
            if b.vbo is not None:
                b.vbo.destroy()
            if b.vao is not None:
                b.vao.destroy()
        self.batches = {}

    def draw(self, mvp, width, height):
        f = self.f
        f.glViewport(0, 0, width, height)
        f.glClearColor(0.12, 0.13, 0.16, 1.0)
        f.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        f.glEnable(GL_DEPTH_TEST)
        f.glDepthFunc(GL_LEQUAL)
        f.glDisable(GL_CULL_FACE)
        self.program.bind()
        self.program.setUniformValue("mvp", mvp)
        self.program.setUniformValue1i("tex", 0)
        ordered = sorted(self.batches.values(), key=lambda b: b.alpha < 1.0)   # opaque first
        for b in ordered:
            if b.alpha < 1.0:
                f.glEnable(GL_BLEND)
                f.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                f.glDepthMask(False)
            self.program.setUniformValue1i("textured", 1 if b.texture else 0)
            self.program.setUniformValue1i("modulate", 1 if b.modulate else 0)
            self.program.setUniformValue1f("alpha", b.alpha)
            if b.texture:
                b.texture.bind(0)
            b.vao.bind()
            f.glDrawArrays(GL_TRIANGLES, 0, b.count)
            b.vao.release()
            if b.texture:
                b.texture.release()
            if b.alpha < 1.0:
                f.glDisable(GL_BLEND)
                f.glDepthMask(True)
        self.program.release()


def default_format():
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    fmt.setDepthBufferSize(24)
    fmt.setSamples(4)
    return fmt


class Map3DView(QOpenGLWidget):
    """Left drag orbits, right/middle drag pans, wheel zooms; double click recentres."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFormat(default_format())
        self.scene = SceneGL()
        self.camera = Camera()
        self._pending = None
        self._last = QPoint()
        self.setMinimumSize(320, 240)

    def show_doc(self, doc, renderer, cells):
        """Load the cells' terrain; the camera looks at the map's own cells."""
        self._pending = build_batches(doc, renderer, cells)
        own = doc.own_cells() or cells
        cx = sum(c[0] for c in own) / len(own)
        cy = sum(c[1] for c in own) / len(own)
        self.camera.target = QVector3D((cx + 0.5) * CELL * 16, 0, (cy + 0.5) * CELL * 16)
        span = max(max(c[0] for c in own) - min(c[0] for c in own), max(c[1] for c in own) - min(c[1] for c in own)) + 1
        self.camera.distance = 700.0 * span
        self.update()

    def initializeGL(self):
        self.scene.init(self.context())
        self.context().aboutToBeDestroyed.connect(self._cleanup)

    def _cleanup(self):
        self.makeCurrent()
        self.scene.release()
        self.doneCurrent()

    def paintGL(self):
        if self._pending is not None:
            self.scene.set_batches(self._pending)
            self._pending = None
        aspect = self.width() / max(1, self.height())
        ratio = self.devicePixelRatioF()
        self.scene.draw(self.camera.matrix(aspect), int(self.width() * ratio), int(self.height() * ratio))

    def mousePressEvent(self, e):
        self._last = e.position().toPoint()

    def mouseMoveEvent(self, e):
        pos = e.position().toPoint()
        d = pos - self._last
        self._last = pos
        if e.buttons() & Qt.LeftButton:
            self.camera.yaw -= d.x() * 0.4
            self.camera.pitch = max(5.0, min(89.0, self.camera.pitch + d.y() * 0.4))
        elif e.buttons() & (Qt.RightButton | Qt.MiddleButton):
            y = math.radians(self.camera.yaw)
            k = self.camera.distance / 600.0
            right = QVector3D(math.cos(y), 0, -math.sin(y))
            fwd = QVector3D(-math.sin(y), 0, -math.cos(y))
            self.camera.target += right * (-d.x() * k) + fwd * (d.y() * k)
        self.update()

    def wheelEvent(self, e):
        self.camera.distance = max(50.0, min(15000.0, self.camera.distance * (0.85 if e.angleDelta().y() > 0 else 1.18)))
        self.update()
