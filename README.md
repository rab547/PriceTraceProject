# PriceTraceProject

A full-stack web application for visual fashion search. Upload a photo of a clothing item and get visually similar results back, powered by CLIP embeddings and a local ChromaDB vector index.

**Stack:** Flask · React · CLIP (ViT-B/32) · ChromaDB · optional Grounding DINO

---

## Project Structure

```
PriceTraceProject/
├── backend/
│   ├── app.py                  # Flask API
│   ├── vector_db.py            # CLIP embeddings + ChromaDB wrapper
│   ├── populate_db.py          # Bulk-index a dataset folder
│   ├── remap_paths.py          # Update image paths in the DB if dataset moves
│   ├── requirements.txt
│   ├── .env.example            # Copy to .env and fill in your dataset path
│   ├── chroma_data/            # Local vector DB (gitignored)
│   └── uploads/                # Temp query images (gitignored)
└── frontend/
    ├── src/
    │   └── App.jsx
    └── package.json
```

---

## First-Time Setup

### 1. Python environment

```powershell
# From the project root
.\venv\Scripts\activate
pip install -r backend\requirements.txt
```

### 2. Dataset

This project uses the [DeepFashion](http://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html) dataset.
Place it anywhere on your machine, then create `backend\.env` from the example:

```powershell
copy backend\.env.example backend\.env
```

Edit `.env` and set your path:

```
FASHION_IMAGES_DIR=C:\path\to\your\deepFashion
```

### 3. Build the vector index

```powershell
cd backend

# Recommended: shop images only (~45K images, ~1-2 hours on CPU)
python populate_db.py "C:\path\to\your\deepFashion" --shop-only

# Or index everything (~239K images, runs overnight)
python populate_db.py "C:\path\to\your\deepFashion"
```

The script is resumable — if interrupted, re-run the same command and it picks up where it left off.

On first run, Hugging Face will download CLIP model weights to `backend/.hf/` (~600 MB).

### 4. Run the backend

```powershell
# From backend/
python app.py
```

Server runs on `http://localhost:5001` by default. Set `PORT` to override.

### 5. Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

---

## Setup for Collaborators (skip re-indexing)

If someone shares the pre-built `chroma_data/` folder (or `chroma_data.zip`):

1. Unzip into `backend/chroma_data/`
2. Get the DeepFashion dataset and set `FASHION_IMAGES_DIR` in `backend/.env`
3. Run `python app.py` — no indexing needed

---

## API

### `POST /upload`

Index an image into the vector DB.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file` | file | required | Image to index |
| `use_dino` | bool | `true` | Use Grounding DINO to detect and crop objects before indexing |
| `prompt` | string | built-in | DINO detection prompt (dot-separated class names) |

### `POST /search`

Find visually similar images already in the DB.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file` | file | required | Query image |
| `k` | int | `10` | Number of results |
| `min_similarity` | float | `0.0` | Minimum cosine similarity threshold |

Returns a ranked list of `{ image_path, similarity }` pairs.

### `GET /image?path=<path>`

Serve an image by its stored path (used by the frontend to display results).

---

## Utilities

**Re-index after moving your dataset:**

```powershell
python remap_paths.py "C:\old\path\to\deepFashion" "C:\new\path\to\deepFashion"
```

**Batch size tuning** (use larger values with a GPU):

```powershell
python populate_db.py "C:\path\to\deepFashion" --shop-only --batch-size=64
```
