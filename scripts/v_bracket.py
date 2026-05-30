import shapely.geometry as sg
import shapely.affinity as sa
from shapely.ops import unary_union
import trimesh
import numpy as np

# ================== PARAMETERS ==================
thickness = 8.0
base_width = 70.0
base_height = 35.0
angle = 45.0

hole_dia_mount = 23.0
hole_dia_truck = 6.0
arm_length = 58.0

# ================================================

# Base Plate
base_rect = sg.box(-base_width/2, -base_height/2, base_width/2, base_height/2)
base = base_rect.buffer(8)
truck_hole = sg.Point(0, 0).buffer(hole_dia_truck / 2)
base = base.difference(truck_hole)

# Right Arm
line1 = sg.LineString([(12, 0), (12 + arm_length, 0)])
line2 = sg.LineString([(12 + arm_length, 0),
                       (12 + arm_length + arm_length * np.cos(np.radians(angle)),
                        arm_length * np.sin(np.radians(angle)))])

arm_path_right = unary_union([line1, line2])
arm_right = arm_path_right.buffer(thickness / 2)

# Left Arm
arm_left = sa.rotate(arm_right, -2 * angle, origin=(12, 0))

# Combine
combined_2d = unary_union([base, arm_right, arm_left])

# Mounting holes
hole1_center = (12 + arm_length * 0.82,  arm_length * 0.48)
hole2_center = (12 + arm_length * 0.82, -arm_length * 0.48)
hole1 = sg.Point(hole1_center).buffer(hole_dia_mount / 2)
hole2 = sg.Point(hole2_center).buffer(hole_dia_mount / 2)

final_2d = combined_2d.difference(unary_union([hole1, hole2]))

# Create 3D mesh
mesh = trimesh.creation.extrude_polygon(final_2d, height=thickness)

# Export
mesh.export("dual_phone_bracket.stl")
print("✅ Successfully exported: dual_phone_bracket.stl")
print("You can now open this file in Bambu Studio.")