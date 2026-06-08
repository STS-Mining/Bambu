from pathlib import Path
import math
import numpy as np
import trimesh
from shapely.geometry import box, Point, Polygon, LineString
from shapely.ops import unary_union
from shapely import affinity
from trimesh.creation import extrude_polygon, cylinder
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

try:
    import qrcode
except ImportError:
    qrcode = None

# =========================================================
# FREE WIFI SIGN - STL GENERATOR
# Dimensions are in millimetres
# Generates separate STL files for Bambu Studio colour assignment:
#   wifi_sign_black_parts.stl  -> assign BLACK filament
#   wifi_sign_white_parts.stl  -> assign WHITE filament
#   wifi_sign_complete_preview.stl -> merged preview only, STL has no colour
# =========================================================

OUT_DIR = Path("wifi_sign_stl")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Sign size
W = 220.0
H = 220.0
BASE_THICKNESS = 3.0
RAISED = 1.8
TEXT_RAISED = 2.2
RADIUS = 12.0
BORDER = 5.0

# Text / wifi settings
SSID = "VIP Lounge"
PASSWORD = "Manchester86United67!"
QR_PAYLOAD = f"WIFI:T:WPA;S:{SSID};P:{PASSWORD};;"

# Use common bold fonts; adjust if missing on your system
FONT_BOLD = FontProperties(family="DejaVu Sans", weight="bold")
FONT_REG = FontProperties(family="DejaVu Sans", weight="bold")


def rounded_rect(x, y, w, h, r, res=24):
    r = min(r, w/2, h/2)
    return box(x+r, y+r, x+w-r, y+h-r).buffer(r, resolution=res)


def make_mesh(poly, z, height):
    if poly.is_empty:
        return None
    m = extrude_polygon(poly, height)
    m.apply_translation([0, 0, z])
    return m


def add_poly(parts, poly, z, height):
    if poly is None or poly.is_empty:
        return
    if poly.geom_type == "GeometryCollection":
        for g in poly.geoms:
            add_poly(parts, g, z, height)
        return
    if poly.geom_type == "MultiPolygon":
        for g in poly.geoms:
            add_poly(parts, g, z, height)
        return
    try:
        mesh = make_mesh(poly, z, height)
        if mesh is not None:
            parts.append(mesh)
    except Exception as e:
        print("Skipped polygon:", e)


def text_poly(text, x, y, target_w=None, target_h=None, size=20, font=FONT_BOLD):
    tp = TextPath((0, 0), text, size=size, prop=font)
    polys = []
    for p in tp.to_polygons():
        if len(p) >= 3:
            poly = Polygon(p)
            if poly.is_valid and poly.area > 0:
                polys.append(poly)
    if not polys:
        return None
    geom = unary_union(polys)
    minx, miny, maxx, maxy = geom.bounds
    geom = affinity.translate(geom, xoff=-minx, yoff=-miny)
    minx, miny, maxx, maxy = geom.bounds
    sx = target_w / (maxx - minx) if target_w else None
    sy = target_h / (maxy - miny) if target_h else None
    if target_w and target_h:
        s = min(sx, sy)
    else:
        s = sx or sy or 1.0
    geom = affinity.scale(geom, xfact=s, yfact=s, origin=(0, 0))
    minx, miny, maxx, maxy = geom.bounds
    geom = affinity.translate(geom, xoff=x, yoff=y)
    return geom


def centered_text(text, cx, cy, target_w=None, target_h=None, size=20, font=FONT_BOLD):
    g = text_poly(text, 0, 0, target_w=target_w, target_h=target_h, size=size, font=font)
    if g is None:
        return None
    minx, miny, maxx, maxy = g.bounds
    return affinity.translate(g, xoff=cx - (minx+maxx)/2, yoff=cy - (miny+maxy)/2)


def line_poly(x1, y1, x2, y2, width, cap=2.5):
    return LineString([(x1, y1), (x2, y2)]).buffer(width/2, cap_style=1, join_style=1, resolution=16)


def ring_poly(cx, cy, outer_r, inner_r):
    return Point(cx, cy).buffer(outer_r, resolution=64).difference(Point(cx, cy).buffer(inner_r, resolution=64))


def wifi_arcs(cx, cy, scale=1.0):
    # raised white Wi-Fi icon made from 3 arcs + dot
    parts = []
    for r, width, start_deg, end_deg in [(37, 7, 25, 155), (26, 6, 28, 152), (15, 5, 35, 145)]:
        pts = []
        for a in np.linspace(math.radians(start_deg), math.radians(end_deg), 70):
            pts.append((cx + math.cos(a)*r*scale, cy + math.sin(a)*r*scale))
        parts.append(LineString(pts).buffer(width*scale/2, cap_style=1, join_style=1, resolution=12))
    parts.append(Point(cx, cy).buffer(5.2*scale, resolution=32))
    return unary_union(parts)


def qr_modules(x, y, size):
    # Returns white QR background and black QR modules.
    if qrcode is not None:
        qr = qrcode.QRCode(border=1, box_size=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(QR_PAYLOAD)
        qr.make(fit=True)
        mat = qr.get_matrix()
    else:
        # fallback fixed pattern if qrcode package is not installed
        mat = [[(i*j + i + j) % 3 == 0 for i in range(33)] for j in range(33)]
        # finder squares
        for fy in [0, 26]:
            for fx in [0, 26]:
                for yy in range(7):
                    for xx in range(7):
                        mat[fy+yy][fx+xx] = xx in (0,6) or yy in (0,6) or (2 <= xx <= 4 and 2 <= yy <= 4)
    n = len(mat)
    cell = size / n
    white_bg = rounded_rect(x, y, size, size, 4, res=10)
    mods = []
    for row, line in enumerate(mat):
        for col, val in enumerate(line):
            if val:
                px = x + col * cell
                py = y + size - (row + 1) * cell
                mods.append(box(px, py, px + cell, py + cell))
    return white_bg, unary_union(mods)


black_parts = []
white_parts = []

# Base black plaque
base = rounded_rect(0, 0, W, H, RADIUS, res=32)
add_poly(black_parts, base, 0, BASE_THICKNESS)

# Raised white outside border/frame
outer = rounded_rect(0, 0, W, H, RADIUS, res=32)
inner = rounded_rect(BORDER, BORDER, W - 2*BORDER, H - 2*BORDER, RADIUS-3, res=32)
add_poly(white_parts, outer.difference(inner), BASE_THICKNESS, RAISED)

# Corner screw holes / white rings + black centres
for cx, cy in [(14, H-14), (W-14, H-14), (14, 14), (W-14, 14)]:
    add_poly(black_parts, Point(cx, cy).buffer(7.5, resolution=48), BASE_THICKNESS + 0.05, RAISED + 0.2)
    add_poly(white_parts, ring_poly(cx, cy, 5.2, 3.3), BASE_THICKNESS + RAISED, 0.9)

# Top FREE text
add_poly(white_parts, centered_text("FREE", W/2, 190, target_w=62, target_h=20, size=25), BASE_THICKNESS+RAISED, TEXT_RAISED)

# Large WiFi text
add_poly(white_parts, centered_text("WiFi", 83, 148, target_w=122, target_h=40, size=54), BASE_THICKNESS+RAISED, TEXT_RAISED)
add_poly(white_parts, wifi_arcs(170, 144, scale=1.05), BASE_THICKNESS+RAISED, TEXT_RAISED)

# Scan to connect pill and divider lines
add_poly(white_parts, rounded_rect(52, 112, 116, 16, 4), BASE_THICKNESS+RAISED, RAISED)
add_poly(black_parts, centered_text("SCAN TO CONNECT", 110, 120, target_w=100, target_h=8.5, size=12), BASE_THICKNESS+RAISED*2+0.1, 1.0)
add_poly(white_parts, line_poly(10, 120, 43, 120, 2.4), BASE_THICKNESS+RAISED, 1.0)
add_poly(white_parts, line_poly(177, 120, 210, 120, 2.4), BASE_THICKNESS+RAISED, 1.0)

# QR code
qr_bg, qr_black = qr_modules(12, 38, 86)
add_poly(white_parts, qr_bg, BASE_THICKNESS+RAISED, 1.2)
add_poly(black_parts, qr_black, BASE_THICKNESS+RAISED+1.25, 1.3)

# Small icon circles
add_poly(white_parts, ring_poly(119, 95, 13, 10.5), BASE_THICKNESS+RAISED, 1.0)
add_poly(white_parts, wifi_arcs(119, 88, scale=0.35), BASE_THICKNESS+RAISED, 1.3)
add_poly(white_parts, ring_poly(119, 58, 13, 10.5), BASE_THICKNESS+RAISED, 1.0)
# simple lock icon
add_poly(white_parts, rounded_rect(114, 52, 10, 12, 2), BASE_THICKNESS+RAISED, 1.2)
add_poly(black_parts, Point(119, 57).buffer(1.5, resolution=16), BASE_THICKNESS+RAISED+1.3, 1.0)
add_poly(black_parts, line_poly(119, 57, 119, 53, 1.5), BASE_THICKNESS+RAISED+1.3, 1.0)

# SSID / password labels
add_poly(white_parts, centered_text("Wi-Fi Network Name", 165, 100, target_w=67, target_h=9, size=12), BASE_THICKNESS+RAISED, 1.2)
add_poly(white_parts, centered_text("(SSID)", 143, 88, target_w=42, target_h=8, size=12), BASE_THICKNESS+RAISED, 1.2)
add_poly(white_parts, rounded_rect(137, 74, 72, 14, 3), BASE_THICKNESS+RAISED, 1.2)
add_poly(black_parts, centered_text(SSID, 173, 80.5, target_w=55, target_h=8, size=12), BASE_THICKNESS+RAISED+1.25, 1.0)
add_poly(white_parts, line_poly(108, 69, 210, 69, 1.8), BASE_THICKNESS+RAISED, 1.0)

add_poly(white_parts, centered_text("Password", 153, 55, target_w=52, target_h=9, size=12), BASE_THICKNESS+RAISED, 1.2)
add_poly(white_parts, rounded_rect(137, 35, 72, 15, 3), BASE_THICKNESS+RAISED, 1.2)
add_poly(black_parts, centered_text(PASSWORD, 173, 42, target_w=65, target_h=7, size=10), BASE_THICKNESS+RAISED+1.25, 1.0)

# Bottom thank you + small wifi + lines
add_poly(white_parts, line_poly(24, 24, 97, 24, 1.8), BASE_THICKNESS+RAISED, 1.0)
add_poly(white_parts, line_poly(123, 24, 196, 24, 1.8), BASE_THICKNESS+RAISED, 1.0)
add_poly(white_parts, ring_poly(110, 24, 8.5, 0.0), BASE_THICKNESS+RAISED, 1.0)
add_poly(black_parts, wifi_arcs(110, 20.8, scale=0.20), BASE_THICKNESS+RAISED+1.1, 0.9)
add_poly(white_parts, centered_text("THANK YOU!", 110, 8.5, target_w=78, target_h=11, size=15), BASE_THICKNESS+RAISED, TEXT_RAISED)

# Export
black = trimesh.util.concatenate(black_parts)
white = trimesh.util.concatenate(white_parts)
complete = trimesh.util.concatenate([black.copy(), white.copy()])

black.export(OUT_DIR / "wifi_sign_black_parts.stl")
white.export(OUT_DIR / "wifi_sign_white_parts.stl")
complete.export(OUT_DIR / "wifi_sign_complete_preview.stl")

print("Saved:")
print(OUT_DIR / "wifi_sign_black_parts.stl")
print(OUT_DIR / "wifi_sign_white_parts.stl")
print(OUT_DIR / "wifi_sign_complete_preview.stl")
print("In Bambu Studio, import black + white STLs together and assign colours.")
