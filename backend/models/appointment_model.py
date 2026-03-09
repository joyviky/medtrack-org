from datetime import datetime


def appointment_schema(patient_id, doctor_id, date, time_slot,
                       reason="", is_emergency=False):
    """
    status lifecycle: pending → approved → completed → prescription_uploaded
    """
    return {
        "patientId": patient_id,
        "doctorId": doctor_id,
        "date": date,
        "timeSlot": time_slot,
        "reason": reason,
        "status": "pending",
        "isEmergency": is_emergency,
        "prescription": None,
        "notes": "",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
