from pathlib import Path
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference, union

# =========================================================
# SETTINGS - ADJUST THESE IF NEEDED
# =========================================================

SAVE_DIR = "milwaukee/stl"

# Automatically use the script filename as the STL filename
SCRIPT_NAME = Path(__file__).stem
OUTPUT_FILE = f"{SCRIPT_NAME}.stl"

# Main base
BASE_LENGTH = 120.0
BASE_WIDTH = 85.0
BASE_THICKNESS = 40.0   # thick base for heavy tools

# Slide-in battery tongue section
TONGUE_LENGTH = 92.0
TONGUE_WIDTH = 52.0
TONGUE_HEIGHT = 14.0

# Side rails that lock into the tool battery slot
RAIL_LENGTH = 88.0
RAIL_WIDTH = 7.0
RAIL_HEIGHT = 6.0

# Rail position
RAIL_OFFSET_Y = 24.0
RAIL_Z_OFFSET = BASE_THICKNESS + TONGUE_HEIGHT

# Front stop lip
STOP_LIP_THICKNESS = 8.0
STOP_LIP_HEIGHT = 22.0

# Screw holes
SCREW_HOLE_DIAMETER = 6.0
COUNTERSINK_DIAMETER = 12.0
HOLE_SPACING_X = 80.0
HOLE_SPACING_Y = 45.0

# Reinforcing ribs
RIB_THICKNESS = 8.0
RIB_HEIGHT = 26.0
RIB_LENGTH = 80.0

# =========================================================
# HELPERS
# =========================================================

def move(mesh, x=0, y=0, z=0):
    mesh.apply_translation([x, y, z])
    return mesh

def make_box(name, size, pos):
    m = box(extents=size)
    m.metadata["name"] = name
    return move(m, *pos)

def make_cylinder(name, diameter, height, pos, sections=64):
    m = cylinder(radius=diameter / 2, height=height, sections=sections)
    m.metadata["name"] = name
    return move(m, *pos)

# =========================================================
# CREATE PARTS
# =========================================================

parts = []

# Thick base plate
base = make_box(
    "heavy_base",
    [BASE_LENGTH, BASE_WIDTH, BASE_THICKNESS],
    [0, 0, BASE_THICKNESS / 2]
)
parts.append(base)

# Main tongue that slides into the tool
tongue = make_box(
    "battery_tongue",
    [TONGUE_LENGTH, TONGUE_WIDTH, TONGUE_HEIGHT],
    [0, 0, BASE_THICKNESS + TONGUE_HEIGHT / 2]
)
parts.append(tongue)

# Left rail
left_rail = make_box(
    "left_slide_rail",
    [RAIL_LENGTH, RAIL_WIDTH, RAIL_HEIGHT],
    [0, RAIL_OFFSET_Y, RAIL_Z_OFFSET + RAIL_HEIGHT / 2]
)
parts.append(left_rail)

# Right rail
right_rail = make_box(
    "right_slide_rail",
    [RAIL_LENGTH, RAIL_WIDTH, RAIL_HEIGHT],
    [0, -RAIL_OFFSET_Y, RAIL_Z_OFFSET + RAIL_HEIGHT / 2]
)
parts.append(right_rail)

# Front stop lip
stop_lip = make_box(
    "front_stop_lip",
    [STOP_LIP_THICKNESS, BASE_WIDTH, STOP_LIP_HEIGHT],
    [BASE_LENGTH / 2 - STOP_LIP_THICKNESS / 2, 0, BASE_THICKNESS + STOP_LIP_HEIGHT / 2]
)
parts.append(stop_lip)

# Reinforcement ribs under/behind tongue
rib_left = make_box(
    "left_reinforcement_rib",
    [RIB_LENGTH, RIB_THICKNESS, RIB_HEIGHT],
    [-10, 22, BASE_THICKNESS + RIB_HEIGHT / 2]
)
parts.append(rib_left)

rib_right = make_box(
    "right_reinforcement_rib",
    [RIB_LENGTH, RIB_THICKNESS, RIB_HEIGHT],
    [-10, -22, BASE_THICKNESS + RIB_HEIGHT / 2]
)
parts.append(rib_right)

centre_rib = make_box(
    "centre_reinforcement_rib",
    [RIB_LENGTH, RIB_THICKNESS, RIB_HEIGHT],
    [-10, 0, BASE_THICKNESS + RIB_HEIGHT / 2]
)
parts.append(centre_rib)

# Join all solid parts
holder = union(parts)

# =========================================================
# CUT SCREW HOLES THROUGH BASE
# =========================================================

cutters = []

hole_positions = [
    [-HOLE_SPACING_X / 2, -HOLE_SPACING_Y / 2],
    [-HOLE_SPACING_X / 2,  HOLE_SPACING_Y / 2],
    [ HOLE_SPACING_X / 2, -HOLE_SPACING_Y / 2],
    [ HOLE_SPACING_X / 2,  HOLE_SPACING_Y / 2],
]

for x, y in hole_positions:
    hole = make_cylinder(
        "screw_hole",
        SCREW_HOLE_DIAMETER,
        BASE_THICKNESS + 4,
        [x, y, BASE_THICKNESS / 2]
    )
    cutters.append(hole)

    countersink = make_cylinder(
        "countersink",
        COUNTERSINK_DIAMETER,
        5,
        [x, y, BASE_THICKNESS - 2]
    )
    cutters.append(countersink)

holder = difference([holder] + cutters)

# =========================================================
# EXPORT STL
# =========================================================

output_dir = Path(SAVE_DIR)
output_dir.mkdir(exist_ok=True)

output_path = output_dir / OUTPUT_FILE
holder.export(output_path)

print(f"STL saved to: {output_path}")