from pathlib import Path
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference

# =========================
# SETTINGS - millimetres
# =========================
WIDTH = 25.0
LENGTH = 40.0
THICKNESS = 30.0

HOLE_DIAMETER = 12.0
HOLE_RADIUS = HOLE_DIAMETER / 2

OUTPUT_DIR = Path("spacers_for_gate/stl")
OUTPUT_DIR.mkdir(exist_ok=True)

script_name = Path(__file__).stem
OUTPUT_FILE = OUTPUT_DIR / f"{script_name}.stl"

# =========================
# CREATE SPACER BODY
# =========================
spacer = box(extents=[WIDTH, LENGTH, THICKNESS])

# =========================
# CREATE CENTRE HOLE
# =========================
hole = cylinder(
    radius=HOLE_RADIUS,
    height=THICKNESS + 2,
    sections=64
)

# Move hole through the spacer vertically
hole.apply_translation([0, 0, 0])

# =========================
# CUT HOLE FROM SPACER
# =========================
spacer_with_hole = difference([spacer, hole])

# =========================
# EXPORT STL
# =========================
spacer_with_hole.export(OUTPUT_FILE)

print(f"STL saved to: {OUTPUT_FILE}")