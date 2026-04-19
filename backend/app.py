import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from vector_db import VectorDB

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_preferred_uploads = os.path.join(BASE_DIR, "uploads")
try:
    os.makedirs(_preferred_uploads, exist_ok=True)
    UPLOAD_FOLDER = _preferred_uploads
except PermissionError:
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "pricetrace_uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

_vdb = VectorDB()


def process_file(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    prompt = request.form.get(
        "prompt",
        "shirt. pants. shoes. jacket. desk. chair. keyboard. mouse. plant. monitor. makeup. brush. palette. lipstick. perfume.",
    )
    use_dino = request.form.get("use_dino", "true").lower() in {"1", "true", "yes", "y"}
    indexed = _vdb.index_image(
        file_path,
        use_grounding_dino=use_dino,
        text_prompt=prompt,
    )
    return indexed


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No filename provided"}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)
    indexed = process_file(filename)
    return jsonify({"message": "File uploaded successfully", "filename": filename, "index": indexed})


@app.route("/search", methods=["POST"])
def search():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No filename provided"}), 400
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], f"query_{secure_filename(file.filename)}")
    file.save(file_path)
    k = int(request.form.get("k", "5"))
    results = _vdb.search_by_image(file_path, k=k)
    return jsonify(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(debug=True, port=port)
