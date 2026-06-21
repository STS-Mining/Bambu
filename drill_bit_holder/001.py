from pathlib import Path
import math
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point
from shapely.ops import triangulate

# =========================================================
# SETTINGS
# =========================================================
HEIGHT = 120.0
OUTER_DIAMETER = 90.0
WALL_THICKNESS = 4.0
BACK_THICKNESS = 6.0
BOTTOM_THICKNESS = 5.0

SCREW_HOLE_DIAMETER = 5.0
COUNTERSINK_DIAMETER = 11.0
COUNTERSINK_DEPTH = 3.0
SCREW_Z_POSITIONS = [35.0, 90.0]

SAVE_DIR = Path("drill_bit_holder/stl")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
script_name = Path(__file__).stem
OUTPUT_FILE = SAVE_DIR / f"{script_name}.stl"

# =========================================================
# HELPERS
# =========================================================
def extrude_xz_polygon(poly, y0, y1):
    verts = []
    faces = []
    vmap = {}

    def vid(x, y, z):
        key = (round(x, 5), round(y, 5), round(z, 5))
        if key not in vmap:
            vmap[key] = len(verts)
            verts.append([x, y, z])
        return vmap[key]

    # front/back faces
    for tri in triangulate(poly):
        if not poly.contains(tri.representative_point()):
            continue

        coords = list(tri.exterior.coords)[:-1]
        a0, b0, c0 = [vid(x, y0, z) for x, z in coords]
        a1, b1, c1 = [vid(x, y1, z) for x, z in coords]

        faces.append([a0, c0, b0])
        faces.append([a1, b1, c1])

    # side walls
    rings = [poly.exterior] + list(poly.interiors)

    for ring in rings:
        coords = list(ring.coords)
        for i in range(len(coords) - 1):
            x1, z1 = coords[i]
            x2, z2 = coords[i + 1]

            a = vid(x1, y0, z1)
            b = vid(x2, y0, z2)
            c = vid(x2, y1, z2)
            d = vid(x1, y1, z1)

            faces.append([a, b, c])
            faces.append([a, c, d])

    return trimesh.Trimesh(vertices=verts, faces=faces, process=True)

# =========================================================
# BACK PLATE WITH REAL HOLES
# =========================================================
r = OUTER_DIAMETER / 2

rect = Polygon([
    (-r, 0),
    ( r, 0),
    ( r, HEIGHT),
    (-r, HEIGHT)
])

small_holes = [
    Point(0, z).buffer(SCREW_HOLE_DIAMETER / 2, resolution=48)
    for z in SCREW_Z_POSITIONS
]

large_holes = [
    Point(0, z).buffer(COUNTERSINK_DIAMETER / 2, resolution=48)
    for z in SCREW_Z_POSITIONS
]

back_inner = rect
for h in small_holes:
    back_inner = back_inner.difference(h)

back_outer = rect
for h in large_holes:
    back_outer = back_outer.difference(h)

# outer countersunk section
mesh_outer_back = extrude_xz_polygon(back_outer, 0, COUNTERSINK_DEPTH)

# inner screw-hole section
mesh_inner_back = extrude_xz_polygon(back_inner, COUNTERSINK_DEPTH, BACK_THICKNESS)

# =========================================================
# HALF ROUND HOLDER BODY
# =========================================================
outer_r = OUTER_DIAMETER / 2
inner_r = outer_r - WALL_THICKNESS

segments = 120
angles = np.linspace(math.pi, 0, segments + 1)

verts = []
faces = []

def add(v):
    verts.append(v)
    return len(verts) - 1

outer_bottom = []
outer_top = []
inner_bottom = []
inner_top = []

for a in angles:
    outer_bottom.append(add([
        outer_r * math.cos(a),
        outer_r * math.sin(a),
        0
    ]))

    outer_top.append(add([
        outer_r * math.cos(a),
        outer_r * math.sin(a),
        HEIGHT
    ]))

    inner_bottom.append(add([
        inner_r * math.cos(a),
        BACK_THICKNESS + inner_r * math.sin(a),
        BOTTOM_THICKNESS
    ]))

    inner_top.append(add([
        inner_r * math.cos(a),
        BACK_THICKNESS + inner_r * math.sin(a),
        HEIGHT
    ]))

for i in range(segments):
    # outside rounded front
    faces.append([outer_bottom[i], outer_bottom[i + 1], outer_top[i + 1]])
    faces.append([outer_bottom[i], outer_top[i + 1], outer_top[i]])

    # inside rounded wall
    faces.append([inner_bottom[i + 1], inner_bottom[i], inner_top[i]])
    faces.append([inner_bottom[i + 1], inner_top[i], inner_top[i + 1]])

    # top rim
    faces.append([outer_top[i], outer_top[i + 1], inner_top[i + 1]])
    faces.append([outer_top[i], inner_top[i + 1], inner_top[i]])

    # bottom
    faces.append([outer_bottom[i], inner_bottom[i], inner_bottom[i + 1]])
    faces.append([outer_bottom[i], inner_bottom[i + 1], outer_bottom[i + 1]])

# left side wall
faces.append([outer_bottom[0], outer_top[0], inner_top[0]])
faces.append([outer_bottom[0], inner_top[0], inner_bottom[0]])

# right side wall
faces.append([outer_bottom[-1], inner_bottom[-1], inner_top[-1]])
faces.append([outer_bottom[-1], inner_top[-1], outer_top[-1]])

cup = trimesh.Trimesh(vertices=verts, faces=faces, process=True)

# =========================================================
# COMBINE AND EXPORT
# =========================================================
final_mesh = trimesh.util.concatenate([
    mesh_outer_back,
    mesh_inner_back,
    cup
])

final_mesh.export(OUTPUT_FILE)

print(f"Saved STL to: {OUTPUT_FILE.resolve()}")