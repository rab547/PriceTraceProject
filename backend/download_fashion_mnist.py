"""
Download Fashion MNIST and save images to ./fashion_images/.
Then populate the vector DB with:

    python populate_db.py ./fashion_images

No extra dependencies — uses torchvision which comes with torch.
"""

import os
import sys

from PIL import Image

try:
    from torchvision.datasets import FashionMNIST
except ImportError:
    print("torchvision not found. Install it with: pip install torchvision")
    sys.exit(1)

N = int(sys.argv[1]) if len(sys.argv) > 1 else 500
OUT_DIR = os.path.join(os.path.dirname(__file__), "fashion_images")

LABELS = [
    "tshirt", "trouser", "pullover", "dress", "coat",
    "sandal", "shirt", "sneaker", "bag", "ankle_boot",
]

print(f"Downloading Fashion MNIST (first {N} images)...")
dataset = FashionMNIST(root="/tmp/fmnist", train=True, download=True)

os.makedirs(OUT_DIR, exist_ok=True)
for i in range(min(N, len(dataset))):
    img_tensor, label = dataset[i]
    label_name = LABELS[label]
    path = os.path.join(OUT_DIR, f"{i:05d}_{label_name}.png")
    img_tensor.save(path)

print(f"Saved {N} images to {OUT_DIR}")
print(f"Now run: python populate_db.py {OUT_DIR}")
