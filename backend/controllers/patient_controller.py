from datetime import datetime
from flask import request, jsonify

from backend.config.db import patients_collection, users_collection
from backend.utils.helpers import format_doc


def get_patient_profile(current_user):
    """Get patient's own profile."""
    patient = patients_collection.find_one({"userId": current_user["_id"]})
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    return jsonify({"patient": format_doc(patient)}), 200


def update_patient_profile(current_user):
    """Patient updates their own profile."""
    data = request.get_json()
    user_id = current_user["_id"]

    update_fields = {}
    allowed = [
        "dateOfBirth", "gender", "bloodGroup", "address",
        "emergencyContact", "allergies", "conditions"
    ]

    for field in allowed:
        if field in data:
            update_fields[field] = data[field]

    if not update_fields:
        return jsonify({"error": "No fields to update"}), 400

    update_fields["updatedAt"] = datetime.utcnow()

    # Also update user-level fields if provided
    user_fields = {}
    if "fullName" in data:
        user_fields["fullName"] = data["fullName"]
    if "phone" in data:
        user_fields["phone"] = data["phone"]
    if user_fields:
        user_fields["updatedAt"] = datetime.utcnow()
        users_collection.update_one(
            {"_id": user_id},
            {"$set": user_fields}
        )

    patients_collection.update_one(
        {"userId": user_id},
        {"$set": update_fields}
    )

    return jsonify({"message": "Profile updated successfully"}), 200


def get_patient_by_id(current_user, patient_id):
    """Doctor or admin views a patient's profile with health alerts."""
    patient = patients_collection.find_one({"_id": patient_id})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    user = users_collection.find_one({"_id": patient["userId"]})
    patient["_id"] = str(patient["_id"])

    if user:
        patient["fullName"] = user.get("fullName", "")
        patient["email"] = user.get("email", "")
        patient["phone"] = user.get("phone", "")

    # Health alerts
    alerts = []
    if patient.get("allergies"):
        for allergy in patient["allergies"]:
            alerts.append(f"⚠ Patient allergic to {allergy}")
    if patient.get("conditions"):
        for condition in patient["conditions"]:
            alerts.append(f"⚠ Patient has {condition}")

    patient["healthAlerts"] = alerts

    return jsonify({"patient": patient}), 200
