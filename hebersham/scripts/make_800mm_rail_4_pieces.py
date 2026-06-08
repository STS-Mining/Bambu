from pathlib import Path
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference

# =========================================================
# ITEM SETTINGS - all dimensions are in millimetres
# =========================================================
TOTAL_LENGTH = 804.0
PIECE_COUNT = 4
PIECE_LENGTH = TOTAL_LENGTH / PIECE_COUNT  # 200 mm each
WIDTH = 20.0       # Y direction
HEIGHT = 35.0      # Z direction

HOLE_DIAMETER = 6.0
HOLE_RADIUS = HOLE_DIAMETER / 2.0
HOLE_FROM_END = 10.0

# Holes go through the 20 mm width, centred halfway up the 35 mm height
HOLE_Y_DEPTH = WIDTH + 10.0  # extra length so it cuts cleanly through
HOLE_Z = HEIGHT / 2.0

SAVE_DIR = Path("hebersham/stl/800mm_rail_4_pieces")
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def make_piece(piece_number: int) -> trimesh.Trimesh:
    """Create one 200 x 20 x 35 mm piece with two 6 mm through-holes."""

    # Main rectangular bar, centred at origin first
    part = box(extents=[PIECE_LENGTH, WIDTH, HEIGHT])

    # Move so bottom-left-back corner is at 0,0,0
    part.apply_translation([PIECE_LENGTH / 2.0, WIDTH / 2.0, HEIGHT / 2.0])

    hole_centres_x = [HOLE_FROM_END, PIECE_LENGTH - HOLE_FROM_END]
    cutters = []

    for x in hole_centres_x:
        # Cylinder default is along Z, so rotate it to run through Y width
        hole = cylinder(
            radius=HOLE_RADIUS,
            height=HOLE_Y_DEPTH,
            sections=64,
        )
        hole.apply_transform(trimesh.transformations.rotation_matrix(
            angle=1.57079632679,  # 90 degrees
            direction=[1, 0, 0],   # rotate around X so cylinder points along Y
        ))
        hole.apply_translation([x, WIDTH / 2.0, HOLE_Z])
        cutters.append(hole)

    try:
        result = difference([part] + cutters)
    except Exception as e:
        raise RuntimeError(
            "Boolean cut failed. Install manifold3d and try again:\n"
            "    pip install trimesh manifold3d numpy\n\n"
            f"Original error: {e}"
        )

    result.remove_unreferenced_vertices()
    result.merge_vertices()
    result.fix_normals()
    result.metadata["name"] = f"800mm rail piece {piece_number} of {PIECE_COUNT}"
    return result


def main():
    pieces = []

    for i in range(1, PIECE_COUNT + 1):
        piece = make_piece(i)
        output_file = SAVE_DIR / f"rail_piece_{i}_200x20x35mm.stl"
        piece.export(output_file)
        pieces.append(piece.copy())
        print(f"Saved: {output_file}")

    # Optional: create a combined build-plate STL with all four pieces spaced apart.
    # This is only for layout/checking. You can also print the four files separately.
    spacing = 10.0
    arranged = []
    for i, piece in enumerate(pieces):
        p = piece.copy()
        p.apply_translation([0, i * (WIDTH + spacing), 0])
        arranged.append(p)

    combined = trimesh.util.concatenate(arranged)
    combined_file = SAVE_DIR / "all_4_pieces_arranged.stl"
    combined.export(combined_file)
    print(f"Saved: {combined_file}")


if __name__ == "__main__":
    main()
