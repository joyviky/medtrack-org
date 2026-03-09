from datetime import datetime


def notification_schema(user_id, message, notif_type="info"):
    """
    notif_type: 'info', 'appointment', 'prescription', 'alert', 'emergency'
    """
    return {
        "userId": user_id,
        "message": message,
        "type": notif_type,
        "readStatus": False,
        "createdAt": datetime.utcnow()
    }
