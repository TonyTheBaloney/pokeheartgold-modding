#!/bin/sh
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
# Start the Rust map editor: tools/mapeditor-rs/mapeditor-rs.sh [MapFolder] [--3d]
# Builds it first if needed (cargo, Rust 1.95 or newer).
here=$(dirname "$(readlink -f "$0")")
command -v cargo >/dev/null || { echo "cargo not found: install Rust (https://rustup.rs)" >&2; exit 1; }
cargo build --release --quiet --manifest-path "$here/Cargo.toml" -p mapeditor || exit 1
exec "$here/target/release/mapeditor-rs" --root "$here/../.." "$@"
