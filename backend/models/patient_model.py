from datetime import datetime


def patient_schema(user_id, date_of_birth="", gender="", blood_group="",
                   address="", emergency_contact="", allergies=None,
                   conditions=None):
    """Patient profile linked to a user document."""
    return {
        "userId": user_id,
        "dateOfBirth": date_of_birth,
        "gender": gender,
        "bloodGroup": blood_group,
        "address": address,
        "emergencyContact": emergency_contact,
        "allergies": allergies or [],
        "conditions": conditions or [],
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
