# PriceTraceProject

Current phase: building a basic file-upload web-application to be used in conjunction with ML processing.

---

## How It Works

1. The user visits the React frontend and selects a file to upload.
2. On submit, the frontend sends the file to the Flask backend via a `POST /upload` request.
3. The backend saves the file to `backend/uploads/` (auto-created on startup).
4. A placeholder pipeline function `process_file()` is called with the filename and prints it — this stub is where future ML pipeline processing will go.

---

## Project Structure


## Setup & Running

### Backend (Flask)

```bash
# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install flask flask-cors

# Run the server
cd backend
python app.py
```

The Flask server runs on `http://localhost:5000`.

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

The React app runs on `http://localhost:5173`.

---

## API

### `POST /upload`

Accepts a multipart form upload with a `file` field.

- Saves the file to `backend/uploads/`
- Calls `process_file(filename)` — a stub that prints the filename
- Returns a JSON response with the saved filename

**Success response:**
```json
{ "message": "File uploaded successfully", "filename": "example.pdf" }
```

**Error response:**
```json
{ "error": "No file provided" }
```

