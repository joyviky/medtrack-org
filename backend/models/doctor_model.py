from datetime import datetime


def doctor_schema(user_id, specialization, qualification, experience_years,
                  consultation_fee, availability=None, bio=""):
    """Doctor profile linked to a user document."""
    if availability is None:
        availability = {
            "monday": {"start": "09:00", "end": "17:00", "active": True},
            "tuesday": {"start": "09:00", "end": "17:00", "active": True},
            "wednesday": {"start": "09:00", "end": "17:00", "active": True},
            "thursday": {"start": "09:00", "end": "17:00", "active": True},
            "friday": {"start": "09:00", "end": "17:00", "active": True},
            "saturday": {"start": "09:00", "end": "13:00", "active": True},
            "sunday": {"start": "", "end": "", "active": False},
        }
    return {
        "userId": user_id,
        "specialization": specialization,
        "qualification": qualification,
        "experienceYears": experience_years,
        "consultationFee": consultation_fee,
        "availability": availability,
        "bio": bio,
        "avgRating": 0,
        "totalReviews": 0,
        "isApproved": False,
        "slotDurationMinutes": 15,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
