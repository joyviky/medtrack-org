from datetime import datetime
from flask import request, jsonify

from backend.config.db import (
    doctors_collection, users_collection, appointments_collection,
    reviews_collection
)
from backend.utils.helpers import (
    format_doc, format_docs, generate_time_slots
)


def get_all_doctors():
    """Get list of all approved doctors with user info."""
    specialization = request.args.get("specialization", "")
    sort_by = request.args.get("sort", "avgRating")

    try:
        # Include doctors that are approved OR don't have isApproved field yet
        query = {"$or": [{"isApproved": True}, {"isApproved": {"$exists": False}}]}
        if specialization:
            query["specialization"] = {"$regex": specialization, "$options": "i"}

        doctors = list(doctors_collection.find(query).sort(sort_by, -1))

        result = []
        for doc in doctors:
            user = users_collection.find_one({"_id": doc["userId"]})
            doc["_id"] = str(doc["_id"])
            doc["userId"] = str(doc.get("userId", ""))
            if user:
                doc["fullName"] = user.get("fullName", "")
                doc["email"] = user.get("email", "")
                doc["phone"] = user.get("phone", "")
            # Ensure totalReviews field exists
            doc["totalReviews"] = doc.get("totalReviews", doc.get("reviewCount", 0))
            result.append(doc)

        return jsonify({"doctors": result}), 200
    except Exception:
        # Fallback: get from users collection
        query = {"role": "doctor"}
        if specialization:
            query["specialization"] = {"$regex": specialization, "$options": "i"}
        doctors = list(users_collection.find(query, {"password": 0}))
        for d in doctors:
            d["_id"] = str(d["_id"])
        return jsonify({"doctors": doctors}), 200


def get_doctor_by_id(doctor_id):
    """Get single doctor details."""
    try:
        # Try doctors_collection first
        doctor = doctors_collection.find_one({"_id": doctor_id})
        if doctor:
            user = users_collection.find_one({"_id": doctor["userId"]})
            doctor["_id"] = str(doctor["_id"])
            if user:
                doctor["fullName"] = user.get("fullName", "")
                doctor["email"] = user.get("email", "")
                doctor["phone"] = user.get("phone", "")
        else:
            # Fallback: try users collection
            doctor = users_collection.find_one({"_id": doctor_id, "role": "doctor"})
            if not doctor:
                return jsonify({"error": "Doctor not found"}), 404
            doctor["_id"] = str(doctor["_id"])
            doctor.pop("password", None)

        # Get reviews
        reviews = list(reviews_collection.find({"doctorId": doctor_id}))
        doctor["reviews"] = format_docs(reviews)
        if reviews:
            avg = sum(r.get("rating", 0) for r in reviews) / len(reviews)
            doctor["rating"] = round(avg, 1)

        return jsonify({"doctor": doctor}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def update_doctor_profile(current_user):
    """Doctor updates their own profile."""
    data = request.get_json()
    user_id = current_user["_id"]

    update_fields = {}
    allowed = [
        "specialization", "qualification", "experienceYears",
        "consultationFee", "bio", "availability", "slotDurationMinutes"
    ]

    for field in allowed:
        if field in data:
            update_fields[field] = data[field]

    if not update_fields:
        return jsonify({"error": "No fields to update"}), 400

    update_fields["updatedAt"] = datetime.utcnow()

    doctors_collection.update_one(
        {"userId": user_id},
        {"$set": update_fields}
    )

    return jsonify({"message": "Profile updated successfully"}), 200


def update_doctor_schedule(current_user):
    """Doctor updates their weekly schedule."""
    data = request.get_json()
    schedule = data.get("schedule", [])
    user_id = current_user["_id"]

    # Build availability dict from schedule list
    availability = {}
    for slot in schedule:
        day = slot.get("day", "").lower()
        availability[day] = {
            "active": slot.get("isAvailable", False),
            "start": slot.get("startTime", "09:00"),
            "end": slot.get("endTime", "17:00")
        }

    doctors_collection.update_one(
        {"userId": user_id},
        {"$set": {"availability": availability, "updatedAt": datetime.utcnow()}},
        upsert=True
    )

    # Also update users collection schedule field
    users_collection.update_one(
        {"_id": user_id, "role": "doctor"},
        {"$set": {"schedule": schedule}}
    )

    return jsonify({"message": "Schedule updated successfully"}), 200


def get_doctor_slots(doctor_id):
    """Get available time slots for a doctor on a specific date."""
    date = request.args.get("date")
    if not date:
        return jsonify({"error": "Date parameter is required"}), 400

    # Try finding by doctors collection _id first, then by userId
    doctor = doctors_collection.find_one({"_id": doctor_id})

    if not doctor:
        doctor = doctors_collection.find_one({"userId": doctor_id})

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Date format must be YYYY-MM-DD"}), 400

    day_name = date_obj.strftime("%A").lower()
    availability = doctor.get("availability", {})
    day_schedule = availability.get(day_name)

    if not day_schedule or not day_schedule.get("active"):
        return jsonify({"availableSlots": [], "bookedSlots": [], "message": "Doctor not available on this day"}), 200

    slot_duration = doctor.get("slotDurationMinutes", 15)
    all_slots = generate_time_slots(
        day_schedule["start"], day_schedule["end"], slot_duration
    )

    # Check booked slots using BOTH doctor _id and userId
    doc_id_str = str(doctor["_id"])
    user_id_str = str(doctor.get("userId", ""))
    booked = appointments_collection.find({
        "$or": [{"doctorId": doc_id_str}, {"doctorId": user_id_str}],
        "date": date,
        "status": {"$in": ["pending", "approved"]}
    })
    booked_times = {appt["timeSlot"] for appt in booked}
    available_slots = [s for s in all_slots if s not in booked_times]

    return jsonify({
        "date": date,
        "day": day_name,
        "allSlots": all_slots,
        "bookedSlots": list(booked_times),
        "availableSlots": available_slots
    }), 200


def get_doctor_schedule(current_user):
    """Get doctor's own availability schedule."""
    doctor = doctors_collection.find_one({"userId": current_user["_id"]})
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    return jsonify({
        "availability": doctor.get("availability", {}),
        "slotDurationMinutes": doctor.get("slotDurationMinutes", 15)
    }), 200


def add_doctor_review(current_user, doctor_id):
    """Patient adds a review for a doctor."""
    data = request.get_json()
    rating = data.get("rating")
    comment = data.get("comment", "")

    if not rating or not (1 <= int(rating) <= 5):
        return jsonify({"error": "Rating must be between 1 and 5"}), 400

    review = {
        "doctorId": doctor_id,
        "patientId": current_user["_id"],
        "patientName": current_user.get("fullName", "Anonymous"),
        "rating": int(rating),
        "comment": comment,
        "createdAt": datetime.utcnow()
    }

    reviews_collection.insert_one(review)

    # Update doctor's average rating
    all_reviews = list(reviews_collection.find({"doctorId": doctor_id}))
    if all_reviews:
        avg = sum(r.get("rating", 0) for r in all_reviews) / len(all_reviews)
        doctors_collection.update_one(
            {"_id": doctor_id},
            {"$set": {"avgRating": round(avg, 1), "reviewCount": len(all_reviews)}}
        )

    return jsonify({"message": "Review added successfully"}), 201
