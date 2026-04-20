"""
Bulk-index a directory of images into the PriceTrace ChromaDB.

Usage:
    python populate_db.py /path/to/deepfashion/images

Each image is embedded with CLIP (no Grounding DINO) and stored with its
absolute file path in metadata so the frontend can retrieve it later.
"""

import os
import sys

from vector_db import VectorDB

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def collect_images(root: str):
    paths = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if os.path.splitext(fname)[1].lower() in IMAGE_EXTENSIONS:
                paths.append(os.path.join(dirpath, fname))
    return paths


def main():
    if len(sys.argv) < 2:
        print("Usage: python populate_db.py <image_directory>")
        sys.exit(1)

    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory.")
        sys.exit(1)

    print(f"Scanning {root} for images...")
    image_paths = collect_images(root)
    total = len(image_paths)
    print(f"Found {total} images. Starting indexing...\n")

    vdb = VectorDB()
    indexed = 0
    errors = 0

    for i, path in enumerate(image_paths, start=1):
        try:
            vdb.index_image(path, use_grounding_dino=False)
            indexed += 1
        except Exception as e:
            errors += 1
            print(f"  [ERROR] {path}: {e}")

        if i % 100 == 0 or i == total:
            print(f"  [{i}/{total}] processed — {indexed} indexed, {errors} errors")

    print(f"\nDone.")
    print(f"  Total processed : {total}")
    print(f"  Successfully indexed : {indexed}")
    print(f"  Errors               : {errors}")
    print(f"  Embedding dimensions : 512 (CLIP ViT-B/32)")


if __name__ == "__main__":
    main()
