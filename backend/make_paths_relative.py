"""
Convert absolute image_path metadata in ChromaDB to relative paths.

Run once after the DB was populated without image_root set. After this,
anyone can set FASHION_IMAGES_DIR in their .env and paths will resolve correctly.

Usage:
    python make_paths_relative.py <dataset_root>

Example:
    python make_paths_relative.py "C:\\Users\\sachh\\datasets\\deepFashion"
"""

import os
import sys

from vector_db import VectorDB

BATCH_SIZE = 500


def main():
    if len(sys.argv) != 2:
        print("Usage: python make_paths_relative.py <dataset_root>")
        sys.exit(1)

    old_root = os.path.normpath(sys.argv[1])

    vdb = VectorDB()
    collection = vdb._collection
    total = collection.count()
    print(f"Found {total} records.")
    print(f"Stripping prefix: '{old_root}'\n")

    updated = 0
    skipped = 0
    offset = 0

    while offset < total:
        batch = collection.get(limit=BATCH_SIZE, offset=offset, include=["metadatas"])
        ids = batch["ids"]
        metadatas = batch["metadatas"]

        new_metadatas = []
        for meta in metadatas:
            new_meta = dict(meta)
            path = new_meta.get("image_path", "")
            norm = os.path.normpath(path)
            try:
                rel = os.path.relpath(norm, old_root)
            except ValueError:
                rel = None

            if rel and not rel.startswith(".."):
                new_meta["image_path"] = rel
                updated += 1
            else:
                skipped += 1
            new_metadatas.append(new_meta)

        collection.update(ids=ids, metadatas=new_metadatas)
        offset += len(ids)

        if offset % 5000 == 0 or offset >= total:
            print(f"  [{min(offset, total)}/{total}] — {updated} updated, {skipped} skipped")

    print(f"\nDone. {updated} paths made relative, {skipped} skipped.")


if __name__ == "__main__":
    main()
