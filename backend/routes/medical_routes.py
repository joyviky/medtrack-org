from flask import Blueprint
from backend.controllers.medical_controller import (
    upload_medical_record, get_medical_records, get_record_by_id
)
from backend.middleware.auth_middleware import token_required

medical_bp = Blueprint("medical", __name__)

medical_bp.route("/upload", methods=["POST"])(
    token_required(upload_medical_record)
)
medical_bp.route("/records", methods=["GET"])(
    token_required(get_medical_records)
)
medical_bp.route("/records/<record_id>", methods=["GET"])(
    token_required(get_record_by_id)
)
