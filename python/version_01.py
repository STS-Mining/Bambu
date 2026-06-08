from pathlib import Path
import numpy as np
import trimesh
from trimesh.creation import box, cylinder, extrude_polygon
from shapely.geometry import box as shapely_box
from shapely.geometry import Point
from shapely.ops import unary_union

# =========================================================
# SETTINGS
# =========================================================
CUBE_SIZE = 100.0
WALL_THICKNESS = 3.0

LOGO_SIZE = 56.0
LOGO_RAISE = 2.0

DETAIL_RAISE = 0.8
DETAIL_WIDTH = 1.2

OUTPUT_FILE = "python/python_hollow_cube_100mm_self_contained.stl"

# =========================================================
# HELPERS
# =========================================================
def rounded_rect(cx, cy, w, h, r):
    return shapely_box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2).buffer(r).buffer(-r)

def make_wall_cube():
    s = CUBE_SIZE
    t = WALL_THICKNESS

    parts = [
        box(extents=(s, s, t), transform=trimesh.transformations.translation_matrix((0, 0,  s / 2 - t / 2))),
        box(extents=(s, s, t), transform=trimesh.transformations.translation_matrix((0, 0, -s / 2 + t / 2))),
        box(extents=(s, t, s), transform=trimesh.transformations.translation_matrix((0,  s / 2 - t / 2, 0))),
        box(extents=(s, t, s), transform=trimesh.transformations.translation_matrix((0, -s / 2 + t / 2, 0))),
        box(extents=(t, s, s), transform=trimesh.transformations.translation_matrix(( s / 2 - t / 2, 0, 0))),
        box(extents=(t, s, s), transform=trimesh.transformations.translation_matrix((-s / 2 + t / 2, 0, 0))),
    ]

    return trimesh.util.concatenate(parts)

def make_python_logo():
    scale = LOGO_SIZE / 60.0

    top = rounded_rect(-7 * scale, 8 * scale, 38 * scale, 24 * scale, 5 * scale)
    bottom = rounded_rect(7 * scale, -8 * scale, 38 * scale, 24 * scale, 5 * scale)

    top_cut = rounded_rect(15 * scale, -1 * scale, 18 * scale, 12 * scale, 3 * scale)
    bottom_cut = rounded_rect(-15 * scale, 1 * scale, 18 * scale, 12 * scale, 3 * scale)

    dot_top = Point(-18 * scale, 15 * scale).buffer(2.4 * scale)
    dot_bottom = Point(18 * scale, -15 * scale).buffer(2.4 * scale)

    logo_shape = unary_union([
        top.difference(top_cut),
        bottom.difference(bottom_cut),
        dot_top,
        dot_bottom,
    ])

    mesh = extrude_polygon(logo_shape, LOGO_RAISE)
    return mesh

def make_face_details():
    parts = []
    positions = [-40, -25, -10, 10, 25, 40]

    for x in positions:
        parts.append(box(extents=(DETAIL_WIDTH, 82, DETAIL_RAISE),
                         transform=trimesh.transformations.translation_matrix((x, 0, DETAIL_RAISE / 2))))

    for y in positions:
        parts.append(box(extents=(82, DETAIL_WIDTH, DETAIL_RAISE),
                         transform=trimesh.transformations.translation_matrix((0, y, DETAIL_RAISE / 2))))

    pad_positions = [
        (-38, -36), (-22, -38), (35, -30),
        (-40, 24), (26, 36), (40, 10),
        (-30, 36), (10, -36)
    ]

    for x, y in pad_positions:
        pad = cylinder(radius=2.2, height=DETAIL_RAISE, sections=24)
        pad.apply_translation((x, y, DETAIL_RAISE / 2))
        parts.append(pad)

    return trimesh.util.concatenate(parts)

def place_on_face(mesh, normal):
    normal = np.array(normal, dtype=float)
    normal = normal / np.linalg.norm(normal)

    placed = mesh.copy()

    rot = trimesh.geometry.align_vectors([0, 0, 1], normal)
    placed.apply_transform(rot)

    placed.apply_translation(normal * (CUBE_SIZE / 2))

    return placed

# =========================================================
# MAIN
# =========================================================
cube = make_wall_cube()
logo = make_python_logo()
details = make_face_details()

faces = [
    (0, 0, 1),
    (0, 0, -1),
    (1, 0, 0),
    (-1, 0, 0),
    (0, 1, 0),
    (0, -1, 0),
]

all_parts = [cube]

for face in faces:
    all_parts.append(place_on_face(details, face))
    all_parts.append(place_on_face(logo, face))

final = trimesh.util.concatenate(all_parts)
final.remove_unreferenced_vertices()
final.merge_vertices()

output_path = Path(OUTPUT_FILE)
final.export(output_path)

print(f"Saved: {output_path.resolve()}")