from flask import Blueprint
from backend.controllers.auth_controller import register, login, get_profile
from backend.middleware.auth_middleware import token_required

auth_bp = Blueprint("auth", __name__)

auth_bp.route("/register", methods=["POST"])(register)
auth_bp.route("/login", methods=["POST"])(login)
auth_bp.route("/profile", methods=["GET"])(token_required(get_profile))
