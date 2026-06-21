from pathlib import Path
import math
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon, cylinder
from trimesh.boolean import union, difference
from trimesh.transformations import rotation_matrix

# =========================================================
# USER SETTINGS
# =========================================================

ARM_LENGTH = 120.0
ARM_WIDTH = 35.0
THICKNESS = ARM_WIDTH * 0.25

V_ANGLE = 70.0

CENTER_HOLE = 6.0
END_HOLE = 23.0

CENTER_HOLE_OFFSET = 25.0

UPRIGHT_HEIGHT = 90.0
UPRIGHT_THICKNESS = THICKNESS * 1.25

EDGE_OFFSET = 20.0

UPRIGHT_LEAN_ANGLE = 30.0
UPRIGHT_OVERLAP = UPRIGHT_LEAN_ANGLE * 0.3

LOWER_END_RADIUS = ARM_WIDTH / 2
UPRIGHT_TOP_RADIUS = 6.0

INNER_V_RADIUS = 1.0
OUTER_V_RADIUS = ARM_WIDTH / 2

# =========================================================
# TOP ARM SUPPORT SETTINGS
# =========================================================

SUPPORT_BACK_FROM_UPRIGHT = 75.0
SUPPORT_HEIGHT = 20.0
SUPPORT_WIDTH = ARM_WIDTH
SUPPORT_OVERLAP = 2.0

# =========================================================
# AUTO SAVE SETTINGS
# =========================================================

SAVE_DIR = "K200/stl"
script_name = Path(__file__).stem
OUTPUT_FILE = f"{script_name}.stl"

# =========================================================
# CREATE ARM SHAPES
# =========================================================

def create_arm(angle_deg, rounded_end=False):
    angle = math.radians(angle_deg)

    if rounded_end:
        r = LOWER_END_RADIUS
        cx = ARM_LENGTH - r

        pts = [(0, -ARM_WIDTH / 2), (cx, -ARM_WIDTH / 2)]

        for a in np.linspace(-90, 90, 32):
            ar = math.radians(a)
            pts.append((cx + r * math.cos(ar), r * math.sin(ar)))

        pts += [(0, ARM_WIDTH / 2), (0, -ARM_WIDTH / 2)]
    else:
        pts = [
            (0, -ARM_WIDTH / 2),
            (ARM_LENGTH, -ARM_WIDTH / 2),
            (ARM_LENGTH, ARM_WIDTH / 2),
            (0, ARM_WIDTH / 2),
            (0, -ARM_WIDTH / 2)
        ]

    rotated = []

    for x, y in pts:
        xr = x * math.cos(angle) - y * math.sin(angle)
        yr = x * math.sin(angle) + y * math.cos(angle)
        rotated.append((xr, yr))

    return Polygon(rotated)


upper_angle = math.radians(V_ANGLE / 2)
lower_angle = math.radians(-V_ANGLE / 2)

arm1 = create_arm(+V_ANGLE / 2, rounded_end=False)
arm2 = create_arm(-V_ANGLE / 2, rounded_end=True)

shape_2d = unary_union([arm1, arm2])

outer_round = Point(0, 0).buffer(OUTER_V_RADIUS, resolution=96)

shape_2d = unary_union([shape_2d, outer_round])

shape_2d = shape_2d.buffer(INNER_V_RADIUS, join_style=1).buffer(
    -INNER_V_RADIUS,
    join_style=1
)

body = extrude_polygon(shape_2d, THICKNESS, engine="earcut")

# =========================================================
# CENTER 6MM HOLE
# =========================================================

center_hole = cylinder(
    radius=CENTER_HOLE / 2,
    height=THICKNESS + 2,
    sections=64
)

center_hole_x = OUTER_V_RADIUS - CENTER_HOLE_OFFSET

center_hole.apply_translation([
    center_hole_x,
    0,
    THICKNESS / 2
])

# =========================================================
# LOWER ARM 23MM HOLE
# =========================================================

hole_distance = ARM_LENGTH - EDGE_OFFSET

lower_x = hole_distance * math.cos(lower_angle)
lower_y = hole_distance * math.sin(lower_angle)

end_hole = cylinder(
    radius=END_HOLE / 2,
    height=THICKNESS + 2,
    sections=128
)

end_hole.apply_translation([
    lower_x,
    lower_y,
    THICKNESS / 2
])

# =========================================================
# UPRIGHT PLATE WITH ROUNDED TOP
# =========================================================

def create_rounded_top_upright():
    t = UPRIGHT_THICKNESS
    h = UPRIGHT_HEIGHT
    r = min(UPRIGHT_TOP_RADIUS, t / 2, h / 2)

    left = -t / 2
    right = t / 2
    bottom = 0
    top = h

    pts = [
        (left, bottom),
        (right, bottom),
        (right, top - r),
    ]

    for a in np.linspace(0, 90, 16):
        ar = math.radians(a)
        pts.append((
            right - r + r * math.cos(ar),
            top - r + r * math.sin(ar)
        ))

    pts.append((left + r, top))

    for a in np.linspace(90, 180, 16):
        ar = math.radians(a)
        pts.append((
            left + r + r * math.cos(ar),
            top - r + r * math.sin(ar)
        ))

    pts.append((left, bottom))

    profile = Polygon(pts)

    upright_mesh = extrude_polygon(profile, ARM_WIDTH, engine="earcut")

    upright_mesh.apply_transform(
        rotation_matrix(math.radians(90), [1, 0, 0])
    )

    upright_mesh.apply_translation([
        0,
        ARM_WIDTH / 2,
        0
    ])

    return upright_mesh


upright_local_x = ARM_LENGTH - (UPRIGHT_THICKNESS / 2)
upright_local_y = 0
upright_local_z = THICKNESS - UPRIGHT_OVERLAP

upright_pivot = [
    upright_local_x - (UPRIGHT_THICKNESS / 2),
    0,
    THICKNESS - UPRIGHT_OVERLAP
]

upright = create_rounded_top_upright()

upright.apply_translation([
    upright_local_x,
    upright_local_y,
    upright_local_z
])

upright.apply_transform(
    rotation_matrix(
        math.radians(-UPRIGHT_LEAN_ANGLE),
        [0, 1, 0],
        point=upright_pivot
    )
)

upright.apply_transform(
    rotation_matrix(upper_angle, [0, 0, 1])
)

# =========================================================
# FIXED TOP ARM SUPPORT GUSSET
# =========================================================

def rotate_y_point(point, angle_deg, pivot):
    angle = math.radians(angle_deg)

    x, y, z = point
    px, py, pz = pivot

    x -= px
    z -= pz

    xr = x * math.cos(angle) + z * math.sin(angle)
    zr = -x * math.sin(angle) + z * math.cos(angle)

    return [
        xr + px,
        y + py,
        zr + pz
    ]


def create_top_arm_support():
    upright_base_x = ARM_LENGTH - UPRIGHT_THICKNESS

    bottom_back_x = upright_base_x - SUPPORT_BACK_FROM_UPRIGHT
    bottom_front_x = upright_base_x + SUPPORT_OVERLAP

    bottom_z = THICKNESS - SUPPORT_OVERLAP

    top_point = [
        upright_base_x + SUPPORT_OVERLAP,
        0,
        THICKNESS + SUPPORT_HEIGHT
    ]

    top_point = rotate_y_point(
        top_point,
        -UPRIGHT_LEAN_ANGLE,
        upright_pivot
    )

    y1 = -SUPPORT_WIDTH / 2
    y2 = SUPPORT_WIDTH / 2

    vertices = [
        [bottom_back_x,  y1, bottom_z],
        [bottom_front_x, y1, bottom_z],
        [top_point[0],   y1, top_point[2]],

        [bottom_back_x,  y2, bottom_z],
        [bottom_front_x, y2, bottom_z],
        [top_point[0],   y2, top_point[2]],
    ]

    faces = [
        [0, 1, 2],
        [3, 5, 4],

        [0, 3, 4],
        [0, 4, 1],

        [1, 4, 5],
        [1, 5, 2],

        [2, 5, 3],
        [2, 3, 0],
    ]

    support = trimesh.Trimesh(
        vertices=vertices,
        faces=faces,
        process=True
    )

    support.apply_transform(
        rotation_matrix(upper_angle, [0, 0, 1])
    )

    return support


top_arm_support = create_top_arm_support()

# =========================================================
# UPRIGHT 23MM HOLE
# =========================================================

upright_hole = cylinder(
    radius=END_HOLE / 2,
    height=UPRIGHT_THICKNESS + 30,
    sections=128
)

upright_hole.apply_transform(
    rotation_matrix(math.radians(90), [0, 1, 0])
)

upright_hole.apply_translation([
    upright_local_x,
    0,
    THICKNESS - UPRIGHT_OVERLAP + (UPRIGHT_HEIGHT / 2)
])

upright_hole.apply_transform(
    rotation_matrix(
        math.radians(-UPRIGHT_LEAN_ANGLE),
        [0, 1, 0],
        point=upright_pivot
    )
)

upright_hole.apply_transform(
    rotation_matrix(upper_angle, [0, 0, 1])
)

# =========================================================
# COMBINE AND CUT
# =========================================================

combined = union(
    [body, upright, top_arm_support],
    engine="manifold"
)

final = difference(
    [
        combined,
        center_hole,
        end_hole,
        upright_hole
    ],
    engine="manifold"
)

# =========================================================
# EXPORT STL
# =========================================================

output_path = Path(SAVE_DIR) / OUTPUT_FILE
output_path.parent.mkdir(parents=True, exist_ok=True)

final.export(str(output_path))

print(f"✅ STL saved as: {output_path}")