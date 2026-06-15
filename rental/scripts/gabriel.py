from pathlib import Path
import math
import trimesh
from trimesh.creation import box, cylinder
from trimesh.transformations import translation_matrix

# =========================================================
# LEGO STYLE NAME TAG - GABRIEL
# Ready-to-print STL
# Built from simple solids for reliable STL export
# All dimensions are in millimetres
# =========================================================

NAME = "GABRIEL"
OUTPUT_FILE = Path("/hebersham/stl/GABRIEL_lego_name_tag.stl")

# Base
BASE_WIDTH = 160.0
BASE_HEIGHT = 52.0
BASE_THICKNESS = 4.0

# LEGO studs
STUD_DIAMETER = 7.8
STUD_HEIGHT = 2.0
STUD_ROWS_Y = [10.5, 41.5]
STUD_COUNT = 8
STUD_START_X = 24.0
STUD_SPACING = 17.5

# Raised block letters
LETTER_THICKNESS = 2.4
LETTER_Z = BASE_THICKNESS + STUD_HEIGHT
LETTER_HEIGHT = 24.0
LETTER_WIDTH = 13.0
LETTER_STROKE = 3.0
LETTER_SPACING = 4.0
TEXT_START_X = 32.0
TEXT_BOTTOM_Y = 14.0

# Keyring loop on left
LOOP_OUTER_RADIUS = 8.0
LOOP_INNER_RADIUS = 3.4
LOOP_X = 12.0
LOOP_Y = BASE_HEIGHT / 2.0
LOOP_HEIGHT = 4.0


def move(mesh, x, y, z):
    mesh.apply_transform(translation_matrix([x, y, z]))
    return mesh


def make_box(cx, cy, cz, sx, sy, sz):
    return move(box(extents=[sx, sy, sz]), cx, cy, cz)


def make_stud(x, y):
    return move(
        cylinder(radius=STUD_DIAMETER / 2, height=STUD_HEIGHT, sections=48),
        x, y, BASE_THICKNESS + STUD_HEIGHT / 2
    )


def make_bar(x, y, w, h):
    """2D letter bar extruded upward."""
    return make_box(
        x + w / 2,
        y + h / 2,
        LETTER_Z + LETTER_THICKNESS / 2,
        w,
        h,
        LETTER_THICKNESS
    )


def letter_parts(ch, x, y):
    W = LETTER_WIDTH
    H = LETTER_HEIGHT
    S = LETTER_STROKE
    M = H / 2 - S / 2
    parts = []

    # Segment helpers
    top = lambda: make_bar(x, y + H - S, W, S)
    mid = lambda: make_bar(x, y + M, W, S)
    bot = lambda: make_bar(x, y, W, S)
    left_top = lambda: make_bar(x, y + H / 2, S, H / 2)
    left_bot = lambda: make_bar(x, y, S, H / 2)
    right_top = lambda: make_bar(x + W - S, y + H / 2, S, H / 2)
    right_bot = lambda: make_bar(x + W - S, y, S, H / 2)

    if ch == "G":
        parts += [top(), bot(), left_top(), left_bot(), right_bot()]
        parts.append(make_bar(x + W * 0.45, y + M, W * 0.55, S))
    elif ch == "A":
        parts += [top(), mid(), left_top(), left_bot(), right_top(), right_bot()]
    elif ch == "B":
        parts += [top(), mid(), bot(), left_top(), left_bot(), right_top(), right_bot()]
    elif ch == "R":
        parts += [top(), mid(), left_top(), left_bot(), right_top()]
        # diagonal leg approximated with small stepped blocks
        parts.append(make_bar(x + W * 0.45, y + H * 0.20, W * 0.25, S))
        parts.append(make_bar(x + W * 0.62, y + H * 0.08, W * 0.25, S))
    elif ch == "I":
        parts += [top(), bot(), make_bar(x + W / 2 - S / 2, y, S, H)]
    elif ch == "E":
        parts += [top(), mid(), bot(), left_top(), left_bot()]
    elif ch == "L":
        parts += [bot(), left_top(), left_bot()]
    else:
        parts += [top(), mid(), bot()]
    return parts


# =========================================================
# BUILD MODEL
# =========================================================
parts = []

# Main rectangular LEGO-tag base
parts.append(make_box(BASE_WIDTH / 2, BASE_HEIGHT / 2, BASE_THICKNESS / 2, BASE_WIDTH, BASE_HEIGHT, BASE_THICKNESS))

# Soft-looking raised border using four thin bars
BORDER_H = 1.4
BORDER_Z = BASE_THICKNESS + BORDER_H / 2
parts.append(make_box(BASE_WIDTH / 2, 1.2, BORDER_Z, BASE_WIDTH, 2.4, BORDER_H))
parts.append(make_box(BASE_WIDTH / 2, BASE_HEIGHT - 1.2, BORDER_Z, BASE_WIDTH, 2.4, BORDER_H))
parts.append(make_box(1.2, BASE_HEIGHT / 2, BORDER_Z, 2.4, BASE_HEIGHT, BORDER_H))
parts.append(make_box(BASE_WIDTH - 1.2, BASE_HEIGHT / 2, BORDER_Z, 2.4, BASE_HEIGHT, BORDER_H))

# Keyring loop as a round raised tab with visible hole marker.
# The centre hole is represented by a shallow recess/marker for drilling if wanted.
parts.append(move(cylinder(radius=LOOP_OUTER_RADIUS, height=LOOP_HEIGHT, sections=64), LOOP_X, LOOP_Y, LOOP_HEIGHT / 2))
parts.append(move(cylinder(radius=LOOP_INNER_RADIUS, height=1.0, sections=48), LOOP_X, LOOP_Y, BASE_THICKNESS + 0.5))

# LEGO studs
for y in STUD_ROWS_Y:
    for i in range(STUD_COUNT):
        x = STUD_START_X + i * STUD_SPACING
        # Keep studs away from the name letters a little; studs sit behind/around the text
        parts.append(make_stud(x, y))

# Raised name using block/LEGO-like letters
x = TEXT_START_X
for ch in NAME:
    parts.extend(letter_parts(ch, x, TEXT_BOTTOM_Y))
    x += LETTER_WIDTH + LETTER_SPACING

# Combine and export
final = trimesh.util.concatenate(parts)
final.remove_unreferenced_vertices()
final.merge_vertices()
final.fix_normals()

final.export(str(OUTPUT_FILE))

print(f"Created: {OUTPUT_FILE}")
print(f"Approx size: {BASE_WIDTH}mm x {BASE_HEIGHT}mm x {BASE_THICKNESS + STUD_HEIGHT + LETTER_THICKNESS:.1f}mm")
print("Note: keyring hole is marked as a small centre circle; drill it through after printing if you want it open.")
