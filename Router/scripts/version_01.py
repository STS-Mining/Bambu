from pathlib import Path
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference

# =========================================================
# SETTINGS
# =========================================================
WIDTH = 150.0       # X direction
LENGTH = 220.0      # Y direction
THICKNESS = 60.0    # Z direction

FAN_SIZE = 120.0
FAN_RECESS_SIZE = 122.0
FAN_RECESS_DEPTH = 26.0

AIR_HOLE_DIAMETER = 114.0

FAN_SCREW_SPACING = 105.0
FAN_SCREW_DIAMETER = 4.5

TOP_MARGIN = 15.0

# =========================================================
# OUTPUT
# =========================================================
SAVE_DIR = Path("Router/stl")
SAVE_DIR.mkdir(exist_ok=True)

script_name = Path(__file__).stem
OUTPUT_FILE = SAVE_DIR / f"{script_name}.stl"

# =========================================================
# POSITIONS
# =========================================================
fan_center_x = WIDTH / 2
fan_center_y = LENGTH - TOP_MARGIN - (FAN_SIZE / 2)
fan_center_z = THICKNESS / 2

# =========================================================
# MAIN SPACER BLOCK
# =========================================================
main_block = box(extents=[WIDTH, LENGTH, THICKNESS])
main_block.apply_translation([
    WIDTH / 2,
    LENGTH / 2,
    THICKNESS / 2
])

cutters = []

# =========================================================
# FAN RECESS POCKET
# =========================================================
fan_recess = box(extents=[
    FAN_RECESS_SIZE,
    FAN_RECESS_SIZE,
    FAN_RECESS_DEPTH + 2
])

fan_recess.apply_translation([
    fan_center_x,
    fan_center_y,
    THICKNESS - (FAN_RECESS_DEPTH / 2) + 1
])

cutters.append(fan_recess)

# =========================================================
# AIR FLOW HOLE THROUGH SPACER
# =========================================================
air_hole = cylinder(
    radius=AIR_HOLE_DIAMETER / 2,
    height=THICKNESS + 4,
    sections=96
)

air_hole.apply_translation([
    fan_center_x,
    fan_center_y,
    THICKNESS / 2
])

cutters.append(air_hole)

# =========================================================
# FAN SCREW HOLES
# =========================================================
offset = FAN_SCREW_SPACING / 2

screw_positions = [
    [-offset, -offset],
    [ offset, -offset],
    [-offset,  offset],
    [ offset,  offset],
]

for dx, dy in screw_positions:
    screw_hole = cylinder(
        radius=FAN_SCREW_DIAMETER / 2,
        height=THICKNESS + 4,
        sections=48
    )

    screw_hole.apply_translation([
        fan_center_x + dx,
        fan_center_y + dy,
        THICKNESS / 2
    ])

    cutters.append(screw_hole)

# =========================================================
# BOOLEAN CUTS
# =========================================================
final = difference(
    [main_block] + cutters,
    engine="manifold"
)

# =========================================================
# EXPORT STL
# =========================================================
final.export(OUTPUT_FILE)

print(f"STL saved to: {OUTPUT_FILE}")