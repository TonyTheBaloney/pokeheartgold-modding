<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Idea: shiny Pokémon icons (parked)

> AI-generated, local to this fork. Do not upstream. **Not built.** These are notes from
> exploring the idea (2026-10-22), kept so the work can pick up where it stopped.

**Goal:** show shiny Pokémon with shiny colors in their small icons (party, PC box,
naming screen...). Battle sprites already have shiny palettes; icons have none in Gen 4.

**Why it's parked:** every approach either gets the colors wrong for many species, or
can't color every shiny in a crowded screen. A PC box full of shinies where only some are
recolored, or recolored approximately, didn't feel right. Nothing below is implemented.

## How icon colors work today

- Every icon uses one of **3 shared 16-color palettes**, in
  `files/poketool/icongra/poke_icon/poke_icon_00000000.pal` (palette 0: 268 species and
  forms, palette 1: 121, palette 2: 155).
- `sPokemonPalNoBySpeciesAndForm` in `src/pokemon_icon_idx.c` says which one, read through
  `GetMonIconPaletteEx(species, form, isEgg)`, `Pokemon_GetIconPalette(mon)` and
  `Boxmon_GetIconPalette(boxMon)`.
- Each screen loads the 3 palettes once (`GetMonIconPlttNaix()`), into 3 of its 16 sprite
  palette slots. The party menu loads them on both screens (palette offsets +1 and +3 in
  `src/party_menu_sprites.c`).
- In the 3 palettes, indices 0-3, 14 and 15 are the same grays and outline; indices 4-13
  are each palette's colors, in a different order.

## Options considered

| Option | Result | Cost | Verdict |
|---|---|---|---|
| **Shiny marker** (a ★ next to shiny icons) | clear, not recolored | small, per screen | the fallback any option needs |
| **Swap palettes**: draw a shiny with one of the other 2 shared palettes | random colors: purple Pikachu, pink or gold Gyarados, white icons like Lugia unchanged | no VRAM; code path only | colors look wrong |
| **6 shared palettes** (3 normal + 3 shiny) | one shiny color per index for ~270 species at once, so still a compromise. Letting each species pick any of 6 palettes helps but can't make every species right | 3 more palette slots in each of the 34 files that load the icon palettes (not checked how many have room) | compromise colors at a real slot cost |
| **Per-species shiny palettes, loaded only for shiny icons** | real shiny colors (generated, below) | ~540 small palettes; one free slot per shiny on screen; a fallback when a screen runs out (PC box) | best colors, but a full box of shinies can't all be colored |

## Generating per-species shiny icon colors

`docs/ideas/shiny-icons/preview.py` (needs Pillow) renders icons with each method next to
the real shiny battle sprite; `preview.png` is its output for 12 species.

The game already has every species' real shiny colors: the battle sprite's normal palette
(`files/poketool/pokegra/pokegra/NNNN/male/front.png`) and shiny palette (`back.png`, as
`tools/scripts/make_pokegra.py` builds them). The icon is recolored by mapping each icon
color to a sprite color and taking that color's shiny version. The outline grays
(indices 14, 15) are never changed. Two ways to do the mapping:

- **nearest**: the nearest normal sprite color. Right when the icon was drawn in the
  sprite's colors: Charizard (black), Scizor (green), Umbreon (blue rings), Bulbasaur,
  Typhlosion, Ampharos (pink).
- **family**: group colors by hue, pair the icon's groups with the sprite's, and map dark
  to dark, light to light. Needed when the icon artist used another hue: Gyarados' icon
  is lavender and its sprite cyan, so "nearest" pairs the lavender with a pale gray-blue
  (shiny: white). "family" pairs lavender with cyan and gives a red Gyarados.
- **best**: whichever of the two gives icon colors closer to the real shiny sprite
  (symmetric chamfer distance in Lab, weighted by pixel share). It picks right for 11 of
  the 12 test species. **Miss:** Ampharos, where it chooses "family" (dark blue) over
  "nearest" (the right pink).

Not done yet:

- Render all ~540 icons (species and forms) and count how many need a hand override.
- Forms: their battle sprites are in `files/poketool/pokegra/otherpoke/`, mapped
  differently from species.
- Overrides: a per-species table (method or explicit colors), checked into the repo and
  built like the other data.

## What any option needs in code

- **Shininess at the icon.** `MonIsShiny(mon)` / `BoxMonIsShiny(boxMon)` (from the
  personality value and trainer ID; no save change). `Pokemon_GetIconPalette` and
  `Boxmon_GetIconPalette` already get the Pokémon: making them shiny-aware covers 16 calls
  in 10 files, including the PC box, summary, battle touch screen and Frontier screens.
  The other 34 calls (`GetMonIconPaletteEx`, `GetBattleMonIconPaletteEx`, 24 files) pass
  only species and form; the party menu and naming screen would need the Pokémon passed in.
- **Palette slots** (6 shared or per-species): each screen's palette layout, checked one
  by one. Not counted yet.

## Related: naming screen details (also not built)

Showing whether a Pokémon is shiny and its IVs on the naming screen
(`src/naming_screen.c`) needs new fields in `NamingScreenArgs`
(`include/naming_screen.h`), filled by its three callers: catching
(`src/battle/battle_command.c`), hatching (`src/hatch_egg_task.c`) and script nickname
prompts (`CallTask_NamingScreen`, `src/launch_application.c`). Gen 4 icons can't show
shininess by color today, so it would be a ★ or text; the IVs a text window on the top
screen.
