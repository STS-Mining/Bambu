from pathlib import Path
import math
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from trimesh.creation import extrude_polygon

NAME = "Benjamin"  # name exactly as requested
OUTPUT = Path('name_tags/benjamin/Benjamin.stl')

# Dimensions in mm
WIDTH = 138.0
HEIGHT = 44.0
BASE_THICKNESS = 3.4
RAISED_HEIGHT = 1.8
BORDER_HEIGHT = 1.2
CORNER_RADIUS = 8.0
KEY_HOLE_DIA = 6.5
KEY_HOLE_X = 12.0
KEY_HOLE_Y = HEIGHT / 2
BORDER_WIDTH = 2.2


def rounded_rect(x, y, w, h, r):
    # create rounded rectangle by buffering a smaller rectangle
    return box(x+r, y+r, x+w-r, y+h-r).buffer(r, resolution=24)


def mesh_from_polygon(poly, height, z=0.0):
    if poly.is_empty:
        return None
    meshes = []
    if poly.geom_type == 'Polygon':
        geoms = [poly]
    else:
        geoms = list(poly.geoms)
    for g in geoms:
        if g.area < 0.05:
            continue
        m = extrude_polygon(g, height)
        m.apply_translation([0, 0, z])
        meshes.append(m)
    if not meshes:
        return None
    return trimesh.util.concatenate(meshes)


def text_to_shape(text, target_width, target_height, x_left, y_center):
    # Bold, rounded-looking font available in matplotlib; no font file is included in the output.
    fp = FontProperties(family='DejaVu Sans', weight='bold')
    tp = TextPath((0, 0), text, size=1, prop=fp)

    rings = []
    vertices = tp.vertices
    codes = tp.codes
    cur = []
    for v, c in zip(vertices, codes):
        if c == 1:  # MOVETO
            if len(cur) >= 3:
                rings.append(cur)
            cur = [tuple(v)]
        elif c == 2 or c == 3:  # LINETO/CURVE approximated by TextPath vertices
            cur.append(tuple(v))
        elif c == 79:  # CLOSEPOLY
            if len(cur) >= 3:
                rings.append(cur)
            cur = []
    if len(cur) >= 3:
        rings.append(cur)

    contours = []
    for r in rings:
        p = Polygon(r)
        if p.is_valid and p.area > 1e-6:
            contours.append(p)

    # Build polygons with holes by containment depth.
    used_holes = set()
    polys = []
    for i, p in enumerate(contours):
        # shells are contours not contained by an odd number of others, based on largest containment rule
        containers = [j for j, q in enumerate(contours) if j != i and q.contains(p.representative_point())]
        if len(containers) % 2 == 0:  # shell
            holes = []
            for k, h in enumerate(contours):
                if k == i:
                    continue
                if p.contains(h.representative_point()):
                    deeper = [j for j, q in enumerate(contours) if j not in (i,k) and p.contains(q.representative_point()) and q.contains(h.representative_point())]
                    if len(deeper) == 0:
                        holes.append(list(h.exterior.coords))
                        used_holes.add(k)
            try:
                polys.append(Polygon(p.exterior.coords, holes))
            except Exception:
                polys.append(p)

    shape = unary_union(polys).buffer(0)
    minx, miny, maxx, maxy = shape.bounds
    scale = min(target_width / (maxx - minx), target_height / (maxy - miny))
    shape = affinity.scale(shape, xfact=scale, yfact=scale, origin=(minx, miny))
    minx, miny, maxx, maxy = shape.bounds
    shape = affinity.translate(shape, xoff=x_left - minx, yoff=y_center - (miny + maxy)/2)
    return shape.buffer(0)


def star(cx, cy, r_outer=4.2, r_inner=1.9, points=5):
    pts=[]
    for i in range(points*2):
        ang = math.pi/2 + i*math.pi/points
        r = r_outer if i%2==0 else r_inner
        pts.append((cx + r*math.cos(ang), cy + r*math.sin(ang)))
    return Polygon(pts)


def lightning(cx, cy, scale=1.0):
    pts = np.array([
        [-3.5,  7.0], [ 2.0,  7.0], [-0.5,  1.2], [4.0, 1.2],
        [-3.0, -8.0], [-1.0, -1.8], [-5.0, -1.8]
    ]) * scale
    pts[:,0] += cx
    pts[:,1] += cy
    return Polygon([tuple(p) for p in pts])

# Base with keyring hole
outer = rounded_rect(0, 0, WIDTH, HEIGHT, CORNER_RADIUS)
hole = Point(KEY_HOLE_X, KEY_HOLE_Y).buffer(KEY_HOLE_DIA/2, resolution=32)
base_shape = outer.difference(hole)

# Raised border ring and keyhole rim
inner = rounded_rect(BORDER_WIDTH, BORDER_WIDTH, WIDTH-2*BORDER_WIDTH, HEIGHT-2*BORDER_WIDTH, CORNER_RADIUS-BORDER_WIDTH)
border_shape = outer.difference(inner).difference(hole)
rim_shape = Point(KEY_HOLE_X, KEY_HOLE_Y).buffer(5.6, resolution=32).difference(hole)

# Text and fun raised shapes
text_shape = text_to_shape(NAME, target_width=86, target_height=22, x_left=29, y_center=HEIGHT/2+0.5)
bolt_shape = lightning(124, HEIGHT/2, scale=1.15)
star1 = star(25, 33.5, 3.4, 1.5)
star2 = star(116, 10.5, 2.8, 1.2)
raised_decor = unary_union([text_shape, bolt_shape, star1, star2]).intersection(inner.buffer(-0.8))

meshes = [
    mesh_from_polygon(base_shape, BASE_THICKNESS, 0),
    mesh_from_polygon(border_shape.union(rim_shape), BORDER_HEIGHT, BASE_THICKNESS),
    mesh_from_polygon(raised_decor, RAISED_HEIGHT, BASE_THICKNESS),
]
meshes = [m for m in meshes if m is not None]
final = trimesh.util.concatenate(meshes)
final.remove_unreferenced_vertices()
final.merge_vertices()
final.export(OUTPUT)
print(f"Saved: {OUTPUT}")
print(f"Size: {WIDTH} x {HEIGHT} x {BASE_THICKNESS+RAISED_HEIGHT:.1f} mm")
print(f"Watertight: {final.is_watertight}")
print(f"Parts/shells: {len(final.split(only_watertight=False))}")
