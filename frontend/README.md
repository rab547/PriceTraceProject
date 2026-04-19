## Frontend (React + Vite)

A simple file upload interface that lets users submit images to the PriceTrace backend for indexing and search.

### Setup

From `frontend/`:

```bash
npm install
npm run dev
```

The app runs at `http://localhost:5173` by default.

> The Flask backend must also be running on port 5001. See `backend/README.md` for setup instructions.

### Usage

1. Click **Choose File** and select an image (jpg/png).
2. Click **Upload** to send it to the backend.
3. A success or error message will appear below the form.

### Project Structure

```
frontend/
├── src/
│   ├── App.jsx       # Main upload UI component
│   ├── App.css       # Component styles
│   ├── main.jsx      # React entry point
│   └── index.css     # Global styles
├── public/           # Static assets
├── index.html
└── vite.config.js
```
