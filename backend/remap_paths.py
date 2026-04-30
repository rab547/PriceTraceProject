"""
Update image_path metadata in an existing ChromaDB when the image directory has moved.

Usage:
    python remap_paths.py <old_prefix> <new_prefix>

Example (teammate downloading the DB):
    python remap_paths.py "C:\\Users\\sachh\\datasets\\fashion" "C:\\Users\\bob\\datasets\\fashion"
"""

import os
import sys

from vector_db import VectorDB

BATCH_SIZE = 500


def main():
    if len(sys.argv) < 3:
        print("Usage: python remap_paths.py <old_prefix> <new_prefix>")
        sys.exit(1)

    old_prefix = os.path.normpath(sys.argv[1])
    new_prefix = os.path.normpath(sys.argv[2])

    vdb = VectorDB()
    collection = vdb._collection
    total = collection.count()
    print(f"Found {total} records.")
    print(f"Remapping: '{old_prefix}' → '{new_prefix}'\n")

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
            path = os.path.normpath(new_meta.get("image_path", ""))
            if path.startswith(old_prefix):
                new_meta["image_path"] = new_prefix + path[len(old_prefix):]
                updated += 1
            else:
                skipped += 1
            new_metadatas.append(new_meta)

        collection.update(ids=ids, metadatas=new_metadatas)
        offset += len(ids)

        if offset % 5000 == 0 or offset >= total:
            print(f"  [{min(offset, total)}/{total}] processed — {updated} updated, {skipped} skipped")

    print(f"\nDone. Updated {updated}/{total} records.")


if __name__ == "__main__":
    main()
