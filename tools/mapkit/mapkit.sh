#!/bin/sh
# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21
# Run mapkit from anywhere inside the checkout: tools/mapkit/mapkit.sh show Cherrygrove
here=$(dirname "$(readlink -f "$0")")
PYTHONPATH="$here${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m mapkit "$@"
