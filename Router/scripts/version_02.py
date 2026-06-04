from pathlib import Path
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference

# =========================================================
# SETTINGS
# =========================================================
WIDTH = 150.0
LENGTH = 220.0
THICKNESS = 60.0

FAN_SIZE = 120.0
FAN_RECESS_SIZE = 122.0
FAN_RECESS_DEPTH = 26.0

AIR_HOLE_DIAMETER = 114.0

FAN_SCREW_SPACING = 105.0
FAN_SCREW_DIAMETER = 4.5

# Internal duct / air chamber
DUCT_WIDTH = 95.0
DUCT_LENGTH = 120.0
DUCT_HEIGHT = 34.0

SIDE_VENT_HEIGHT = 20.0
SIDE_VENT_DEPTH = 45.0

# =========================================================
# OUTPUT
# =========================================================
SAVE_DIR = Path("Router/stl")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

script_name = Path(__file__).stem
OUTPUT_FILE = SAVE_DIR / f"{script_name}.stl"

# =========================================================
# POSITIONS
# =========================================================
fan_center_x = WIDTH / 2
fan_center_y = LENGTH / 2

# =========================================================
# MAIN BODY
# =========================================================
main_block = box(extents=[WIDTH, LENGTH, THICKNESS])
main_block.apply_translation([WIDTH / 2, LENGTH / 2, THICKNESS / 2])

cutters = []

# =========================================================
# TOP FAN RECESS
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
# ROUND FAN AIR HOLE
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

for dx, dy in [
    [-offset, -offset],
    [ offset, -offset],
    [-offset,  offset],
    [ offset,  offset],
]:
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
# INTERNAL AIR CHAMBER UNDER FAN
# =========================================================
duct = box(extents=[
    DUCT_WIDTH,
    DUCT_LENGTH,
    DUCT_HEIGHT
])
duct.apply_translation([
    fan_center_x,
    fan_center_y,
    DUCT_HEIGHT / 2
])
cutters.append(duct)

# =========================================================
# LEFT AND RIGHT LOWER AIR INLETS
# =========================================================
left_vent = box(extents=[
    SIDE_VENT_DEPTH,
    DUCT_LENGTH,
    SIDE_VENT_HEIGHT
])
left_vent.apply_translation([
    SIDE_VENT_DEPTH / 2,
    fan_center_y,
    SIDE_VENT_HEIGHT / 2 + 4
])
cutters.append(left_vent)

right_vent = box(extents=[
    SIDE_VENT_DEPTH,
    DUCT_LENGTH,
    SIDE_VENT_HEIGHT
])
right_vent.apply_translation([
    WIDTH - (SIDE_VENT_DEPTH / 2),
    fan_center_y,
    SIDE_VENT_HEIGHT / 2 + 4
])
cutters.append(right_vent)

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
final.export(str(OUTPUT_FILE))

print(f"STL saved to: {OUTPUT_FILE}")