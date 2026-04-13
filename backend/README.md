## Backend (Vector DB + Grounding DINO)

This backend supports:
- Uploading an image and indexing it into a local Chroma vector DB
- Optional detection via Grounding DINO (to crop detected regions)
- CLIP image embeddings (`openai/clip-vit-base-patch32`) for similarity search
- A simple Flask API for indexing and lookup

### Setup

From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PORT=5002 python app.py
```

Notes:
- The server defaults to **port 5001** if `PORT` is not set. If you already have something on 5000/5001, pick another port (e.g. `5002`).
- On first run, Hugging Face will download model weights. This project configures the cache to a writable project directory: `backend/.hf/`.

### Endpoints

- `POST /upload`
  - **form-data**:
    - `file`: image file (jpg/png)
    - `use_dino` (optional, default `true`): `true|false`
    - `prompt` (optional): Grounding DINO text prompt, using `.` to separate classes

- `POST /search`
  - **form-data**:
    - `file`: query image file (jpg/png)
    - `k` (optional, default `5`): number of nearest neighbors

### Example usage (curl)

Index an image (no detection; store full image embedding):

```bash
curl -s -X POST \
  -F "file=@test_image.png" \
  -F "use_dino=false" \
  "http://127.0.0.1:${PORT:-5002}/upload"
```

Index an image with Grounding DINO crops (detection + crop + embed each crop):

```bash
curl -s -X POST \
  -F "file=@test_image.png" \
  -F "use_dino=true" \
  -F "prompt=price tag. label. barcode." \
  "http://127.0.0.1:${PORT:-5002}/upload"
```

Search by image (returns top-k nearest neighbors already in Chroma):

```bash
curl -s -X POST \
  -F "file=@test_image.png" \
  -F "k=5" \
  "http://127.0.0.1:${PORT:-5002}/search"
```

### Local storage

- Uploaded files: `backend/uploads/`
- Chroma persistence: `backend/chroma_data/`
- Hugging Face model cache: `backend/.hf/`

### Troubleshooting

- If you see a warning about `torchvision` not being installed, the CLIP image processor will fall back to a PIL backend. This is OK for correctness; installing `torchvision` can remove the warning.

