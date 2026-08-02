"""32x32 battle sprites for the 12 Znome species.

Sprites come from znome_parts: creatures assembled from anatomy (body,
head, face, mirrored appendages) and rendered GB-style with white
bodies, selective dither shading and solid black outlines.
"""

from znome_parts import SPECIES, generate

SIZE = 32

ORDER = [
    "rubblin", "cragnome", "frostpod", "cryonaut", "sparklet", "arcfang",
    "tinplate", "ferrox", "mycomite", "bloomshade", "nullet", "vantabeast",
]

assert set(ORDER) == set(SPECIES)

ZNOMES = [(name, lambda n=name: generate(n)) for name in ORDER]
