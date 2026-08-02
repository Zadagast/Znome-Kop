"""Procedurally generated 32x32 sprites for the 12 Znome species.

Each species is a coarse silhouette bias mask ('#' body, '+' sparse,
'.' empty) plus a hand-picked seed fed to znome_gen_masked (a 1-bit
mask-guided variant of the Deep-Fold generator). Masks are designed
around how the cellular automata grows: solid cores for mass, sparse
'+' fringes where organic edges, limbs and wisps should sprout.
Void-line species render dark.
"""

from znome_gen_masked import generate

SIZE = 32

# (mask, seed, dark)
SPECIES = {
    # regolith: round pebble hatchling, stubby feet, cracked crown
    "rubblin": ([
        "............",
        "....+##+....",
        "...######...",
        "..########..",
        "..########..",
        "..########..",
        "..########..",
        "..########..",
        "...######...",
        "..+#+..+#+..",
        "...+....+...",
        "............"], 7, False),
    # regolith: broad golem, boulder shoulders, hanging arms
    "cragnome": ([
        "............",
        "....####....",
        "..+######+..",
        ".##########.",
        "+##########+",
        "##+######+##",
        "##.######.##",
        "+#.######.#+",
        "...######...",
        "..+##++##+..",
        "..##+..+##..",
        "............"], 4, False),
    # cryo: ice seed, jagged crystal crown
    "frostpod": ([
        "..+..##..+..",
        "..#+.##.+#..",
        "..###+####..",
        ".+########+.",
        ".##########.",
        ".##########.",
        ".##########.",
        "..########..",
        "..+######+..",
        "...+####+...",
        "....+##+....",
        "............"], 6, False),
    # cryo: tall crystalline wraith, trailing shards below
    "cryonaut": ([
        "...+#..#+...",
        "...######...",
        "..########..",
        "..########..",
        "...######...",
        "..+######+..",
        ".##########.",
        ".##########.",
        "..########..",
        "..+##..##+..",
        "...+#..#+...",
        "....+..+...."], 3, False),
    # plasma: flame wisp, flickering sparse edges
    "sparklet": ([
        ".....+......",
        "....+#+.....",
        "...+###+....",
        "...#####....",
        "..+#####+...",
        "..#######...",
        "..#######...",
        "..+#####+...",
        "...#####....",
        "...+###+....",
        "....+#+.....",
        "............"], 0, False),
    # plasma: eared static feline, whisker fringe, tail
    "arcfang": ([
        ".##.....##..",
        ".###+..+##..",
        ".#########..",
        "+#########+.",
        ".#########..",
        "..#######...",
        "..#######.++",
        ".#########.+",
        ".#########+.",
        ".##+.##.+##.",
        ".#+..##..+..",
        "............"], 6, False),
    # ferro: boxy scrap robot, antenna head, square feet
    "tinplate": ([
        "....####....",
        "....####....",
        ".....##.....",
        ".##########.",
        ".##########.",
        ".##########.",
        ".##########.",
        ".##########.",
        ".##########.",
        "..##+..+##..",
        "..##....##..",
        "............"], 3, False),
    # ferro: plated quadruped, spined back
    "ferrox": ([
        "..+.+..+.+..",
        ".###+..+###.",
        ".##########.",
        "############",
        "############",
        "############",
        "############",
        ".##########.",
        ".+########+.",
        ".##.+##+.##.",
        ".##..##..##.",
        "............"], 7, False),
    # myco: capped spore walker, wide cap with drooping rim
    "mycomite": ([
        "....+##+....",
        "..########..",
        ".##########.",
        "############",
        "#+########+#",
        "+..######..+",
        "...######...",
        "...######...",
        "..+######+..",
        "..##+..+##..",
        "............",
        "............"], 2, False),
    # myco: void flower, petal crown, narrow waist, root feet
    "bloomshade": ([
        "..#+.##.+#..",
        ".##########.",
        ".##########.",
        "..########..",
        "...######...",
        "...+####+...",
        "....####....",
        "...######...",
        "..########..",
        ".###+..+###.",
        ".##+....+##.",
        "............"], 3, False),
    # void: small dark mote, wispy halo
    "nullet": ([
        "............",
        ".....++.....",
        "...+####+...",
        "..########..",
        "..########..",
        ".+########+.",
        "..########..",
        "..########..",
        "...######...",
        "....+##+....",
        ".....++.....",
        "............"], 5, True),
    # void: hulking horned apex beast, clawed stance
    "vantabeast": ([
        "##+......+##",
        "###+....+###",
        "+##########+",
        "############",
        "############",
        "############",
        "############",
        "############",
        "+##########+",
        ".###+..+###.",
        ".+##....##+.",
        "............"], 6, True),
}

ORDER = [
    "rubblin", "cragnome", "frostpod", "cryonaut", "sparklet", "arcfang",
    "tinplate", "ferrox", "mycomite", "bloomshade", "nullet", "vantabeast",
]


def _sprite(name):
    mask, seed, dark = SPECIES[name]
    base = sum(ord(ch) for ch in name) * 131
    return generate(base + seed, mask=mask, dark=dark)


ZNOMES = [(name, lambda n=name: _sprite(n)) for name in ORDER]
