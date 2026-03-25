# PriceTraceProject

Current phase: building a basic file-upload web-application to be used in conjunction with ML processing. 

---

## How It Works

1. The user visits the React frontend and selects a file to upload.
2. On submit, the frontend sends the file to the Flask backend via a `POST /upload` request.
3. The backend saves the file to a designated `uploads/` folder.
4. A placeholder pipeline function is called with the filename and prints it — this stub is where future processing logic will go.


## Setup & Running

### Backend (Flask)

```bash
cd backend
pip install flask flask-cors
python app.py
```

The Flask server runs on `http://localhost:5000`.

### Frontend (React) (Not made yet)

```bash
cd frontend
npm install
npm start
```

The React app runs on `http://localhost:3000`.
