# pokeheartgold-modding

> [!WARNING]
> **This repository is AI-generated and is not affiliated with pret.**
> It is a fork of [pret/pokeheartgold](https://github.com/pret/pokeheartgold) whose
> changes were written by LLM coding agents. pret does not accept AI-generated code
> and does not want to be associated with it: don't send anything from here to pret,
> and don't ask pret for help with it. Issues and questions belong here.
> How the work was made and checked: [AI.md](AI.md).

A version of the Pokémon HeartGold and SoulSilver decompilation set up for modding. The
goal is to make changing the game feel like working in pret's
[pokeemerald](https://github.com/pret/pokeemerald): game data as text, PNG, JSON and
MIDI files you can edit, plus tools and guides for the common jobs.

Both ROMs still build **byte for byte** from this repository (`make` checks it):

* **pokeheartgold.us.nds** `sha1: 4fcded0e2713dc03929845de631d0932ea2b5a37`
* **pokesoulsilver.us.nds** `sha1: f8dc38ea20c17541a43b58c5e6d18c1732c7e582`

All compiled code is C or C++. The assembly left is code that was hand-written in
assembly originally (about 0.6% of the code) and data tables.

[![Source-language coverage treemap](docs/progress/treemap.svg)](INSTALL.md#progress-reports)

## What's here

| Area | In this repository | Guide |
|---|---|---|
| Maps | `data/maps/<Map>/` folders (`map.json`, `scripts.pory`, `text.json`) like pokeemerald's; layouts, terrain and heights as files; the `mapkit` tool; a map editor | [maps-and-warps.md](docs/modding/maps-and-warps.md), [terrain.md](docs/modding/terrain.md) |
| Scripts | every map's scripts decompiled to poryscript-style `scripts.pory`, compiled by `mapkit` | [SCRIPTING.md](docs/modding/SCRIPTING.md), [npcs-and-scripts.md](docs/modding/npcs-and-scripts.md) |
| Pokémon | base stats, evolutions, learnsets, egg moves as JSON; sprites as PNG | [pokemon.md](docs/modding/pokemon.md) |
| Moves, items | `battle_moves.json`, `data/items/items.json`, item icons as PNG | [moves.md](docs/modding/moves.md), [items.md](docs/modding/items.md) |
| Trainers | parties as JSON; trainer sprites as PNG with their animations | [trainer-classes.md](docs/modding/trainer-classes.md) |
| Music and sound | the sound archive as files in `sound/`; new songs from MIDI, instruments from WAV | [music.md](docs/modding/music.md) |
| Story, flags, gyms | every story gate with its flag and script; what each gym sets and checks | [story-progression.md](docs/modding/story-progression.md), [gyms.md](docs/modding/gyms.md) |
| Engine | abilities, UI screens, save layout, hard-coded limits | [abilities.md](docs/modding/abilities.md), [ui.md](docs/modding/ui.md), [save-data.md](docs/modding/save-data.md), [game-limits.md](docs/modding/game-limits.md) |
| Map format | gen4map, a documented text format for Gen 4 maps, meant to become a standalone tool | [docs/gen4map](docs/gen4map/README.md) |

**Start with [docs/WIKI.md](docs/WIKI.md)**: every documented task, with the guide and
command for it. Its last section lists what isn't documented yet.

## Building

Setup is in [INSTALL.md](INSTALL.md). Then:

```bash
make                # build HeartGold and check it matches the retail ROM
make soulsilver     # the same for SoulSilver
make release        # build without the checks: use this once you've changed something
```

A modified game won't match the retail checksums; that is expected. The tools have
their own tests, listed in [CONTRIBUTING.md](CONTRIBUTING.md#checks).

## Status

- Each guide ends with a **Not verified** section listing what was only read in the code,
  not tested in the game. Treat those parts with care.
- This repository is a base for mods, so `main` always builds matching ROMs. Changes to
  the game itself belong in your own fork.
- The guides describe this fork's layout. Most of it doesn't exist in pret's repository.

## Credits

The decompilation, its build system and most of the original tools come from
[pret/pokeheartgold](https://github.com/pret/pokeheartgold) and its contributors; their
commits are kept in this repository's history. The layout and many conventions follow
[pret/pokeemerald](https://github.com/pret/pokeemerald). Bundled third-party tools keep
their own licenses (see their folders under `tools/`).

pret's repository has no license file, and this fork adds none. Pokémon is © Nintendo,
Creatures Inc. and GAME FREAK inc.; this project is not affiliated with them.
