from pathlib import Path
import math
import trimesh
from shapely.geometry import Polygon
from trimesh.creation import extrude_polygon

# =========================================================
# SETTINGS
# =========================================================
LENGTH = 30.0
WIDTH = 10.0
THICKNESS = 20.0

FLAT_SPOT = 10.0       # flat section on top, in the centre
CURVE_START_Z = 0.0    # lower this for more curve, raise for less curve

SAVE_DIR = Path("router/stl")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = SAVE_DIR / "spacer_block_curved_with_flat.stl"

# =========================================================
# SIDE PROFILE
# =========================================================
flat_start_x = (LENGTH - FLAT_SPOT) / 2
flat_end_x = flat_start_x + FLAT_SPOT

points = []

# Bottom edge
points.append((0, 0))
points.append((LENGTH, 0))

# Right curved side
steps = 32
for i in range(steps + 1):
    t = i / steps
    x = LENGTH - (t * flat_start_x)
    z = CURVE_START_Z + (THICKNESS - CURVE_START_Z) * math.sin(t * math.pi / 2)
    points.append((x, z))

# Flat top centre
points.append((flat_start_x, THICKNESS))

# Left curved side
for i in range(steps, -1, -1):
    t = i / steps
    x = t * flat_start_x
    z = CURVE_START_Z + (THICKNESS - CURVE_START_Z) * math.sin(t * math.pi / 2)
    points.append((x, z))

profile = Polygon(points)

# Extrude through WIDTH
spacer = extrude_polygon(profile, WIDTH)

spacer.merge_vertices()
spacer.fix_normals()

# =========================================================
# EXPORT
# =========================================================
spacer.export(OUTPUT_FILE)

print(f"Saved STL to: {OUTPUT_FILE}")