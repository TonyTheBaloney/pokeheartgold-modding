# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""tools/mapeditor/mapeditor.sh [MapFolder]"""

import argparse
import sys

from PySide6.QtWidgets import QApplication

from . import project
from .window import MainWindow


def main(argv=None):
    ap = argparse.ArgumentParser(description="HGSS map editor")
    ap.add_argument("map", nargs="?", help="map to open, e.g. Cherrygrove")
    ap.add_argument("--root", default=project.ROOT, help="pokeheartgold checkout")
    a, qt_args = ap.parse_known_args(argv)
    app = QApplication([sys.argv[0]] + qt_args)
    app.setApplicationName("HGSS map editor")
    w = MainWindow(project.open_repo(a.root), a.map)
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
