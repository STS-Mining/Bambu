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
BASE_THICKNESS = 25.0

CORNER_RADIUS = 8.0

PLATE_HEIGHT = 18.0

CENTRE_PLATE_LENGTH = 70.0
CENTRE_PLATE_WIDTH = 48.0
CENTRE_PLATE_HEIGHT = 14.0

RAIL_LENGTH = 82.0
RAIL_WIDTH = 13.0
RAIL_HEIGHT = 22.0

RAIL_SLOT_WIDTH = 7.0
RAIL_SLOT_DEPTH = 14.0
RAIL_SLOT_LENGTH = 28.0

RAIL_OFFSET_Y = 25.0
RAIL_OFFSET_X = -4.0

TOP_RAMP_LENGTH = 22.0
TOP_RAMP_HEIGHT = 22.0

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

def make_cylinder(diameter, height, pos, sections=64):
    return move(
        cylinder(radius=diameter / 2, height=height, sections=sections),
        *pos
    )

# =========================================================
# ROUNDED BASE
# =========================================================

base = make_box(
    [BASE_LENGTH, BASE_WIDTH, BASE_THICKNESS],
    [0, 0, BASE_THICKNESS / 2]
)

corner_cutters = []

for x in [-BASE_LENGTH / 2, BASE_LENGTH / 2]:
    for y in [-BASE_WIDTH / 2, BASE_WIDTH / 2]:
        cutter = make_box(
            [CORNER_RADIUS * 2, CORNER_RADIUS * 2, BASE_THICKNESS + 4],
            [x, y, BASE_THICKNESS / 2]
        )
        round_cut = make_cylinder(
            CORNER_RADIUS * 2,
            BASE_THICKNESS + 6,
            [
                x - CORNER_RADIUS if x > 0 else x + CORNER_RADIUS,
                y - CORNER_RADIUS if y > 0 else y + CORNER_RADIUS,
                BASE_THICKNESS / 2
            ]
        )
        corner_cutters.append(difference([cutter, round_cut]))

base = difference([base] + corner_cutters)

# =========================================================
# RAISED CENTRE BATTERY SLIDE BLOCK
# =========================================================

centre_block = make_box(
    [CENTRE_PLATE_LENGTH, CENTRE_PLATE_WIDTH, CENTRE_PLATE_HEIGHT],
    [0, 0, BASE_THICKNESS + CENTRE_PLATE_HEIGHT / 2]
)

# =========================================================
# SIDE RAILS
# =========================================================

left_rail = make_box(
    [RAIL_LENGTH, RAIL_WIDTH, RAIL_HEIGHT],
    [RAIL_OFFSET_X, RAIL_OFFSET_Y, BASE_THICKNESS + RAIL_HEIGHT / 2]
)

right_rail = make_box(
    [RAIL_LENGTH, RAIL_WIDTH, RAIL_HEIGHT],
    [RAIL_OFFSET_X, -RAIL_OFFSET_Y, BASE_THICKNESS + RAIL_HEIGHT / 2]
)

holder = union([base, centre_block, left_rail, right_rail])

# =========================================================
# CUT RECESSED SLOTS INTO RAILS
# =========================================================

cutters = []

slot_x_positions = [-23.0, 20.0]

for y in [RAIL_OFFSET_Y, -RAIL_OFFSET_Y]:
    for x in slot_x_positions:
        slot = make_box(
            [RAIL_SLOT_LENGTH, RAIL_SLOT_WIDTH, RAIL_SLOT_DEPTH],
            [
                x,
                y,
                BASE_THICKNESS + RAIL_HEIGHT / 2
            ]
        )
        cutters.append(slot)

# top angled-looking relief cutouts
for y in [RAIL_OFFSET_Y, -RAIL_OFFSET_Y]:
    top_slot = make_box(
        [20.0, RAIL_SLOT_WIDTH, 18.0],
        [
            -38.0,
            y,
            BASE_THICKNESS + RAIL_HEIGHT - 7.0
        ]
    )
    cutters.append(top_slot)

holder = difference([holder] + cutters)

# =========================================================
# CUT CENTRE OPEN U SHAPE
# =========================================================

centre_cutout = make_box(
    [44.0, 34.0, CENTRE_PLATE_HEIGHT + 6],
    [
        -10.0,
        0,
        BASE_THICKNESS + CENTRE_PLATE_HEIGHT / 2
    ]
)

front_cutout = make_box(
    [28.0, 55.0, CENTRE_PLATE_HEIGHT + 6],
    [
        28.0,
        0,
        BASE_THICKNESS + CENTRE_PLATE_HEIGHT / 2
    ]
)

holder = difference([holder, centre_cutout, front_cutout])

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
    hole = make_cylinder(
        SCREW_HOLE_DIAMETER,
        BASE_THICKNESS + 8,
        [x, y, BASE_THICKNESS / 2]
    )
    hole_cutters.append(hole)

    countersink = make_cylinder(
        COUNTERSINK_DIAMETER,
        COUNTERSINK_DEPTH,
        [x, y, BASE_THICKNESS - COUNTERSINK_DEPTH / 2 + 0.1]
    )
    hole_cutters.append(countersink)

holder = difference([holder] + hole_cutters)

# =========================================================
# EXPORT STL
# =========================================================

output_dir = Path(SAVE_DIR)
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / OUTPUT_FILE
holder.export(output_path)

print(f"STL saved to: {output_path}")