"""
Bulk-index a directory of images into the PriceTrace ChromaDB.

Usage:
    python populate_db.py /path/to/deepfashion/images

Each image is embedded with CLIP (no Grounding DINO) and stored with its
absolute file path in metadata so the frontend can retrieve it later.

Re-running the script resumes from where it left off — already-indexed
images are skipped based on the progress file in chroma_data/.
"""

import os
import sys

from vector_db import VectorDB

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROGRESS_FILE = os.path.join(_BACKEND_DIR, "chroma_data", "populate_progress.txt")


def load_progress() -> set:
    if not os.path.exists(PROGRESS_FILE):
        return set()
    with open(PROGRESS_FILE) as f:
        return {line.strip() for line in f if line.strip()}


def mark_done(path: str) -> None:
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "a") as f:
        f.write(path + "\n")


def collect_images(root: str):
    paths = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if os.path.splitext(fname)[1].lower() in IMAGE_EXTENSIONS:
                paths.append(os.path.join(dirpath, fname))
    return paths


def rebuild_progress(root: str) -> None:
    """Seed the progress file from paths already stored in ChromaDB."""
    import chromadb

    persist_dir = os.path.join(_BACKEND_DIR, "chroma_data")
    client = chromadb.PersistentClient(path=persist_dir)
    try:
        collection = client.get_collection("pricetrace_images")
    except Exception:
        print("No existing collection found.")
        return

    print("Reading existing entries from ChromaDB (this may take a moment)...")
    result = collection.get(include=["metadatas"])
    metadatas = result.get("metadatas") or []

    abs_root = os.path.abspath(root)
    paths = set()
    for meta in metadatas:
        rel = meta.get("image_path", "")
        if rel:
            paths.add(os.path.abspath(os.path.join(abs_root, rel)))

    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        for p in paths:
            f.write(p + "\n")

    print(f"Progress file seeded with {len(paths)} entries -> {PROGRESS_FILE}")
    print("You can now run the script normally to resume indexing.")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not args:
        print("Usage: python populate_db.py <image_directory> [--rebuild-progress]")
        sys.exit(1)

    root = args[0]
    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory.")
        sys.exit(1)

    if "--rebuild-progress" in sys.argv:
        rebuild_progress(root)
        sys.exit(0)

    print(f"Scanning {root} for images...")
    image_paths = collect_images(root)
    total = len(image_paths)

    done = load_progress()
    remaining = [p for p in image_paths if os.path.abspath(p) not in done]
    skipped = total - len(remaining)

    if skipped:
        print(f"Resuming: {skipped} already indexed, {len(remaining)} remaining.\n")
    else:
        print(f"Found {total} images. Starting indexing...\n")

    vdb = VectorDB(image_root=root)
    indexed = 0
    errors = 0
    n = len(remaining)

    for i, path in enumerate(remaining, start=1):
        abs_path = os.path.abspath(path)
        try:
            vdb.index_image(abs_path, use_grounding_dino=False)
            indexed += 1
            mark_done(abs_path)
        except Exception as e:
            errors += 1
            print(f"  [ERROR] {path}: {e}")

        if i % 100 == 0 or i == n:
            print(f"  [{i}/{n}] processed — {indexed} indexed, {errors} errors")

    print(f"\nDone.")
    print(f"  Total processed : {n}")
    print(f"  Successfully indexed : {indexed}")
    print(f"  Errors               : {errors}")
    print(f"  Embedding dimensions : 512 (CLIP ViT-B/32)")


if __name__ == "__main__":
    main()
