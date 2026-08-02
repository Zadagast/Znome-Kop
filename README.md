# Znome Kop

A 1-bit sci-fi monster-collecting RPG for the [Playdate](https://play.date), set on Mars.
You are a Kop: you sweep the spore fields outside Hellas Colony, contain Znomes in stasis
pods, train a squad and push deeper through procedurally generated sectors.

No story, no cutscenes. The game is the loop: explore, catch, train, battle, go further out.

```
Hellas Colony  ->  Dust Flats  ->  Rust Canyon  ->  Lava Tubes  ->  Relay Station  ->  Anomaly Field
 (hand-built)          (generated from here on, one relay tower per sector unlocks the next)
```

## Controls

| Input | World | Battle / menus |
| --- | --- | --- |
| D-pad | Walk left / right | Move the cursor |
| A | Talk | Confirm |
| B | Open the pause menu (squad, Kodex, kit, save) | Cancel / back |

## Play it

The compiled bundle `ZnomeKop.pdx` is committed, so no SDK or build step is needed:

```sh
git pull
open ZnomeKop.pdx            # macOS: opens in the Playdate Simulator
PlaydateSimulator ZnomeKop.pdx   # Linux/Windows
```

For the device, zip the `ZnomeKop.pdx` folder and upload the zip at
[play.date/account/sideload](https://play.date/account/sideload).

## Build

Requires the [Playdate SDK](https://play.date/dev/) (`PLAYDATE_SDK_PATH`), plus `lua5.4`
and Python `Pillow` if you want to regenerate art.

```sh
make build     # compile source/ -> ZnomeKop.pdx
make test      # headless gameplay tests (generation, battle, data)
make art       # regenerate sprite sheets + source/scripts/world/atlas.lua
make run       # build and launch the simulator
make preview SECTOR=3 SEED=42   # ASCII dump of a generated sector
```

## Project layout

```
source/
  main.lua                 entry point, 30 fps scene loop
  pdxinfo
  images/                  1-bit sheets (AI scenes + characters, Znomes, launcher)
  scripts/
    core/                  util, seeded RNG, UI chrome, asset loading, save
    data/                  types, moves, species, items, sector definitions
    world/                 legacy top-down mapgen (kept for the test suite)
    game/                  creature, battle model, scenes, side-scroller, battle UI, menus
tests/                     headless harness + suite (runs under plain lua5.4)
tools/                     art generators, AI art converter, ASCII map previewer
```

Everything the game shows is data-driven: creatures, moves, type chart, items and the
per-sector generation parameters all live in `source/scripts/data/`.

## Procedural sectors

Full WFC over 3,000+ tiles is too slow for the device, so generation is a hybrid
(`source/scripts/world/mapgen.lua`):

1. **Macro grid.** The sector is solved at 1/4 resolution — one macro cell is 4x4 tiles, so a
   64x48 sector is a 16x12 solve.
2. **Structure first.** Points of interest are pre-collapsed onto the grid before solving, so
   layouts have intent rather than being pure noise.
3. **Constrained fill.** Entropy-ordered WFC with an adjacency table (`OPEN`, `ROUGH`, `FIELD`,
   `WALL`, `HAZARD`, `SITE`) plus a same-label affinity bonus, which is what makes rock ridges
   and grass fields read as coherent regions.
4. **Guaranteed routes.** A minimum spanning tree over the POIs (plus a couple of loops for
   non-linearity) is carved as corridors.
5. **Expansion and validation.** Macro cells expand to tiles with softened borders; a flood
   fill then proves every POI is reachable, repairs anything that is not, seals unreachable
   pockets and tops up encounter ground.

Generation is deterministic from `(sector, seed)` and takes ~35 ms per sector in the headless
harness, so a save file only stores seeds and a handful of flags.

## Battle

Six types (`REGOLITH`, `CRYO`, `PLASMA`, `FERRIC`, `SPORE`, `VOID`), each strong against two and
weak to two. Six stats, four move slots, stat stages, five status conditions, multi-hit/drain/
recoil moves, criticals and a Gen-1-flavoured containment formula that rewards weakening and
statusing a target before throwing a pod.

`source/scripts/game/battle.lua` is pure Lua with no Playdate dependencies, which is why the
test suite can run thousands of turns per commit.

## Tests

`make test` runs entirely under stock `lua5.4` (the harness stubs `import`). It covers RNG
determinism and fairness, the type chart's symmetry, species/move data integrity, levelling and
evolution, battle termination and damage sanity, catch-rate behaviour, and — for 40 seeds of
every generated sector — that the entry is walkable, every walkable tile is reachable, every POI
is connected, a relay onward exists, there is enough encounter ground, and generation stays
inside the frame budget.
