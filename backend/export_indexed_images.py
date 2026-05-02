"""
Copy only the images that are indexed in ChromaDB to an output folder.

Useful for sharing a smaller dataset bundle alongside chroma_data/ — collaborators
point FASHION_IMAGES_DIR at the exported folder instead of the full dataset.

Usage:
    python export_indexed_images.py <output_dir>

Example:
    python export_indexed_images.py ../indexed_images
"""

import os
import sys
import shutil
from dotenv import load_dotenv

load_dotenv()

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) != 2:
        print("Usage: python export_indexed_images.py <output_dir>")
        sys.exit(1)

    output_dir = os.path.abspath(sys.argv[1])
    image_root = os.environ.get("FASHION_IMAGES_DIR")

    if not image_root:
        print("Error: FASHION_IMAGES_DIR is not set in .env")
        sys.exit(1)

    import chromadb
    client = chromadb.PersistentClient(path=os.path.join(_BACKEND_DIR, "chroma_data"))
    col = client.get_collection("pricetrace_images")

    print(f"Reading {col.count()} entries from ChromaDB...")
    result = col.get(include=["metadatas"])
    rel_paths = {m["image_path"] for m in result["metadatas"] if m.get("image_path")}

    print(f"Found {len(rel_paths)} unique images. Copying to {output_dir} ...\n")
    os.makedirs(output_dir, exist_ok=True)

    copied = 0
    missing = 0

    for i, rel_path in enumerate(rel_paths, 1):
        src = os.path.join(image_root, rel_path)
        dst = os.path.join(output_dir, rel_path)

        if not os.path.isfile(src):
            missing += 1
            continue

        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

        if i % 5000 == 0 or i == len(rel_paths):
            print(f"  [{i}/{len(rel_paths)}] {copied} copied, {missing} missing")

    print(f"\nDone. {copied} images exported to {output_dir}")
    if missing:
        print(f"  {missing} files were missing from FASHION_IMAGES_DIR and skipped.")
    print(f"\nCollaborators should set FASHION_IMAGES_DIR to point at this folder.")


if __name__ == "__main__":
    main()
