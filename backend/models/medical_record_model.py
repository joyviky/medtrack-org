from datetime import datetime


def medical_record_schema(patient_id, record_type, title, description="",
                          file_path="", doctor_id=None):
    """
    record_type: 'blood_test', 'prescription', 'scan', 'consultation', 'report'
    """
    return {
        "patientId": patient_id,
        "doctorId": doctor_id,
        "recordType": record_type,
        "title": title,
        "description": description,
        "filePath": file_path,
        "createdAt": datetime.utcnow()
    }
