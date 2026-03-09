import jwt
import os
import bcrypt
from datetime import datetime, timedelta
from flask import request, jsonify
from dotenv import load_dotenv

from backend.config.db import (
    users_collection, doctors_collection, patients_collection
)
from backend.models.user_model import user_schema
from backend.models.doctor_model import doctor_schema
from backend.models.patient_model import patient_schema
from backend.utils.helpers import format_user

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "medtrack-secret")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION_HOURS", 24))


def register():
    """Register a new user (patient or doctor)."""
    data = request.get_json()

    required = ["email", "password", "fullName", "role"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"'{field}' is required"}), 400

    if data["role"] not in ["patient", "doctor"]:
        return jsonify({"error": "Role must be 'patient' or 'doctor'"}), 400

    # Check if user already exists
    if users_collection.find_one({"email": data["email"]}):
        return jsonify({"error": "Email already registered"}), 409

    # Hash password
    hashed = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt())

    user = user_schema(
        email=data["email"],
        password_hash=hashed.decode("utf-8"),
        role=data["role"],
        full_name=data["fullName"],
        phone=data.get("phone", "")
    )

    result = users_collection.insert_one(user)
    user_id = str(result.inserted_id)

    # Create role-specific profile
    if data["role"] == "doctor":
        doctor = doctor_schema(
            user_id=user_id,
            specialization=data.get("specialization", "General Physician"),
            qualification=data.get("qualification", ""),
            experience_years=data.get("experienceYears", 0),
            consultation_fee=data.get("consultationFee", 500),
            bio=data.get("bio", "")
        )
        doctors_collection.insert_one(doctor)
    else:
        patient = patient_schema(
            user_id=user_id,
            date_of_birth=data.get("dateOfBirth", ""),
            gender=data.get("gender", ""),
            blood_group=data.get("bloodGroup", ""),
            address=data.get("address", "")
        )
        patients_collection.insert_one(patient)

    # Generate token
    token = jwt.encode(
        {
            "userId": user_id,
            "role": data["role"],
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": {
            "id": user_id,
            "email": data["email"],
            "fullName": data["fullName"],
            "role": data["role"]
        }
    }), 201


def login():
    """Authenticate user and return JWT."""
    data = request.get_json()

    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password are required"}), 400

    user = users_collection.find_one({"email": data["email"]})
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not bcrypt.checkpw(data["password"].encode("utf-8"),
                          user["password"].encode("utf-8")):
        return jsonify({"error": "Invalid email or password"}), 401

    user_id = str(user["_id"])

    token = jwt.encode(
        {
            "userId": user_id,
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    # Get profile info
    profile = None
    if user["role"] == "doctor":
        doc = doctors_collection.find_one({"userId": user_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            profile = doc
    elif user["role"] == "patient":
        pat = patients_collection.find_one({"userId": user_id})
        if pat:
            pat["_id"] = str(pat["_id"])
            profile = pat

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user_id,
            "email": user["email"],
            "fullName": user["fullName"],
            "role": user["role"],
            "profile": profile
        }
    }), 200


def get_profile(current_user):
    """Get current user's profile."""
    user_id = current_user["_id"]
    role = current_user["role"]

    profile = None
    if role == "doctor":
        profile = doctors_collection.find_one({"userId": user_id})
    elif role == "patient":
        profile = patients_collection.find_one({"userId": user_id})

    if profile:
        profile["_id"] = str(profile["_id"])

    return jsonify({
        "user": format_user(current_user),
        "profile": profile
    }), 200
