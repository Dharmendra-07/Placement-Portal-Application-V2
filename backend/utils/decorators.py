from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from models.models import Role


def role_required(*roles):
    """Decorator: allow access only to users with one of the given roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in roles:
                return jsonify({"message": "Access denied: insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    return role_required(Role.ADMIN)(fn)


def company_required(fn):
    return role_required(Role.COMPANY)(fn)


def student_required(fn):
    return role_required(Role.STUDENT)(fn)


def admin_or_company_required(fn):
    return role_required(Role.ADMIN, Role.COMPANY)(fn)


def not_blacklisted(fn):
    """Decorator: block blacklisted users from accessing the endpoint."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("is_blacklisted"):
            return jsonify({"message": "Your account has been blacklisted."}), 403
        return fn(*args, **kwargs)
    return wrapper
