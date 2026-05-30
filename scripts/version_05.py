from pathlib import Path
import math
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon, cylinder, box
from trimesh.boolean import union, difference


# =========================================================
# USER SETTINGS
# =========================================================

ARM_LENGTH = 140.0
ARM_WIDTH = 30.0
THICKNESS = 8.0

V_ANGLE = 40.0          # Included angle in TOP VIEW

CENTER_HOLE = 6.0
END_HOLE = 23.0

UPRIGHT_HEIGHT = 50.0
UPRIGHT_THICKNESS = 6.0

# =========================================================
# AUTO SAVE SETTINGS
# =========================================================
SAVE_DIR = "stl"                    # Folder to save into
# Automatically use the current Python filename (without .py)
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

arm1 = create_arm(+V_ANGLE / 2)
arm2 = create_arm(-V_ANGLE / 2)

shape_2d = unary_union([arm1, arm2])

body = extrude_polygon(
    shape_2d,
    THICKNESS,
    engine="earcut"
)

# =========================================================
# CENTER HOLE
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
# LOWER ARM END HOLE
# =========================================================

lower_angle = math.radians(-V_ANGLE / 2)

lower_x = ARM_LENGTH * math.cos(lower_angle)
lower_y = ARM_LENGTH * math.sin(lower_angle)

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
# UPRIGHT PLATE - ROTATED TO MATCH ARM ANGLE
# =========================================================

upper_angle = math.radians(V_ANGLE / 2)

upper_x = ARM_LENGTH * math.cos(upper_angle)
upper_y = ARM_LENGTH * math.sin(upper_angle)

upright = box(
    extents=[
        ARM_WIDTH,
        UPRIGHT_THICKNESS,
        UPRIGHT_HEIGHT
    ]
)

# Move upright so its base sits on top of the arm
upright.apply_translation([
    0,
    0,
    UPRIGHT_HEIGHT / 2 + THICKNESS
])

# Rotate upright around Z so it lines up with the V arm
upright.apply_transform(
    trimesh.transformations.rotation_matrix(
        upper_angle,
        [0, 0, 1]
    )
)

# Move it to the end of the upper arm
upright.apply_translation([
    upper_x,
    upper_y,
    0
])

# =========================================================
# UPRIGHT HOLE - ROTATED WITH UPRIGHT
# =========================================================

upright_hole = cylinder(
    radius=END_HOLE / 2,
    height=UPRIGHT_THICKNESS + 20,
    sections=128
)

# Rotate cylinder so it cuts through the upright plate thickness
upright_hole.apply_transform(
    trimesh.transformations.rotation_matrix(
        math.radians(90),
        [1, 0, 0]
    )
)

# Position hole before Z rotation
upright_hole.apply_translation([
    0,
    0,
    THICKNESS + UPRIGHT_HEIGHT * 0.65
])

# Rotate hole around Z with the upright
upright_hole.apply_transform(
    trimesh.transformations.rotation_matrix(
        upper_angle,
        [0, 0, 1]
    )
)

# Move hole to upright location
upright_hole.apply_translation([
    upper_x,
    upper_y,
    0
])

# =========================================================
# COMBINE
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