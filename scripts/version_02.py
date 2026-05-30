from pathlib import Path
import math
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon, cylinder
from trimesh.boolean import difference

# =========================================================
# SETTINGS
# =========================================================
ARM_LENGTH = 140.0
ARM_WIDTH = 30.0
THICKNESS = 8.0
V_ANGLE = 40.0

INNER_FILLET_RADIUS = 12.0
OUTER_FILLET_RADIUS = 20.0

CENTER_HOLE = 6.0
END_HOLE = 23.0

# Amount of material to leave beyond the 23 mm holes
END_EDGE_MATERIAL = 8.0

# Automatically calculate how far to move the holes inward
HOLE_INSET = (END_HOLE / 2) + END_EDGE_MATERIAL

# =========================================================
# AUTO SAVE SETTINGS
# =========================================================
SAVE_DIR = "stl"

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

    coords = [
        (
            x * math.cos(angle) - y * math.sin(angle),
            x * math.sin(angle) + y * math.cos(angle)
        )
        for x, y in rect.exterior.coords
    ]

    return Polygon(coords)

arm1 = create_arm(V_ANGLE / 2)
arm2 = create_arm(-V_ANGLE / 2)

v_shape_2d = unary_union([arm1, arm2])

# =========================================================
# APPLY FILLET / ROUNDING
# =========================================================
buffered = v_shape_2d.buffer(OUTER_FILLET_RADIUS, join_style=1)
v_fillet_2d = buffered.buffer(-INNER_FILLET_RADIUS, join_style=1)

# =========================================================
# EXTRUDE TO 3D
# =========================================================
body = extrude_polygon(v_fillet_2d, THICKNESS, engine="earcut")

# =========================================================
# HOLES
# =========================================================
def create_hole(diameter, x, y):
    hole = cylinder(
        radius=diameter / 2,
        height=THICKNESS + 4,
        sections=64
    )

    hole.apply_translation([x, y, THICKNESS / 2])
    return hole

# Center hole
center_hole = create_hole(CENTER_HOLE, 0, 0)

# End holes moved inward
upper_angle = math.radians(V_ANGLE / 2)
lower_angle = math.radians(-V_ANGLE / 2)

hole_distance = ARM_LENGTH - HOLE_INSET

ux = hole_distance * math.cos(upper_angle)
uy = hole_distance * math.sin(upper_angle)

lx = hole_distance * math.cos(lower_angle)
ly = hole_distance * math.sin(lower_angle)

end_hole1 = create_hole(END_HOLE, ux, uy)
end_hole2 = create_hole(END_HOLE, lx, ly)

# =========================================================
# FINAL ASSEMBLY
# =========================================================
print("Cutting holes...")

final = difference(
    [body, center_hole, end_hole1, end_hole2],
    engine="manifold"
)

# =========================================================
# EXPORT STL
# =========================================================
output_path = Path(SAVE_DIR) / OUTPUT_FILE
output_path.parent.mkdir(parents=True, exist_ok=True)

final.export(str(output_path))

print(f"✅ STL saved as: {output_path}")
print(f"✅ End holes inset: {HOLE_INSET:.1f} mm")
print(f"✅ Material beyond holes: {END_EDGE_MATERIAL:.1f} mm")