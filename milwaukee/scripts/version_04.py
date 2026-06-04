from pathlib import Path
import math
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference, union

# =========================================================
# Milwaukee M18 Tool Holder - Heavy Base Version
# Recreated from the supplied 3MF as a parametric Python model.
# Saves the STL using the same name as this script.
# =========================================================

SAVE_DIR = "milwaukee/stl"
script_name = Path(__file__).stem
OUTPUT_FILE = f"{script_name}.stl"

# =========================================================
# MAIN SIZE SETTINGS
# =========================================================

# Uploaded 3MF measured approx: 56.75 x 74.00 x 26.68 mm.
# This script keeps the slide section close, but makes the base heavier.
BASE_LENGTH = 74.0
BASE_WIDTH = 57.0
BASE_THICKNESS = 18.0       # change to 22.0 or 25.0 for very heavy tools
BASE_CORNER_RADIUS = 3.0

TOP_PLATE_LENGTH = 74.0
TOP_PLATE_WIDTH = 57.0
TOP_PLATE_THICKNESS = 4.0
TOP_PLATE_CORNER_RADIUS = 3.0

# Two main Milwaukee slide rails
RAIL_LENGTH = 61.0
RAIL_WIDTH = 8.5
RAIL_HEIGHT = 13.5
RAIL_OFFSET_Y = 20.5
RAIL_ROUND_RADIUS = 4.2

# Raised rear guide/stop blocks
REAR_STOP_LENGTH = 14.0
REAR_STOP_WIDTH = 8.5
REAR_STOP_HEIGHT = 17.0
REAR_STOP_X = -24.0

# Recessed channels beside the rails
SIDE_CHANNEL_LENGTH = 67.0
SIDE_CHANNEL_WIDTH = 4.0
SIDE_CHANNEL_HEIGHT = 4.0
SIDE_CHANNEL_OFFSET_Y = 13.0

# Screw holes
SCREW_HOLE_DIAMETER = 6.0
COUNTERSINK_DIAMETER = 15.0
COUNTERSINK_DEPTH = 4.5
HOLE_X_POSITIONS = [-18.0, 18.0]
HOLE_Y = 0.0

# Front engraved text is optional. Keep False for easier printing.
ADD_FRONT_TEXT = False
FRONT_TEXT = "Urban 3D"

# =========================================================
# HELPERS
# =========================================================

def move(mesh, x=0, y=0, z=0):
    mesh.apply_translation([x, y, z])
    return mesh


def make_box(size, pos):
    return move(box(extents=size), *pos)


def make_cylinder(diameter, height, pos, sections=96):
    return move(cylinder(radius=diameter / 2, height=height, sections=sections), *pos)


def rounded_rect_box(length, width, height, radius, z_base):
    """Create a rectangular slab with rounded outside corners."""
    slab = make_box([length, width, height], [0, 0, z_base + height / 2])

    cutters = []
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            corner_square = make_box(
                [radius * 2, radius * 2, height + 4],
                [sx * length / 2, sy * width / 2, z_base + height / 2],
            )
            round_keep = make_cylinder(
                radius * 2,
                height + 6,
                [sx * (length / 2 - radius), sy * (width / 2 - radius), z_base + height / 2],
            )
            cutters.append(difference([corner_square, round_keep]))

    return difference([slab] + cutters)


def rounded_bar(length, width, height, radius, x, y, z_base):
    """Create a long rounded-ended bar running along X."""
    centre_len = max(0.1, length - width)
    middle = make_box([centre_len, width, height], [x, y, z_base + height / 2])
    left_end = make_cylinder(width, height, [x - centre_len / 2, y, z_base + height / 2])
    right_end = make_cylinder(width, height, [x + centre_len / 2, y, z_base + height / 2])
    return union([middle, left_end, right_end])

# =========================================================
# BUILD MODEL
# =========================================================

parts = []

base = rounded_rect_box(BASE_LENGTH, BASE_WIDTH, BASE_THICKNESS, BASE_CORNER_RADIUS, 0)
parts.append(base)

top_z = BASE_THICKNESS
top_plate = rounded_rect_box(
    TOP_PLATE_LENGTH,
    TOP_PLATE_WIDTH,
    TOP_PLATE_THICKNESS,
    TOP_PLATE_CORNER_RADIUS,
    top_z,
)
parts.append(top_plate)

rail_z = BASE_THICKNESS + TOP_PLATE_THICKNESS
left_rail = rounded_bar(RAIL_LENGTH, RAIL_WIDTH, RAIL_HEIGHT, RAIL_ROUND_RADIUS, 0, RAIL_OFFSET_Y, rail_z)
right_rail = rounded_bar(RAIL_LENGTH, RAIL_WIDTH, RAIL_HEIGHT, RAIL_ROUND_RADIUS, 0, -RAIL_OFFSET_Y, rail_z)
parts.extend([left_rail, right_rail])

# Rear upstanding stops/guides at the back of each rail
rear_left = rounded_bar(
    REAR_STOP_LENGTH,
    REAR_STOP_WIDTH,
    REAR_STOP_HEIGHT,
    REAR_STOP_WIDTH / 2,
    REAR_STOP_X,
    RAIL_OFFSET_Y,
    rail_z,
)
rear_right = rounded_bar(
    REAR_STOP_LENGTH,
    REAR_STOP_WIDTH,
    REAR_STOP_HEIGHT,
    REAR_STOP_WIDTH / 2,
    REAR_STOP_X,
    -RAIL_OFFSET_Y,
    rail_z,
)
parts.extend([rear_left, rear_right])

holder = union(parts)

# =========================================================
# CUT RECESSES, CLEARANCES, HOLES
# =========================================================

cutters = []

# shallow side channels under/inside the rail area
cutters.append(
    make_box(
        [SIDE_CHANNEL_LENGTH, SIDE_CHANNEL_WIDTH, SIDE_CHANNEL_HEIGHT],
        [0, SIDE_CHANNEL_OFFSET_Y, BASE_THICKNESS + SIDE_CHANNEL_HEIGHT / 2],
    )
)
cutters.append(
    make_box(
        [SIDE_CHANNEL_LENGTH, SIDE_CHANNEL_WIDTH, SIDE_CHANNEL_HEIGHT],
        [0, -SIDE_CHANNEL_OFFSET_Y, BASE_THICKNESS + SIDE_CHANNEL_HEIGHT / 2],
    )
)

# open centre clearance between the rear guide blocks
cutters.append(
    make_box(
        [25.0, 26.0, REAR_STOP_HEIGHT + 8],
        [REAR_STOP_X + 2.0, 0, rail_z + REAR_STOP_HEIGHT / 2],
    )
)

# screw holes and countersinks
for x in HOLE_X_POSITIONS:
    cutters.append(
        make_cylinder(
            SCREW_HOLE_DIAMETER,
            BASE_THICKNESS + TOP_PLATE_THICKNESS + 10,
            [x, HOLE_Y, (BASE_THICKNESS + TOP_PLATE_THICKNESS) / 2],
        )
    )
    cutters.append(
        make_cylinder(
            COUNTERSINK_DIAMETER,
            COUNTERSINK_DEPTH,
            [x, HOLE_Y, BASE_THICKNESS + TOP_PLATE_THICKNESS - COUNTERSINK_DEPTH / 2 + 0.1],
        )
    )

holder = difference([holder] + cutters)

# =========================================================
# OPTIONAL FRONT TEXT ENGRAVING
# =========================================================

if ADD_FRONT_TEXT:
    try:
        text_mesh = trimesh.creation.text(FRONT_TEXT, font_size=7, height=1.0)
        text_mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90), [1, 0, 0]))
        text_mesh.apply_translation([0, -BASE_WIDTH / 2 - 0.05, BASE_THICKNESS / 2])
        holder = difference([holder, text_mesh])
    except Exception as e:
        print(f"Text engraving skipped: {e}")

# Clean up mesh
holder.update_faces(holder.unique_faces())
holder.remove_unreferenced_vertices()
holder.fix_normals()

# =========================================================
# EXPORT STL
# =========================================================

output_dir = Path(SAVE_DIR)
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / OUTPUT_FILE
holder.export(output_path)

print(f"STL saved to: {output_path}")
print(f"Overall size approx: {holder.extents[0]:.2f} x {holder.extents[1]:.2f} x {holder.extents[2]:.2f} mm")
