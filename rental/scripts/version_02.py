from pathlib import Path
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference

# =========================================================
# ITEM SETTINGS - all dimensions are in millimetres
# =========================================================
PIECE_COUNT = 4
PIECE_LENGTH = 200.0
WIDTH = 20.0
HEIGHT = 35.0

# =========================================================
# HOLE SETTINGS
# =========================================================
HOLE_DIAMETER = 6.0
HOLE_RADIUS = HOLE_DIAMETER / 2.0

HOLE_X = PIECE_LENGTH / 2.0
HOLE_Z = HEIGHT / 2.0
HOLE_Y_DEPTH = WIDTH + 10.0

COUNTERSINK_DIAMETER = 15.0
COUNTERSINK_RADIUS = COUNTERSINK_DIAMETER / 2.0
COUNTERSINK_DEPTH = 6.0

# =========================================================
# INTERLOCK SETTINGS
# =========================================================
INTERLOCK_LENGTH = 25.0

TONGUE_WIDTH = 12.0
TONGUE_HEIGHT = 20.0

CLEARANCE = 0.5

SLOT_WIDTH = TONGUE_WIDTH + CLEARANCE
SLOT_HEIGHT = TONGUE_HEIGHT + CLEARANCE

SAVE_DIR = Path("hebersham/stl/800mm_rail_4_pieces_interlocking_countersunk")
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def make_box(extents, centre):
    b = box(extents=extents)
    b.apply_translation(centre)
    return b


def make_piece(piece_number: int) -> trimesh.Trimesh:
    part = box(extents=[PIECE_LENGTH, WIDTH, HEIGHT])
    part.apply_translation([PIECE_LENGTH / 2.0, WIDTH / 2.0, HEIGHT / 2.0])

    cutters = []

    has_left_slot = piece_number != 1
    has_right_tongue = piece_number != PIECE_COUNT

    # =====================================================
    # LEFT SLOT
    # Piece 1 has square left end
    # Pieces 2, 3, 4 have slot on left end
    # =====================================================
    if has_left_slot:
        slot = make_box(
            extents=[INTERLOCK_LENGTH + 2.0, SLOT_WIDTH, SLOT_HEIGHT],
            centre=[
                INTERLOCK_LENGTH / 2.0,
                WIDTH / 2.0,
                HEIGHT / 2.0,
            ],
        )
        cutters.append(slot)

    # =====================================================
    # RIGHT TONGUE
    # Pieces 1, 2, 3 have tongue on right end
    # Piece 4 has square right end
    # =====================================================
    if has_right_tongue:
        tongue_start_x = PIECE_LENGTH - INTERLOCK_LENGTH
        tongue_centre_x = tongue_start_x + INTERLOCK_LENGTH / 2.0

        top_cut = make_box(
            extents=[INTERLOCK_LENGTH + 2.0, WIDTH, (HEIGHT - TONGUE_HEIGHT) / 2.0],
            centre=[
                tongue_centre_x,
                WIDTH / 2.0,
                HEIGHT - ((HEIGHT - TONGUE_HEIGHT) / 4.0),
            ],
        )

        bottom_cut = make_box(
            extents=[INTERLOCK_LENGTH + 2.0, WIDTH, (HEIGHT - TONGUE_HEIGHT) / 2.0],
            centre=[
                tongue_centre_x,
                WIDTH / 2.0,
                (HEIGHT - TONGUE_HEIGHT) / 4.0,
            ],
        )

        side_cut_1 = make_box(
            extents=[INTERLOCK_LENGTH + 2.0, (WIDTH - TONGUE_WIDTH) / 2.0, HEIGHT],
            centre=[
                tongue_centre_x,
                (WIDTH - TONGUE_WIDTH) / 4.0,
                HEIGHT / 2.0,
            ],
        )

        side_cut_2 = make_box(
            extents=[INTERLOCK_LENGTH + 2.0, (WIDTH - TONGUE_WIDTH) / 2.0, HEIGHT],
            centre=[
                tongue_centre_x,
                WIDTH - ((WIDTH - TONGUE_WIDTH) / 4.0),
                HEIGHT / 2.0,
            ],
        )

        cutters.extend([top_cut, bottom_cut, side_cut_1, side_cut_2])

    # =====================================================
    # CENTRE 6 MM HOLE THROUGH WIDTH
    # =====================================================
    hole = cylinder(
        radius=HOLE_RADIUS,
        height=HOLE_Y_DEPTH,
        sections=64,
    )

    hole.apply_transform(
        trimesh.transformations.rotation_matrix(
            angle=1.57079632679,
            direction=[1, 0, 0],
        )
    )

    hole.apply_translation([HOLE_X, WIDTH / 2.0, HOLE_Z])
    cutters.append(hole)

    # =====================================================
    # COUNTERSINK / RECESS
    # 15 mm diameter, 6 mm deep from front face
    # =====================================================
    countersink = cylinder(
        radius=COUNTERSINK_RADIUS,
        height=COUNTERSINK_DEPTH + 1.0,
        sections=64,
    )

    countersink.apply_transform(
        trimesh.transformations.rotation_matrix(
            angle=1.57079632679,
            direction=[1, 0, 0],
        )
    )

    countersink.apply_translation([
        HOLE_X,
        COUNTERSINK_DEPTH / 2.0,
        HOLE_Z,
    ])

    cutters.append(countersink)

    result = difference([part] + cutters)

    result.remove_unreferenced_vertices()
    result.merge_vertices()
    result.fix_normals()

    result.metadata["name"] = f"interlocking rail piece {piece_number}"
    return result


def main():
    pieces = []

    for i in range(1, PIECE_COUNT + 1):
        piece = make_piece(i)

        output_file = SAVE_DIR / f"interlocking_rail_piece_{i}_200x20x35mm_countersunk.stl"
        piece.export(output_file)

        pieces.append(piece.copy())
        print(f"Saved: {output_file}")

    spacing = 10.0
    arranged = []

    for i, piece in enumerate(pieces):
        p = piece.copy()
        p.apply_translation([0, i * (WIDTH + spacing), 0])
        arranged.append(p)

    combined = trimesh.util.concatenate(arranged)
    combined_file = SAVE_DIR / "all_4_interlocking_pieces_arranged_countersunk.stl"
    combined.export(combined_file)

    print(f"Saved: {combined_file}")


if __name__ == "__main__":
    main()