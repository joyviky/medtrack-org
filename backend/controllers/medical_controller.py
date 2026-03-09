import os
from datetime import datetime
from flask import request, jsonify
from werkzeug.utils import secure_filename

from backend.config.db import (
    medical_records_collection, patients_collection, notifications_collection
)
from backend.models.medical_record_model import medical_record_schema
from backend.models.notification_model import notification_schema
from backend.utils.helpers import format_doc, format_docs

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))), "uploads")

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_medical_record(current_user):
    """Upload a medical record/report."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": f"Allowed file types: {ALLOWED_EXTENSIONS}"}), 400

    record_type = request.form.get("recordType", "report")
    title = request.form.get("title", "Medical Record")
    description = request.form.get("description", "")
    patient_id = request.form.get("patientId", "")

    # Determine upload subfolder
    subfolder = "prescriptions" if record_type == "prescription" else "reports"
    upload_path = os.path.join(UPLOAD_FOLDER, subfolder)
    os.makedirs(upload_path, exist_ok=True)

    # Save file
    filename = secure_filename(
        f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    )
    filepath = os.path.join(upload_path, filename)
    file.save(filepath)

    # Determine patient
    if current_user["role"] == "patient":
        patient = patients_collection.find_one({"userId": current_user["_id"]})
        patient_id = str(patient["_id"]) if patient else current_user["_id"]
        doctor_id = None
    else:
        doctor_id = current_user["_id"]

    record = medical_record_schema(
        patient_id=patient_id,
        record_type=record_type,
        title=title,
        description=description,
        file_path=f"/uploads/{subfolder}/{filename}",
        doctor_id=doctor_id
    )

    result = medical_records_collection.insert_one(record)

    # Notify patient if doctor uploaded
    if current_user["role"] == "doctor" and patient_id:
        patient = patients_collection.find_one({"_id": patient_id})
        if patient:
            notif = notification_schema(
                user_id=patient["userId"],
                message=f"📋 New {record_type} uploaded: {title}",
                notif_type="prescription"
            )
            notifications_collection.insert_one(notif)

    return jsonify({
        "message": "Record uploaded successfully",
        "recordId": str(result.inserted_id)
    }), 201


def get_medical_records(current_user):
    """Get medical records (timeline) for a patient."""
    patient_id = request.args.get("patientId", "")

    if current_user["role"] == "patient":
        patient = patients_collection.find_one({"userId": current_user["_id"]})
        if patient:
            patient_id = str(patient["_id"])

    if not patient_id:
        return jsonify({"error": "Patient ID required"}), 400

    records = list(
        medical_records_collection.find(
            {"patientId": patient_id}
        ).sort("createdAt", -1)
    )

    return jsonify({"records": format_docs(records)}), 200


def get_record_by_id(current_user, record_id):
    """Get a specific medical record."""
    record = medical_records_collection.find_one({"_id": record_id})
    if not record:
        return jsonify({"error": "Record not found"}), 404

    return jsonify({"record": format_doc(record)}), 200
