# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Top-down pictures of a cell's 3D terrain and props, for the map view.

Each cell's model.nsbmd (data/landdata/NNNN/) is drawn with the textures of
its map's area (map.json "area_data" -> area header NARC_a_0_4_2 -> map
textures NARC_a_0_4_4), and each prop in props.json with the area's prop
models (NARC_a_0_4_0 outdoors, NARC_a_1_4_8 indoors, chosen by the header's
buildModelKind) and prop textures (NARC_a_0_7_0), as src/field/area_data.c
and map_prop_manager.c load them.

Looking straight down, every triangle maps texture space to the image by an
affine transform, so QPainter can fill it with the texture as a brush. Triangles
are drawn from the lowest to the highest so roofs and trees cover the ground.
One model unit is one pixel: a 32-tile cell is 512 x 512, the same as the view.
"""

import os
import struct

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPolygonF, QTransform

from mapkit import landdata, nitro

CELL_PX = 512
HALF = CELL_PX / 2
AREA_HEADERS = "files/a/0/4/2"
MAP_TEXTURES = "files/a/0/4/4"
PROP_TEXTURES = "files/a/0/7/0"
PROP_MODELS = {0: "files/a/1/4/8", 1: "files/a/0/4/0"}  # buildModelKind 0 = room, otherwise field


class Narc:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.members = landdata.narc_members(f.read())

    def __getitem__(self, i):
        return self.members[i]

    def __len__(self):
        return len(self.members)


class TerrainRenderer:
    def __init__(self, root):
        self.root = root
        self._narcs = {}
        self._texsets = {}
        self._images = {}
        self._meshes = {}
        self.errors = []      # (what, message) for things that could not be drawn

    def _narc(self, rel):
        if rel not in self._narcs:
            self._narcs[rel] = Narc(os.path.join(self.root, rel))
        return self._narcs[rel]

    def area(self, area_id):
        """(prop list/texture id, map texture id, buildModelKind) of an area."""
        prop_id, tex_id, _anim, kind, _light = struct.unpack("<HHHBB", self._narc(AREA_HEADERS)[area_id])
        return prop_id, tex_id, kind

    def _texset(self, rel, idx):
        """The NSBTX in member idx, or None: areas without prop textures have a 4-byte placeholder."""
        key = (rel, idx)
        if key not in self._texsets:
            data = self._narc(rel)[idx]
            self._texsets[key] = nitro.load_nsbtx(data) if data[:4] == b"BTX0" else None
        return self._texsets[key]

    def _image(self, texset_key, texset, material):
        """QImage for a material's texture (mirrored when the material flips), or None."""
        key = (texset_key, material.texture, material.palette, material.flip)
        if key not in self._images:
            img = None
            decoded = texset.image(material.texture, material.palette) if texset and material.texture else None
            if decoded:
                w, h, rgba = decoded
                img = QImage(rgba, w, h, w * 4, QImage.Format_RGBA8888).copy()
                fs, ft = material.flip
                if fs or ft:  # mirrored repeat: one period is the image and its mirror
                    big = QImage(w * (2 if fs else 1), h * (2 if ft else 1), QImage.Format_RGBA8888)
                    p = QPainter(big)
                    p.setCompositionMode(QPainter.CompositionMode_Source)
                    p.drawImage(0, 0, img)
                    if fs:
                        p.drawImage(w, 0, img.mirrored(True, False))
                    if ft:
                        p.drawImage(0, h, img.mirrored(False, True))
                    if fs and ft:
                        p.drawImage(w, h, img.mirrored(True, True))
                    p.end()
                    img = big
            self._images[key] = img
        return self._images[key]

    def _mesh(self, key, data):
        if key not in self._meshes:
            models, own_tex = nitro.load_nsbmd(data)
            tris = []
            for m in models:
                tris += m.triangles()
            self._meshes[key] = (tris, own_tex)
        return self._meshes[key]

    def cell_triangles(self, land_id, area_id, props, altitude=0):
        """[(Triangle, texset key, TextureSet, offset)] for the terrain and its props.

        The terrain is raised by the layout cell's altitude (altitude << 15 in fx32,
        CalcMapPosition in src/field/map_load_manager.c); props are not, their y is
        absolute (MapPropManager_DrawWithOffset adds only x and z)."""
        prop_id, tex_id, kind = self.area(area_id)
        out = []
        chunk = os.path.join(self.root, landdata.LANDDATA_DIR, "%04d" % land_id)
        with open(os.path.join(chunk, "model.nsbmd"), "rb") as f:
            tris, own = self._mesh(("land", land_id), f.read())
        texset = own or self._texset(MAP_TEXTURES, tex_id)
        tkey = ("land", land_id) if own else (MAP_TEXTURES, tex_id)
        out += [(t, tkey, texset, (0.0, altitude * 8.0, 0.0)) for t in tris]
        models = self._narc(PROP_MODELS[1 if kind else 0])
        ptex = self._texset(PROP_TEXTURES, prop_id)
        for i, p in enumerate(props):
            n = p["model"]
            if not 0 <= n < len(models):
                self.errors.append(("land %04d prop %d" % (land_id, i), "no prop model %d" % n))
                continue
            try:
                tris, own = self._mesh(("prop", kind, n), models[n])
            except nitro.NitroError as e:
                self.errors.append(("prop model %d" % n, str(e)))
                continue
            key = ("prop", kind, n) if own else (PROP_TEXTURES, prop_id)
            ts = own or ptex
            out += [(t, key, ts, tuple(p["position"])) for t in tris]
        return out

    def render_cell(self, land_id, area_id, props, altitude=0):
        """QImage (CELL_PX square, transparent where nothing is drawn) of the cell from above."""
        img = QImage(CELL_PX, CELL_PX, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        try:
            items = self.cell_triangles(land_id, area_id, props, altitude)
        except (nitro.NitroError, OSError, IndexError, struct.error) as e:
            self.errors.append(("land %04d" % land_id, str(e)))
            return img
        # lowest first; for equal heights keep the model's own order
        order = sorted(range(len(items)), key=lambda i: max(p[1] + items[i][3][1] for p in items[i][0].pos))
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setPen(Qt.NoPen)
        for i in order:
            tri, tkey, texset, off = items[i]
            pts = [(x + off[0] + HALF, z + off[2] + HALF) for x, _, z in tri.pos]
            area2 = (pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1]) - (pts[2][0] - pts[0][0]) * (pts[1][1] - pts[0][1])
            if abs(area2) < 0.01:      # a wall seen edge-on
                continue
            mat = tri.material
            alpha = mat.alpha if mat else 31
            p.setOpacity(1.0 if alpha in (0, 31) else alpha / 31.0)
            poly = QPolygonF([QPointF(x, y) for x, y in pts])
            img_tex = self._image(tkey, texset, mat) if mat else None
            brush = None
            if img_tex is not None:
                t = _uv_transform(tri.uv, pts)
                if t is not None:
                    brush = QBrush(img_tex)
                    brush.setTransform(t)
            if brush is None:
                r, g, b = (sum(c[k] for c in tri.color) // 3 for k in range(3))  # one color per vertex
                brush = QBrush(QColor(r, g, b))
            p.setBrush(brush)
            p.drawPolygon(poly)
        p.end()
        return img


def _uv_transform(uv, pts):
    """QTransform taking texel coordinates to image pixels for one triangle, or None."""
    (u0, v0), (u1, v1), (u2, v2) = uv
    du1, dv1, du2, dv2 = u1 - u0, v1 - v0, u2 - u0, v2 - v0
    det = du1 * dv2 - du2 * dv1
    if abs(det) < 1e-9:
        return None
    (x0, y0), (x1, y1), (x2, y2) = pts
    dx1, dy1, dx2, dy2 = x1 - x0, y1 - y0, x2 - x0, y2 - y0
    # [x y] = [u v] * [[a b], [c d]] + [e f]
    a = (dx1 * dv2 - dx2 * dv1) / det
    c = (dx2 * du1 - dx1 * du2) / det
    b = (dy1 * dv2 - dy2 * dv1) / det
    d = (dy2 * du1 - dy1 * du2) / det
    e = x0 - a * u0 - c * v0
    f = y0 - b * u0 - d * v0
    return QTransform(a, b, c, d, e, f)
