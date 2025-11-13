from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", "/app/media")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "media-service"}), 200


@app.route("/upload", methods=["POST"])
def upload_media():
    """Upload media file"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(filepath)
        
        # Mock optimization (in real app: resize, compress, convert format)
        file_size = os.path.getsize(filepath)
        
        return jsonify({
            "filename": unique_filename,
            "size": file_size,
            "url": f"/media/{unique_filename}"
        }), 201
    
    return jsonify({"error": "Invalid file type"}), 400


@app.route("/media/<filename>", methods=["GET"])
def get_media(filename):
    """Serve media file"""
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({"error": "File not found"}), 404


@app.route("/media", methods=["GET"])
def list_media():
    """List all media files"""
    try:
        files = os.listdir(app.config["UPLOAD_FOLDER"])
        media_files = [{"filename": f, "url": f"/media/{f}"} for f in files if allowed_file(f)]
        return jsonify(media_files), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5010))
    app.run(host="0.0.0.0", port=port, debug=True)
