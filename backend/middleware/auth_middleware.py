import jwt
import os
from functools import wraps
from flask import request, jsonify
from backend.config.db import users_collection
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "medtrack-secret")


def token_required(f):
    """Decorator to protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = users_collection.find_one(
                {"_id": data["userId"]}
            )
            if not current_user:
                return jsonify({"error": "User not found"}), 401
            current_user["_id"] = str(current_user["_id"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(current_user, *args, **kwargs)

    return decorated


def role_required(*roles):
    """Decorator to restrict routes to specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if current_user.get("role") not in roles:
                return jsonify({"error": "Access denied. Insufficient permissions."}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator
