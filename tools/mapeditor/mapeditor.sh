#!/bin/sh
# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
# Start the map editor: tools/mapeditor/mapeditor.sh [MapFolder]
# First run: python3 -m venv tools/mapeditor/.venv && tools/mapeditor/.venv/bin/pip install PySide6
here=$(dirname "$(readlink -f "$0")")
py="$here/.venv/bin/python"
[ -x "$py" ] || { echo "no venv: python3 -m venv $here/.venv && $here/.venv/bin/pip install PySide6" >&2; exit 1; }
cd "$here" && exec "$py" -m mapeditor "$@"
