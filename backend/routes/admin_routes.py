from flask import Blueprint, jsonify
from backend.middleware.auth_middleware import token_required, role_required
from backend.config.db import get_db

admin_bp = Blueprint("admin", __name__)


def get_all_doctors_admin(current_user):
    """Admin: Get all doctors with full details."""
    db = get_db()
    doctors = list(db.users.find({"role": "doctor"}, {"password": 0}))
    for d in doctors:
        d["_id"] = str(d["_id"])
    return jsonify({"doctors": doctors}), 200


def get_all_patients_admin(current_user):
    """Admin: Get all patients."""
    db = get_db()
    patients = list(db.users.find({"role": "patient"}, {"password": 0}))
    for p in patients:
        p["_id"] = str(p["_id"])
        # Count appointments
        try:
            p["appointmentCount"] = db.appointments.count_documents({"patientId": p["_id"]})
        except Exception:
            p["appointmentCount"] = 0
    return jsonify({"patients": patients}), 200


def get_all_appointments_admin(current_user):
    """Admin: Get all appointments."""
    db = get_db()

    appointments = list(db.appointments.find({}).sort("date", -1).limit(500))
    result = []
    for a in appointments:
        a["_id"] = str(a["_id"])
        # Enrich with names
        try:
            patient = db.users.find_one({"_id": a.get("patientId")}, {"fullName": 1, "email": 1})
            doctor = db.users.find_one({"_id": a.get("doctorId")}, {"fullName": 1, "specialization": 1})
            a["patientName"] = patient.get("fullName", "Unknown") if patient else a.get("patientName", "Unknown")
            a["doctorName"] = doctor.get("fullName", "Unknown") if doctor else a.get("doctorName", "Unknown")
            a["specialization"] = doctor.get("specialization", "General") if doctor else a.get("specialization", "General")
        except Exception:
            a["patientName"] = a.get("patientName", "Unknown")
            a["doctorName"] = a.get("doctorName", "Unknown")
        result.append(a)
    return jsonify({"appointments": result}), 200


def verify_doctor_admin(current_user, doctor_id):
    """Admin: Verify a doctor."""
    db = get_db()
    try:
        db.users.update_one({"_id": doctor_id}, {"$set": {"isVerified": True}})
        return jsonify({"message": "Doctor verified successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def remove_doctor_admin(current_user, doctor_id):
    """Admin: Remove a doctor."""
    db = get_db()
    try:
        db.users.delete_one({"_id": doctor_id, "role": "doctor"})
        return jsonify({"message": "Doctor removed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Register routes
admin_bp.route("/doctors", methods=["GET"])(
    token_required(role_required("admin")(get_all_doctors_admin))
)
admin_bp.route("/patients", methods=["GET"])(
    token_required(role_required("admin")(get_all_patients_admin))
)
admin_bp.route("/appointments", methods=["GET"])(
    token_required(role_required("admin")(get_all_appointments_admin))
)
admin_bp.route("/doctors/<doctor_id>/verify", methods=["PUT"])(
    token_required(role_required("admin")(verify_doctor_admin))
)
admin_bp.route("/doctors/<doctor_id>", methods=["DELETE"])(
    token_required(role_required("admin")(remove_doctor_admin))
)
