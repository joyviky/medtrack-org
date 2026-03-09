from datetime import datetime


def review_schema(patient_id, doctor_id, rating, comment=""):
    """Rating 1-5 with optional comment."""
    return {
        "patientId": patient_id,
        "doctorId": doctor_id,
        "rating": max(1, min(5, rating)),
        "comment": comment,
        "createdAt": datetime.utcnow()
    }
