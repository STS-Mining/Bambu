from pathlib import Path
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference, union
from trimesh.transformations import translation_matrix

# =========================================================
# WATERPROOF BOX SETTINGS - millimetres
# =========================================================

OUTER_LENGTH = 220.0
OUTER_WIDTH = 220.0
BASE_HEIGHT = 70.0

WALL_THICKNESS = 4.0
BOTTOM_THICKNESS = 4.0

LID_THICKNESS = 5.0
LID_OVERHANG = 4.0

GASKET_GROOVE_WIDTH = 4.0
GASKET_GROOVE_DEPTH = 2.0

SCREW_HOLE_DIAMETER = 4.5
SCREW_POST_DIAMETER = 12.0
SCREW_POST_HOLE_DIAMETER = 3.0
SCREW_POST_HEIGHT = BASE_HEIGHT - 6.0

SCREW_OFFSET = 18.0

SAVE_DIR = Path("nbn_box/stl")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
script_name = Path(__file__).stem
BASE_FILE = SAVE_DIR / f"{script_name}_base.stl"
LID_FILE = SAVE_DIR / f"{script_name}_lid.stl"

# =========================================================
# HELPERS
# =========================================================

def move(mesh, x=0, y=0, z=0):
    mesh.apply_transform(translation_matrix([x, y, z]))
    return mesh

def make_cylinder(diameter, height, x, y, z, sections=64):
    cyl = cylinder(
        radius=diameter / 2,
        height=height,
        sections=sections
    )
    return move(cyl, x, y, z)

# =========================================================
# BASE
# =========================================================

outer_base = box(extents=[OUTER_LENGTH, OUTER_WIDTH, BASE_HEIGHT])
move(outer_base, 0, 0, BASE_HEIGHT / 2)

inner_void = box(extents=[
    OUTER_LENGTH - WALL_THICKNESS * 2,
    OUTER_WIDTH - WALL_THICKNESS * 2,
    BASE_HEIGHT
])
move(inner_void, 0, 0, BOTTOM_THICKNESS + BASE_HEIGHT / 2)

base = difference([outer_base, inner_void])

# Screw posts inside base
post_positions = [
    (-OUTER_LENGTH / 2 + SCREW_OFFSET, -OUTER_WIDTH / 2 + SCREW_OFFSET),
    ( OUTER_LENGTH / 2 - SCREW_OFFSET, -OUTER_WIDTH / 2 + SCREW_OFFSET),
    (-OUTER_LENGTH / 2 + SCREW_OFFSET,  OUTER_WIDTH / 2 - SCREW_OFFSET),
    ( OUTER_LENGTH / 2 - SCREW_OFFSET,  OUTER_WIDTH / 2 - SCREW_OFFSET),
]

posts = []

for x, y in post_positions:
    post = make_cylinder(
        SCREW_POST_DIAMETER,
        SCREW_POST_HEIGHT,
        x,
        y,
        BOTTOM_THICKNESS + SCREW_POST_HEIGHT / 2
    )

    hole = make_cylinder(
        SCREW_POST_HOLE_DIAMETER,
        SCREW_POST_HEIGHT + 2,
        x,
        y,
        BOTTOM_THICKNESS + SCREW_POST_HEIGHT / 2
    )

    post = difference([post, hole])
    posts.append(post)

base = union([base] + posts)

# =========================================================
# LID WITH INTERLOCKING INNER ROUTERED EDGE
# =========================================================

LID_LIP_HEIGHT = 5.0
LID_LIP_THICKNESS = 3.0
LID_CLEARANCE = 0.4

lid_length = OUTER_LENGTH + LID_OVERHANG * 2
lid_width = OUTER_WIDTH + LID_OVERHANG * 2

lid_top = box(extents=[lid_length, lid_width, LID_THICKNESS])
move(lid_top, 0, 0, LID_THICKNESS / 2)

# Raised inner lip that goes down inside the box
lip_outer = box(extents=[
    OUTER_LENGTH - WALL_THICKNESS * 2 - LID_CLEARANCE,
    OUTER_WIDTH - WALL_THICKNESS * 2 - LID_CLEARANCE,
    LID_LIP_HEIGHT
])
move(lip_outer, 0, 0, -LID_LIP_HEIGHT / 2)

lip_inner = box(extents=[
    OUTER_LENGTH - WALL_THICKNESS * 2 - LID_CLEARANCE - LID_LIP_THICKNESS * 2,
    OUTER_WIDTH - WALL_THICKNESS * 2 - LID_CLEARANCE - LID_LIP_THICKNESS * 2,
    LID_LIP_HEIGHT + 2
])
move(lip_inner, 0, 0, -LID_LIP_HEIGHT / 2)

lid_lip = difference([lip_outer, lip_inner])

lid = union([lid_top, lid_lip])

# Gasket/routered groove around lip
outer_groove = box(extents=[
    OUTER_LENGTH - 2,
    OUTER_WIDTH - 2,
    GASKET_GROOVE_DEPTH
])
move(outer_groove, 0, 0, 0.5)

inner_groove = box(extents=[
    OUTER_LENGTH - 2 - GASKET_GROOVE_WIDTH * 2,
    OUTER_WIDTH - 2 - GASKET_GROOVE_WIDTH * 2,
    GASKET_GROOVE_DEPTH + 1
])
move(inner_groove, 0, 0, 0.5)

gasket_cut = difference([outer_groove, inner_groove])
lid = difference([lid, gasket_cut])

# Screw holes through lid
lid_holes = []

for x, y in post_positions:
    hole = make_cylinder(
        SCREW_HOLE_DIAMETER,
        LID_THICKNESS + LID_LIP_HEIGHT + 8,
        x,
        y,
        0
    )
    lid_holes.append(hole)

lid = difference([lid] + lid_holes)

# =========================================================
# EXPORT
# =========================================================


base_file = SAVE_DIR / f"{script_name}_base.stl"
lid_file = SAVE_DIR / f"{script_name}_lid.stl"

base.export(base_file)
lid.export(lid_file)

print("STL files created:")
print(base_file)
print(lid_file)