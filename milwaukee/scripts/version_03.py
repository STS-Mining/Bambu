from pathlib import Path
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference, union

# =========================================================
# AUTO SAVE SETTINGS
# =========================================================

SAVE_DIR = "milwaukee/stl"
script_name = Path(__file__).stem
OUTPUT_FILE = f"{script_name}.stl"

# =========================================================
# MAIN DIMENSIONS
# =========================================================

BASE_LENGTH = 120.0
BASE_WIDTH = 85.0
BASE_THICKNESS = 25.0      # extra thick for heavy tools
CORNER_RADIUS = 8.0

# Raised centre slide platform
PLATFORM_LENGTH = 74.0
PLATFORM_WIDTH = 50.0
PLATFORM_HEIGHT = 15.0

# Side slide rails
RAIL_LENGTH = 88.0
RAIL_WIDTH = 13.0
RAIL_HEIGHT = 24.0
RAIL_OFFSET_Y = 26.0
RAIL_OFFSET_X = -2.0

# Recessed slots in the rails
SLOT_WIDTH = 7.5
SLOT_DEPTH = 16.0
SLOT_LENGTH = 31.0

# Screw holes
SCREW_HOLE_DIAMETER = 6.0
COUNTERSINK_DIAMETER = 16.0
COUNTERSINK_DEPTH = 6.0
HOLE_SPACING_X = 80.0
HOLE_SPACING_Y = 70.0

# =========================================================
# HELPERS
# =========================================================

def move(mesh, x=0, y=0, z=0):
    mesh.apply_translation([x, y, z])
    return mesh

def make_box(size, pos):
    return move(box(extents=size), *pos)

def make_cylinder(diameter, height, pos, sections=72):
    return move(
        cylinder(radius=diameter / 2, height=height, sections=sections),
        *pos
    )

# =========================================================
# BASE PLATE
# =========================================================

base = make_box(
    [BASE_LENGTH, BASE_WIDTH, BASE_THICKNESS],
    [0, 0, BASE_THICKNESS / 2]
)

# Rounded corner cutters
corner_cutters = []

for sx in [-1, 1]:
    for sy in [-1, 1]:
        square_cut = make_box(
            [CORNER_RADIUS * 2, CORNER_RADIUS * 2, BASE_THICKNESS + 4],
            [
                sx * BASE_LENGTH / 2,
                sy * BASE_WIDTH / 2,
                BASE_THICKNESS / 2
            ]
        )

        round_keep = make_cylinder(
            CORNER_RADIUS * 2,
            BASE_THICKNESS + 6,
            [
                sx * (BASE_LENGTH / 2 - CORNER_RADIUS),
                sy * (BASE_WIDTH / 2 - CORNER_RADIUS),
                BASE_THICKNESS / 2
            ]
        )

        corner_cutters.append(difference([square_cut, round_keep]))

base = difference([base] + corner_cutters)

# =========================================================
# TOP BATTERY-SLIDE SHAPE
# =========================================================

platform = make_box(
    [PLATFORM_LENGTH, PLATFORM_WIDTH, PLATFORM_HEIGHT],
    [0, 0, BASE_THICKNESS + PLATFORM_HEIGHT / 2]
)

left_rail = make_box(
    [RAIL_LENGTH, RAIL_WIDTH, RAIL_HEIGHT],
    [RAIL_OFFSET_X, RAIL_OFFSET_Y, BASE_THICKNESS + RAIL_HEIGHT / 2]
)

right_rail = make_box(
    [RAIL_LENGTH, RAIL_WIDTH, RAIL_HEIGHT],
    [RAIL_OFFSET_X, -RAIL_OFFSET_Y, BASE_THICKNESS + RAIL_HEIGHT / 2]
)

holder = union([base, platform, left_rail, right_rail])

# =========================================================
# CUT THE OPEN U-SHAPE IN THE CENTRE
# =========================================================

rear_opening = make_box(
    [36.0, 38.0, PLATFORM_HEIGHT + 6],
    [-28.0, 0, BASE_THICKNESS + PLATFORM_HEIGHT / 2]
)

front_opening = make_box(
    [32.0, 56.0, PLATFORM_HEIGHT + 6],
    [26.0, 0, BASE_THICKNESS + PLATFORM_HEIGHT / 2]
)

holder = difference([holder, rear_opening, front_opening])

# =========================================================
# CUT LONG RECESSED CHANNELS INTO SIDE RAILS
# =========================================================

slot_cutters = []

for y in [RAIL_OFFSET_Y, -RAIL_OFFSET_Y]:
    # long lower slot
    slot_cutters.append(
        make_box(
            [SLOT_LENGTH, SLOT_WIDTH, SLOT_DEPTH],
            [
                18.0,
                y,
                BASE_THICKNESS + RAIL_HEIGHT / 2
            ]
        )
    )

    # long upper slot
    slot_cutters.append(
        make_box(
            [SLOT_LENGTH, SLOT_WIDTH, SLOT_DEPTH],
            [
                -23.0,
                y,
                BASE_THICKNESS + RAIL_HEIGHT / 2
            ]
        )
    )

    # top triangular/angled-looking relief area
    slot_cutters.append(
        make_box(
            [20.0, SLOT_WIDTH, SLOT_DEPTH],
            [
                -44.0,
                y,
                BASE_THICKNESS + RAIL_HEIGHT - SLOT_DEPTH / 2
            ]
        )
    )

holder = difference([holder] + slot_cutters)

# =========================================================
# ADD SMALL CROSS BARS BETWEEN RAIL SLOT SECTIONS
# =========================================================

crossbars = []

for y in [RAIL_OFFSET_Y, -RAIL_OFFSET_Y]:
    crossbars.append(
        make_box(
            [6.0, RAIL_WIDTH, 4.0],
            [
                -2.0,
                y,
                BASE_THICKNESS + RAIL_HEIGHT / 2
            ]
        )
    )

holder = union([holder] + crossbars)

# =========================================================
# SCREW HOLES AND COUNTERSINKS
# =========================================================

hole_positions = [
    [-HOLE_SPACING_X / 2, -HOLE_SPACING_Y / 2],
    [-HOLE_SPACING_X / 2,  HOLE_SPACING_Y / 2],
    [ HOLE_SPACING_X / 2, -HOLE_SPACING_Y / 2],
    [ HOLE_SPACING_X / 2,  HOLE_SPACING_Y / 2],
]

hole_cutters = []

for x, y in hole_positions:
    hole_cutters.append(
        make_cylinder(
            SCREW_HOLE_DIAMETER,
            BASE_THICKNESS + 10,
            [x, y, BASE_THICKNESS / 2]
        )
    )

    hole_cutters.append(
        make_cylinder(
            COUNTERSINK_DIAMETER,
            COUNTERSINK_DEPTH,
            [x, y, BASE_THICKNESS - COUNTERSINK_DEPTH / 2 + 0.1]
        )
    )

holder = difference([holder] + hole_cutters)

# =========================================================
# EXPORT STL
# =========================================================

output_dir = Path(SAVE_DIR)
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / OUTPUT_FILE
holder.export(output_path)

print(f"STL saved to: {output_path}")