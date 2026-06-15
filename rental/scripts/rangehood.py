from pathlib import Path
import trimesh
from shapely.geometry import Polygon
from trimesh.creation import extrude_polygon, cylinder
from trimesh.boolean import difference

# =========================
# SETTINGS - millimetres
# =========================
LENGTH = 15.0
THICK_END_HEIGHT = 6.0
THIN_END_HEIGHT = 3.0
DEPTH = 20.0

HOLE_DIAMETER = 3.0
HOLE_X = 18.0
HOLE_Z = THICK_END_HEIGHT / 2

SAVE_DIR = Path("hebersham/stl")
SAVE_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = SAVE_DIR / "tapered_shape_with_3mm_hole.stl"

# =========================
# SIDE PROFILE
# X = length
# Z = height
# =========================
profile = Polygon([
    (0, 0),
    (LENGTH, 0),
    (LENGTH, THIN_END_HEIGHT),
    (0, THICK_END_HEIGHT),
])

body = extrude_polygon(profile, DEPTH)
body.apply_translation([0, -DEPTH / 2, 0])

# =========================
# 3mm hole through thick part
# Hole goes through the depth
# =========================
hole = cylinder(
    radius=HOLE_DIAMETER / 2,
    height=DEPTH + 4,
    sections=48
)

# Rotate cylinder so it cuts through Y direction
hole.apply_transform(trimesh.transformations.rotation_matrix(
    1.5708, [1, 0, 0]
))

hole.apply_translation([HOLE_X, 0, HOLE_Z])

final = difference([body, hole])

final.export(OUTPUT_FILE)

print(f"Saved STL to: {OUTPUT_FILE}")