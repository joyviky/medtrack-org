import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)
    )), "frontend"),
    static_url_path=""
)

CORS(app)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "medtrack-secret")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

# ─── Register Blueprints ─────────────────────────────────────
from backend.routes.auth_routes import auth_bp
from backend.routes.doctor_routes import doctor_bp
from backend.routes.patient_routes import patient_bp
from backend.routes.appointment_routes import appointment_bp
from backend.routes.medical_routes import medical_bp
from backend.routes.notification_routes import notification_bp
from backend.routes.admin_routes import admin_bp

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(doctor_bp, url_prefix="/api/doctors")
app.register_blueprint(patient_bp, url_prefix="/api/patients")
app.register_blueprint(appointment_bp, url_prefix="/api/appointments")
app.register_blueprint(medical_bp, url_prefix="/api/medical")
app.register_blueprint(notification_bp, url_prefix="/api/notifications")
app.register_blueprint(admin_bp, url_prefix="/api/admin")

# ─── Serve uploaded files ────────────────────────────────────
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
)), "uploads")


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ─── Serve Frontend Pages ────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/pages/<path:filename>")
def serve_page(filename):
    return send_from_directory(
        os.path.join(app.static_folder, "pages"), filename
    )


# ─── Health Check ────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "MedTrack API is running 🏥"
    }), 200


if __name__ == "__main__":
    # Create upload directories
    os.makedirs(os.path.join(UPLOAD_FOLDER, "reports"), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, "prescriptions"), exist_ok=True)

    # Initialize database indexes
    from backend.config.db import init_indexes
    init_indexes()

    print("[MedTrack] Server starting on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
