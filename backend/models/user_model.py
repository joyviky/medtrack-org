from datetime import datetime


def user_schema(email, password_hash, role, full_name, phone=""):
    """
    role: 'patient', 'doctor', 'admin'
    """
    return {
        "email": email,
        "password": password_hash,
        "role": role,
        "fullName": full_name,
        "phone": phone,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
