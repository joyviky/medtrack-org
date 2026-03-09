from flask import Blueprint
from backend.controllers.appointment_controller import (
    book_appointment, get_patient_appointments, get_doctor_appointments,
    update_appointment_status, get_appointment_details, emergency_booking,
    add_review
)
from backend.middleware.auth_middleware import token_required, role_required

appointment_bp = Blueprint("appointment", __name__)

appointment_bp.route("/book", methods=["POST"])(
    token_required(role_required("patient")(book_appointment))
)
appointment_bp.route("/patient", methods=["GET"])(
    token_required(role_required("patient")(get_patient_appointments))
)
appointment_bp.route("/doctor", methods=["GET"])(
    token_required(role_required("doctor")(get_doctor_appointments))
)
appointment_bp.route("/status", methods=["PUT"])(
    token_required(role_required("doctor")(update_appointment_status))
)
appointment_bp.route("/<appointment_id>", methods=["GET"])(
    token_required(get_appointment_details)
)
appointment_bp.route("/emergency", methods=["POST"])(
    token_required(role_required("patient")(emergency_booking))
)
appointment_bp.route("/review", methods=["POST"])(
    token_required(role_required("patient")(add_review))
)
