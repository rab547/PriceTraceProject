"""
Bulk-index a directory of images into the PriceTrace ChromaDB.

Usage:
    python populate_db.py <image_directory> [--shop-only] [--batch-size=N]

Images are CLIP-embedded in batches for speed (default batch size: 32).
Re-running resumes from where it left off via the progress file.

Flags:
    --shop-only       Only index shop_*.jpg files (product shots, ~45K for
                      DeepFashion vs 239K total). Recommended for price tracking.
    --batch-size=N    Images per CLIP forward pass (default 32; use 64+ with GPU).
    --rebuild-progress  Seed the progress file from existing ChromaDB entries
                        so you can resume without re-indexing.
"""

import os
import sys
import time

from vector_db import VectorDB

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
DEFAULT_BATCH_SIZE = 32

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROGRESS_FILE = os.path.join(_BACKEND_DIR, "chroma_data", "populate_progress.txt")


def load_progress() -> set:
    if not os.path.exists(PROGRESS_FILE):
        return set()
    with open(PROGRESS_FILE) as f:
        return {line.strip() for line in f if line.strip()}


def mark_done(paths) -> None:
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "a") as f:
        for path in paths:
            f.write(path + "\n")


def collect_images(root: str, shop_only: bool = False):
    paths = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if os.path.splitext(fname)[1].lower() not in IMAGE_EXTENSIONS:
                continue
            if shop_only and not fname.lower().startswith("shop"):
                continue
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


def fmt_eta(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds/60:.0f}m"
    return f"{seconds/3600:.1f}h"


def main():
    raw_args = sys.argv[1:]
    shop_only = "--shop-only" in raw_args

    batch_size = DEFAULT_BATCH_SIZE
    for arg in raw_args:
        if arg.startswith("--batch-size="):
            batch_size = int(arg.split("=", 1)[1])

    args = [a for a in raw_args if not a.startswith("--")]

    if not args:
        print("Usage: python populate_db.py <image_directory> [--shop-only] [--batch-size=N]")
        sys.exit(1)

    root = args[0]
    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory.")
        sys.exit(1)

    if "--rebuild-progress" in raw_args:
        rebuild_progress(root)
        sys.exit(0)

    print(f"Scanning {root} for images{' (shop only)' if shop_only else ''}...")
    image_paths = collect_images(root, shop_only=shop_only)
    total = len(image_paths)

    done = load_progress()
    remaining = [p for p in image_paths if os.path.abspath(p) not in done]
    skipped = total - len(remaining)

    if skipped:
        print(f"Resuming: {skipped} already indexed, {len(remaining)} remaining.")
    else:
        print(f"Found {total} images.")

    print(f"Batch size: {batch_size}\n")

    if not remaining:
        print("Nothing to do.")
        sys.exit(0)

    vdb = VectorDB(image_root=root)
    indexed = 0
    errors = 0
    n = len(remaining)
    start = time.time()
    report_every = max(1, (n // batch_size) // 20) * batch_size  # ~20 progress lines

    for i in range(0, n, batch_size):
        batch = remaining[i:i + batch_size]
        indexed_paths, batch_errors = vdb.index_images_batch(batch)

        mark_done([os.path.abspath(p) for p in indexed_paths])
        indexed += len(indexed_paths)
        errors += len(batch_errors)

        for path, err in batch_errors:
            print(f"  [ERROR] {os.path.basename(path)}: {err}")

        done_count = i + len(batch)
        if done_count % report_every == 0 or done_count >= n:
            elapsed = time.time() - start
            rate = indexed / elapsed if elapsed > 0 else 0
            eta = (n - done_count) / rate if rate > 0 else 0
            print(f"  [{done_count}/{n}]  {rate:.1f} img/s  ETA {fmt_eta(eta)}", flush=True)

    elapsed = time.time() - start
    print(f"\nDone in {fmt_eta(elapsed)}.")
    print(f"  Indexed : {indexed}")
    print(f"  Errors  : {errors}")


if __name__ == "__main__":
    main()
