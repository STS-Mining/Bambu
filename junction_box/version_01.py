from pathlib import Path
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference, union
from trimesh.transformations import rotation_matrix

# =========================================================
# JUNCTION BOX SETTINGS - millimetres
# =========================================================

OUTER_LENGTH = 140.0
OUTER_WIDTH = 80.0
OUTER_HEIGHT = 50.0

WALL_THICKNESS = 4.0
BOTTOM_THICKNESS = 4.0

CORNER_RADIUS = 3.0

HOLE_DIAMETER = 20.0
HOLE_Z = 25.0
FRONT_HOLE_X_SPACING = 40.0

# =========================================================
# LID SETTINGS
# =========================================================

LID_THICKNESS = 4.0
LID_OVERHANG = 1.5

# Small raised lip under lid to locate inside box
LID_LOCATING_LIP_HEIGHT = 3.0
LID_LOCATING_LIP_THICKNESS = 2.0
LID_CLEARANCE = 0.5

# Screw settings
SCREW_HOLE_DIAMETER = 3.2      # suits M3 screw clearance
SCREW_POST_DIAMETER = 9.0
SCREW_POST_HOLE_DIAMETER = 2.6 # pilot hole for M3 screw
SCREW_POST_HEIGHT = OUTER_HEIGHT - BOTTOM_THICKNESS - 3.0

SCREW_OFFSET_X = 12.0
SCREW_OFFSET_Y = 12.0

COUNTERSINK_DIAMETER = 8.0
COUNTERSINK_DEPTH = 2.0

# Output
SAVE_DIR = Path("junction_box")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
script_name = Path(__file__).stem

BASE_OUTPUT_FILE = SAVE_DIR / f"{script_name}_base.stl"
LID_OUTPUT_FILE = SAVE_DIR / f"{script_name}_lid.stl"

# =========================================================
# HELPERS
# =========================================================

def cyl_z(radius, height, x, y, z, sections=64):
    c = cylinder(radius=radius, height=height, sections=sections)
    c.apply_translation([x, y, z])
    return c


def cyl_y(radius, height, x, y, z, sections=64):
    c = cylinder(radius=radius, height=height, sections=sections)
    c.apply_transform(rotation_matrix(1.5708, [1, 0, 0]))
    c.apply_translation([x, y, z])
    return c


def rounded_box(extents, radius=2.0, center=(0, 0, 0)):
    """
    Makes a slightly rounded box using convex hull of corner spheres.
    Good enough for 3D-printable rounded edges.
    """
    x, y, z = extents
    cx, cy, cz = center

    core_x = x - radius * 2
    core_y = y - radius * 2
    core_z = z - radius * 2

    parts = []

    for sx in [-1, 1]:
        for sy in [-1, 1]:
            for sz in [-1, 1]:
                s = trimesh.creation.icosphere(subdivisions=2, radius=radius)
                s.apply_translation([
                    cx + sx * core_x / 2,
                    cy + sy * core_y / 2,
                    cz + sz * core_z / 2
                ])
                parts.append(s)

    return trimesh.convex.convex_hull(trimesh.util.concatenate(parts))


# =========================================================
# CREATE BASE
# =========================================================

outer = rounded_box(
    [OUTER_LENGTH, OUTER_WIDTH, OUTER_HEIGHT],
    radius=CORNER_RADIUS,
    center=[0, 0, OUTER_HEIGHT / 2]
)

inner = box(extents=[
    OUTER_LENGTH - WALL_THICKNESS * 2,
    OUTER_WIDTH - WALL_THICKNESS * 2,
    OUTER_HEIGHT
])

inner.apply_translation([
    0,
    0,
    BOTTOM_THICKNESS + OUTER_HEIGHT / 2
])

base = difference([outer, inner])

# =========================================================
# SIDE CABLE HOLES
# =========================================================

hole_radius = HOLE_DIAMETER / 2
hole_depth = OUTER_WIDTH + 20

holes = []

# Front side: two holes
for x in [-FRONT_HOLE_X_SPACING / 2, FRONT_HOLE_X_SPACING / 2]:
    holes.append(cyl_y(hole_radius, hole_depth, x, -OUTER_WIDTH / 2, HOLE_Z))

# Back side: one centered hole
holes.append(cyl_y(hole_radius, hole_depth, 0, OUTER_WIDTH / 2, HOLE_Z))

base = difference([base] + holes)

# =========================================================
# SCREW POSTS IN BASE
# =========================================================

post_positions = [
    (-OUTER_LENGTH / 2 + SCREW_OFFSET_X, -OUTER_WIDTH / 2 + SCREW_OFFSET_Y),
    ( OUTER_LENGTH / 2 - SCREW_OFFSET_X, -OUTER_WIDTH / 2 + SCREW_OFFSET_Y),
    (-OUTER_LENGTH / 2 + SCREW_OFFSET_X,  OUTER_WIDTH / 2 - SCREW_OFFSET_Y),
    ( OUTER_LENGTH / 2 - SCREW_OFFSET_X,  OUTER_WIDTH / 2 - SCREW_OFFSET_Y),
]

posts = []
post_holes = []

for x, y in post_positions:
    posts.append(
        cyl_z(
            SCREW_POST_DIAMETER / 2,
            SCREW_POST_HEIGHT,
            x,
            y,
            BOTTOM_THICKNESS + SCREW_POST_HEIGHT / 2
        )
    )

    post_holes.append(
        cyl_z(
            SCREW_POST_HOLE_DIAMETER / 2,
            SCREW_POST_HEIGHT + 4,
            x,
            y,
            BOTTOM_THICKNESS + SCREW_POST_HEIGHT / 2
        )
    )

base = union([base] + posts)
base = difference([base] + post_holes)

# =========================================================
# CREATE LID
# =========================================================

lid_length = OUTER_LENGTH + LID_OVERHANG * 2
lid_width = OUTER_WIDTH + LID_OVERHANG * 2

lid = rounded_box(
    [lid_length, lid_width, LID_THICKNESS],
    radius=CORNER_RADIUS,
    center=[0, 0, LID_THICKNESS / 2]
)

# Locating lip under lid
lip_outer = box(extents=[
    OUTER_LENGTH - LID_CLEARANCE,
    OUTER_WIDTH - LID_CLEARANCE,
    LID_LOCATING_LIP_HEIGHT
])
lip_outer.apply_translation([0, 0, -LID_LOCATING_LIP_HEIGHT / 2])

lip_inner = box(extents=[
    OUTER_LENGTH - WALL_THICKNESS * 2 - LID_LOCATING_LIP_THICKNESS,
    OUTER_WIDTH - WALL_THICKNESS * 2 - LID_LOCATING_LIP_THICKNESS,
    LID_LOCATING_LIP_HEIGHT + 1
])
lip_inner.apply_translation([0, 0, -LID_LOCATING_LIP_HEIGHT / 2])

lip = difference([lip_outer, lip_inner])

lid = union([lid, lip])

# Screw holes through lid with countersunk tops
lid_screw_holes = []

for x, y in post_positions:
    # Main screw clearance hole
    lid_screw_holes.append(
        cyl_z(
            SCREW_HOLE_DIAMETER / 2,
            LID_THICKNESS + LID_LOCATING_LIP_HEIGHT + 8,
            x,
            y,
            0
        )
    )

    # Countersink / screw head recess from top of lid
    lid_screw_holes.append(
        cyl_z(
            COUNTERSINK_DIAMETER / 2,
            COUNTERSINK_DEPTH,
            x,
            y,
            LID_THICKNESS - COUNTERSINK_DEPTH / 2
        )
    )

lid = difference([lid] + lid_screw_holes)

# =========================================================
# EXPORT
# =========================================================

base.remove_unreferenced_vertices()
lid.remove_unreferenced_vertices()

base.export(BASE_OUTPUT_FILE)
lid.export(LID_OUTPUT_FILE)

print(f"Base STL saved to: {BASE_OUTPUT_FILE}")
print(f"Lid STL saved to:  {LID_OUTPUT_FILE}")