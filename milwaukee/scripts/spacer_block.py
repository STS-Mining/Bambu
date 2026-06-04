from pathlib import Path
import trimesh
from trimesh.creation import box, cylinder

LENGTH = 73.0
WIDTH = 56.0
THICKNESS = 30.0

HOLE_DIAMETER = 6.0
HOLE_RADIUS = HOLE_DIAMETER / 2

SAVE_DIR = Path("milwaukee/stl")
SAVE_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = SAVE_DIR / "spacer_block.stl"

# Main block
block = box(extents=[LENGTH, WIDTH, THICKNESS])
block.apply_translation([LENGTH/2, WIDTH/2, THICKNESS/2])

# Hole locations
hole_positions = [
    [15.0, WIDTH/2, THICKNESS/2],
    [LENGTH - 10.0, WIDTH/2, THICKNESS/2]
]

holes = []

for pos in hole_positions:
    hole = cylinder(
        radius=HOLE_RADIUS,
        height=THICKNESS + 2,
        sections=64
    )
    hole.apply_translation(pos)
    holes.append(hole)

# Cut holes
result = trimesh.boolean.difference(
    [block] + holes,
    engine='manifold'
)

result.export(OUTPUT_FILE)

print(f"Saved STL to {OUTPUT_FILE}")