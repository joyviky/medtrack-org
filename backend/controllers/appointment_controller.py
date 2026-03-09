from datetime import datetime
from flask import request, jsonify

from backend.config.db import (
    appointments_collection, doctors_collection, patients_collection,
    users_collection, notifications_collection, reviews_collection
)
from backend.models.appointment_model import appointment_schema
from backend.models.notification_model import notification_schema
from backend.models.review_model import review_schema
from backend.utils.helpers import format_doc, format_docs


def book_appointment(current_user):
    """Patient books an appointment."""
    data = request.get_json()

    required = ["doctorId", "date", "timeSlot"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"'{field}' is required"}), 400

    # Check doctor exists — try doctors collection _id first, then userId
    doctor = doctors_collection.find_one({"_id": data["doctorId"]})

    if not doctor:
        doctor = doctors_collection.find_one({"userId": data["doctorId"]})

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    doc_id_str = str(doctor["_id"])
    user_id_str = str(doctor.get("userId", ""))

    # Check slot availability using BOTH doctor IDs
    existing = appointments_collection.find_one({
        "$or": [{"doctorId": doc_id_str}, {"doctorId": user_id_str}],
        "date": data["date"],
        "timeSlot": data["timeSlot"],
        "status": {"$in": ["pending", "approved"]}
    })

    if existing:
        return jsonify({"error": "This time slot is already booked"}), 409

    # Get patient profile
    patient = patients_collection.find_one({"userId": current_user["_id"]})
    patient_id = str(patient["_id"]) if patient else current_user["_id"]

    # Get doctor user info for storing name
    doctor_user = users_collection.find_one({"_id": doctor["userId"]})
    doctor_name = doctor_user.get("fullName", "") if doctor_user else ""

    appointment = appointment_schema(
        patient_id=patient_id,
        doctor_id=data["doctorId"],
        date=data["date"],
        time_slot=data["timeSlot"],
        reason=data.get("reason", ""),
        is_emergency=data.get("isEmergency", False)
    )
    # Store extra info for display
    appointment["doctorName"] = doctor_name
    appointment["patientName"] = current_user.get("fullName", "")
    appointment["specialization"] = doctor.get("specialization", "")

    result = appointments_collection.insert_one(appointment)

    # Notify doctor
    if doctor_user:
        notif_type = "emergency" if data.get("isEmergency") else "appointment"
        prefix = "🚨 EMERGENCY: " if data.get("isEmergency") else ""
        notif = notification_schema(
            user_id=doctor["userId"],
            message=f"{prefix}New appointment request from {current_user['fullName']} on {data['date']} at {data['timeSlot']}",
            notif_type=notif_type
        )
        notifications_collection.insert_one(notif)

    return jsonify({
        "message": "Appointment booked successfully",
        "appointmentId": str(result.inserted_id)
    }), 201


def get_patient_appointments(current_user):
    """Get all appointments for a patient."""
    user_id = current_user["_id"]
    status = request.args.get("status", "")

    # Query by patientId matching either user._id OR patients_collection._id
    patient = patients_collection.find_one({"userId": user_id})
    patient_obj_id = str(patient["_id"]) if patient else None

    # Build OR query to catch seeded (userId) and newly booked (patient._id)
    or_conditions = [{"patientId": user_id}]
    if patient_obj_id:
        or_conditions.append({"patientId": patient_obj_id})

    query = {"$or": or_conditions}
    if status:
        query["status"] = status

    appointments = list(
        appointments_collection.find(query).sort("date", -1)
    )

    # Enrich with doctor info
    for appt in appointments:
        appt["_id"] = str(appt["_id"])
        # Try doctorId as doctors._id first, then as userId
        doc = doctors_collection.find_one({"_id": appt["doctorId"]})
        if not doc:
            doc = doctors_collection.find_one({"userId": appt["doctorId"]})
        if doc:
            user = users_collection.find_one({"_id": doc["userId"]})
            appt["doctorName"] = user.get("fullName", appt.get("doctorName", "")) if user else appt.get("doctorName", "")
            appt["specialization"] = doc.get("specialization", appt.get("specialization", ""))
        # Keep seeded names as fallback
        if not appt.get("doctorName"):
            appt["doctorName"] = appt.get("doctorName", "Doctor")

    return jsonify({"appointments": appointments}), 200


def get_doctor_appointments(current_user):
    """Get all appointments for a doctor."""
    user_id = current_user["_id"]
    doctor = doctors_collection.find_one({"userId": user_id})

    status = request.args.get("status", "")
    date = request.args.get("date", "")

    # Query by doctorId matching either doctor._id OR userId
    or_conditions = [{"doctorId": user_id}]
    if doctor:
        or_conditions.append({"doctorId": str(doctor["_id"])})

    query = {"$or": or_conditions}
    if status:
        query["status"] = status
    if date:
        query["date"] = date

    appointments = list(
        appointments_collection.find(query).sort("date", -1)
    )

    # Enrich with patient info
    for appt in appointments:
        appt["_id"] = str(appt["_id"])
        # Try patientId as patients._id first, then as userId
        pat = patients_collection.find_one({"_id": appt["patientId"]})
        if not pat:
            pat = patients_collection.find_one({"userId": appt["patientId"]})
        if pat:
            user = users_collection.find_one({"_id": pat["userId"]})
            appt["patientName"] = user.get("fullName", appt.get("patientName", "")) if user else appt.get("patientName", "")
            appt["patientAlerts"] = []
            if pat.get("allergies"):
                appt["patientAlerts"].extend([f"Allergic to {a}" for a in pat["allergies"]])
            if pat.get("conditions"):
                appt["patientAlerts"].extend(pat["conditions"])
        if not appt.get("patientName"):
            appt["patientName"] = appt.get("patientName", "Patient")

    return jsonify({"appointments": appointments}), 200


def update_appointment_status(current_user):
    """Doctor updates appointment status."""
    data = request.get_json()

    if "appointmentId" not in data or "status" not in data:
        return jsonify({"error": "appointmentId and status are required"}), 400

    valid_statuses = ["approved", "completed", "cancelled", "prescription_uploaded"]
    if data["status"] not in valid_statuses:
        return jsonify({"error": f"Status must be one of: {valid_statuses}"}), 400

    appointment = appointments_collection.find_one(
        {"_id": data["appointmentId"]}
    )
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    update = {
        "status": data["status"],
        "updatedAt": datetime.utcnow()
    }

    if "notes" in data:
        update["notes"] = data["notes"]
    if "prescription" in data:
        update["prescription"] = data["prescription"]

    appointments_collection.update_one(
        {"_id": data["appointmentId"]},
        {"$set": update}
    )

    # Notify patient
    patient = patients_collection.find_one(
        {"_id": appointment["patientId"]}
    )
    if patient:
        status_messages = {
            "approved": "✅ Your appointment has been approved",
            "completed": "✅ Your appointment is marked as completed",
            "cancelled": "❌ Your appointment has been cancelled",
            "prescription_uploaded": "📋 A prescription has been uploaded for your appointment"
        }
        notif = notification_schema(
            user_id=patient["userId"],
            message=f"{status_messages.get(data['status'], 'Appointment updated')} on {appointment['date']} at {appointment['timeSlot']}",
            notif_type="appointment"
        )
        notifications_collection.insert_one(notif)

    return jsonify({"message": f"Appointment {data['status']} successfully"}), 200


def get_appointment_details(current_user, appointment_id):
    """Get details of a specific appointment."""
    appointment = appointments_collection.find_one(
        {"_id": appointment_id}
    )
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    appointment = format_doc(appointment)

    # Add doctor info
    doc = doctors_collection.find_one({"_id": appointment["doctorId"]})
    if not doc:
        doc = doctors_collection.find_one({"userId": appointment["doctorId"]})
    if doc:
        user = users_collection.find_one({"_id": doc["userId"]})
        appointment["doctorName"] = user.get("fullName", "") if user else ""
        appointment["specialization"] = doc.get("specialization", "")
        appointment["consultationFee"] = doc.get("consultationFee", 0)

    # Add patient info
    pat = patients_collection.find_one({"_id": appointment["patientId"]})
    if not pat:
        pat = patients_collection.find_one({"userId": appointment["patientId"]})
    if pat:
        user = users_collection.find_one({"_id": pat["userId"]})
        appointment["patientName"] = user.get("fullName", "") if user else ""
        appointment["healthAlerts"] = []
        if pat.get("allergies"):
            appointment["healthAlerts"].extend(
                [f"⚠ Allergic to {a}" for a in pat["allergies"]]
            )
        if pat.get("conditions"):
            appointment["healthAlerts"].extend(
                [f"⚠ Has {c}" for c in pat["conditions"]]
            )

    return jsonify({"appointment": appointment}), 200


def emergency_booking(current_user):
    """Find next available doctor for emergency."""
    data = request.get_json() or {}
    specialization = data.get("specialization", "")

    query = {"$or": [{"isApproved": True}, {"isApproved": {"$exists": False}}]}
    if specialization:
        query["specialization"] = {"$regex": specialization, "$options": "i"}

    # Get all matching doctors sorted by least appointments today
    doctors = list(doctors_collection.find(query))

    today = datetime.utcnow().strftime("%Y-%m-%d")
    best_doctor = None
    min_appointments = float("inf")

    for doc in doctors:
        doc_id = str(doc["_id"])
        user_id = str(doc.get("userId", ""))
        count = appointments_collection.count_documents({
            "$or": [{"doctorId": doc_id}, {"doctorId": user_id}],
            "date": today,
            "status": {"$in": ["pending", "approved"]}
        })
        if count < min_appointments:
            min_appointments = count
            best_doctor = doc

    if not best_doctor:
        return jsonify({"error": "No doctors available for emergency"}), 404

    user = users_collection.find_one({"_id": best_doctor["userId"]})
    best_doctor["_id"] = str(best_doctor["_id"])
    if user:
        best_doctor["fullName"] = user.get("fullName", "")

    return jsonify({
        "message": "Emergency doctor found",
        "doctor": best_doctor,
        "todayAppointments": min_appointments
    }), 200


def add_review(current_user):
    """Patient adds a review for a doctor."""
    data = request.get_json()

    required = ["doctorId", "rating"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"'{field}' is required"}), 400

    patient = patients_collection.find_one({"userId": current_user["_id"]})
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    # Check if patient had a completed appointment with this doctor
    completed = appointments_collection.find_one({
        "patientId": str(patient["_id"]),
        "doctorId": data["doctorId"],
        "status": {"$in": ["completed", "prescription_uploaded"]}
    })

    if not completed:
        return jsonify({"error": "You can only review doctors after a completed appointment"}), 403

    review = review_schema(
        patient_id=str(patient["_id"]),
        doctor_id=data["doctorId"],
        rating=data["rating"],
        comment=data.get("comment", "")
    )

    reviews_collection.insert_one(review)

    # Update doctor's average rating
    all_reviews = list(reviews_collection.find({"doctorId": data["doctorId"]}))
    avg = sum(r["rating"] for r in all_reviews) / len(all_reviews)
    doctors_collection.update_one(
        {"_id": data["doctorId"]},
        {"$set": {"avgRating": round(avg, 1), "totalReviews": len(all_reviews)}}
    )

    return jsonify({"message": "Review added successfully"}), 201
