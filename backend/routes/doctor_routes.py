from flask import Blueprint
from backend.controllers.doctor_controller import (
    get_all_doctors, get_doctor_by_id, update_doctor_profile,
    get_doctor_slots, get_doctor_schedule, update_doctor_schedule,
    add_doctor_review
)
from backend.middleware.auth_middleware import token_required, role_required

doctor_bp = Blueprint("doctor", __name__)

doctor_bp.route("/", methods=["GET"])(get_all_doctors)
doctor_bp.route("/<doctor_id>", methods=["GET"])(get_doctor_by_id)
doctor_bp.route("/<doctor_id>/slots", methods=["GET"])(get_doctor_slots)
doctor_bp.route("/<doctor_id>/review", methods=["POST"])(
    token_required(role_required("patient")(add_doctor_review))
)

doctor_bp.route("/profile/update", methods=["PUT"])(
    token_required(role_required("doctor")(update_doctor_profile))
)
doctor_bp.route("/schedule", methods=["GET"])(
    token_required(role_required("doctor")(get_doctor_schedule))
)
doctor_bp.route("/schedule", methods=["PUT"])(
    token_required(role_required("doctor")(update_doctor_schedule))
)
