from pathlib import Path
import math
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon, cylinder, box
from trimesh.boolean import union, difference
from trimesh.transformations import rotation_matrix


# =========================================================
# USER SETTINGS
# =========================================================

ARM_LENGTH = 150.0
ARM_WIDTH = 30.0
THICKNESS = 8.0

V_ANGLE = 40.0

CENTER_HOLE = 6.0
END_HOLE = 23.0

UPRIGHT_HEIGHT = 60.0
UPRIGHT_THICKNESS = 8.0

EDGE_OFFSET = 20.0

SAVE_DIR = "stl"
script_name = Path(__file__).stem
OUTPUT_FILE = f"{script_name}.stl"


# =========================================================
# CREATE V SHAPE
# =========================================================

def create_arm(angle_deg):
    angle = math.radians(angle_deg)

    rect = Polygon([
        (0, -ARM_WIDTH / 2),
        (ARM_LENGTH, -ARM_WIDTH / 2),
        (ARM_LENGTH, ARM_WIDTH / 2),
        (0, ARM_WIDTH / 2)
    ])

    pts = []

    for x, y in rect.exterior.coords:
        xr = x * math.cos(angle) - y * math.sin(angle)
        yr = x * math.sin(angle) + y * math.cos(angle)
        pts.append((xr, yr))

    return Polygon(pts)


upper_angle = math.radians(V_ANGLE / 2)
lower_angle = math.radians(-V_ANGLE / 2)

arm1 = create_arm(+V_ANGLE / 2)
arm2 = create_arm(-V_ANGLE / 2)

shape_2d = unary_union([arm1, arm2])

body = extrude_polygon(
    shape_2d,
    THICKNESS,
    engine="earcut"
)


# =========================================================
# CENTER 6MM HOLE
# =========================================================

center_hole = cylinder(
    radius=CENTER_HOLE / 2,
    height=THICKNESS + 2,
    sections=64
)

center_hole.apply_translation([
    0,
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
# UPRIGHT PLATE ON UPPER ARM
# =========================================================

# Local position on upper arm
upright_local_x = ARM_LENGTH - (UPRIGHT_THICKNESS / 2)
upright_local_y = 0
upright_local_z = THICKNESS + (UPRIGHT_HEIGHT / 2)

# Convert local arm position to world position
upright_x = upright_local_x * math.cos(upper_angle)
upright_y = upright_local_x * math.sin(upper_angle)

upright = box(
    extents=[
        UPRIGHT_THICKNESS,   # thickness along the arm
        ARM_WIDTH,           # width across the arm
        UPRIGHT_HEIGHT       # height upward
    ]
)

upright.apply_translation([
    upright_local_x,
    upright_local_y,
    upright_local_z
])

upright.apply_transform(
    rotation_matrix(
        upper_angle,
        [0, 0, 1]
    )
)


# =========================================================
# 23MM HOLE IN UPRIGHT PLATE
# =========================================================

upright_hole = cylinder(
    radius=END_HOLE / 2,
    height=UPRIGHT_THICKNESS + 10,
    sections=128
)

# Rotate cylinder so it cuts through the upright thickness
upright_hole.apply_transform(
    rotation_matrix(
        math.radians(90),
        [0, 1, 0]
    )
)

# Hole centered left/right and top/bottom in upright
upright_hole.apply_translation([
    upright_local_x,
    0,
    THICKNESS + (UPRIGHT_HEIGHT / 2)
])

upright_hole.apply_transform(
    rotation_matrix(
        upper_angle,
        [0, 0, 1]
    )
)


# =========================================================
# COMBINE AND CUT HOLES
# =========================================================

combined = union(
    [body, upright],
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