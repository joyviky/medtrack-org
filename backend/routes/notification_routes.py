from flask import Blueprint, jsonify, request
from datetime import datetime

from backend.config.db import (
    notifications_collection, users_collection, doctors_collection,
    patients_collection, appointments_collection
)
from backend.middleware.auth_middleware import token_required, role_required
from backend.utils.helpers import format_docs, suggest_departments

notification_bp = Blueprint("notification", __name__)


@notification_bp.route("/", methods=["GET"])
@token_required
def get_notifications(current_user):
    """Get all notifications for the current user."""
    notifications = list(
        notifications_collection.find(
            {"userId": current_user["_id"]}
        ).sort("createdAt", -1).limit(50)
    )
    unread = notifications_collection.count_documents({
        "userId": current_user["_id"],
        "readStatus": False
    })

    return jsonify({
        "notifications": format_docs(notifications),
        "unreadCount": unread
    }), 200


@notification_bp.route("/read/<notif_id>", methods=["PUT"])
@token_required
def mark_as_read(current_user, notif_id):
    """Mark a notification as read."""
    notifications_collection.update_one(
        {"_id": notif_id, "userId": current_user["_id"]},
        {"$set": {"readStatus": True}}
    )
    return jsonify({"message": "Notification marked as read"}), 200


@notification_bp.route("/read-all", methods=["PUT"])
@token_required
def mark_all_read(current_user):
    """Mark all notifications as read."""
    notifications_collection.update_many(
        {"userId": current_user["_id"]},
        {"$set": {"readStatus": True}}
    )
    return jsonify({"message": "All notifications marked as read"}), 200


# ─── Admin Analytics ─────────────────────────────────────────
@notification_bp.route("/admin/analytics", methods=["GET"])
@token_required
@role_required("admin")
def admin_analytics(current_user):
    """Admin analytics dashboard data."""
    today = datetime.utcnow().strftime("%Y-%m-%d")

    total_patients = patients_collection.count_documents({})
    total_doctors = doctors_collection.count_documents({})
    total_appointments = appointments_collection.count_documents({})
    today_appointments = appointments_collection.count_documents({"date": today})
    pending_appointments = appointments_collection.count_documents({"status": "pending"})

    # Popular specializations
    pipeline = [
        {"$group": {"_id": "$specialization", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    popular_specs = list(doctors_collection.aggregate(pipeline))

    # Recent appointments
    recent = list(
        appointments_collection.find().sort("createdAt", -1).limit(10)
    )

    return jsonify({
        "totalPatients": total_patients,
        "totalDoctors": total_doctors,
        "totalAppointments": total_appointments,
        "todayAppointments": today_appointments,
        "pendingAppointments": pending_appointments,
        "popularSpecializations": [
            {"name": s["_id"], "count": s["count"]} for s in popular_specs
        ],
        "recentAppointments": format_docs(recent)
    }), 200


# ─── Admin: Manage Doctors ────────────────────────────────────
@notification_bp.route("/admin/doctors", methods=["GET"])
@token_required
@role_required("admin")
def admin_get_doctors(current_user):
    """Admin get all doctors (approved and pending)."""
    doctors = list(doctors_collection.find())
    result = []
    for doc in doctors:
        user = users_collection.find_one({"_id": doc["userId"]})
        doc["_id"] = str(doc["_id"])
        if user:
            doc["fullName"] = user.get("fullName", "")
            doc["email"] = user.get("email", "")
        result.append(doc)

    return jsonify({"doctors": result}), 200


@notification_bp.route("/admin/doctors/approve/<doctor_id>", methods=["PUT"])
@token_required
@role_required("admin")
def approve_doctor(current_user, doctor_id):
    """Admin approves a doctor registration."""
    doctors_collection.update_one(
        {"_id": doctor_id},
        {"$set": {"isApproved": True, "updatedAt": datetime.utcnow()}}
    )
    return jsonify({"message": "Doctor approved successfully"}), 200


# ─── Symptom Suggestion API ──────────────────────────────────
@notification_bp.route("/symptoms/suggest", methods=["POST"])
def symptom_suggestion():
    """AI symptom suggestion — suggests departments based on symptoms."""
    data = request.get_json()
    symptoms = data.get("symptoms", "")
    if not symptoms:
        return jsonify({"error": "Please provide symptoms text"}), 400

    result = suggest_departments(symptoms)
    return jsonify(result), 200
