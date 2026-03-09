from flask import Blueprint
from backend.controllers.patient_controller import (
    get_patient_profile, update_patient_profile, get_patient_by_id
)
from backend.middleware.auth_middleware import token_required, role_required

patient_bp = Blueprint("patient", __name__)

patient_bp.route("/profile", methods=["GET"])(
    token_required(role_required("patient")(get_patient_profile))
)
patient_bp.route("/profile/update", methods=["PUT"])(
    token_required(role_required("patient")(update_patient_profile))
)
patient_bp.route("/<patient_id>", methods=["GET"])(
    token_required(role_required("doctor", "admin")(get_patient_by_id))
)
