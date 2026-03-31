from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app import db
from models.models import User, Company, Student, Role, ApprovalStatus
from utils.validators import validate, rules

auth_bp = Blueprint("auth", __name__)


# ─── Helper ───────────────────────────────────────────────────────────────────

def make_token(user):
    """Create a JWT with role claims embedded."""
    additional_claims = {
        "role":           user.role,
        "is_blacklisted": user.is_blacklisted,
        "is_active":      user.is_active,
    }
    return create_access_token(identity=str(user.id),
                               additional_claims=additional_claims)


# ─── Login (all roles) ────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"message": "Account is deactivated. Contact admin."}), 403

    if user.is_blacklisted:
        return jsonify({"message": "Account is blacklisted. Contact admin."}), 403

    # For company: check approval status
    if user.role == Role.COMPANY:
        company = Company.query.filter_by(user_id=user.id).first()
        if company and company.approval_status != ApprovalStatus.APPROVED:
            return jsonify({
                "message": "Your company registration is pending admin approval.",
                "approval_status": company.approval_status
            }), 403

    token = make_token(user)

    # Build profile snapshot for frontend
    profile = {}
    if user.role == Role.COMPANY:
        c = Company.query.filter_by(user_id=user.id).first()
        profile = c.to_dict() if c else {}
    elif user.role == Role.STUDENT:
        s = Student.query.filter_by(user_id=user.id).first()
        profile = s.to_dict() if s else {}

    return jsonify({
        "access_token": token,
        "role":         user.role,
        "user_id":      user.id,
        "profile":      profile,
        "message":      "Login successful"
    }), 200


# ─── Student Registration ─────────────────────────────────────────────────────

@auth_bp.route("/register/student", methods=["POST"])
def register_student():
    data = request.get_json()

    errors = validate(data, {
        "full_name": [rules.required, rules.min_length(2)],
        "email":     [rules.required, rules.email],
        "password":  [rules.required, rules.min_length(6)],
        "phone":     [rules.phone],
        "cgpa":      [rules.cgpa],
    })
    if errors:
        return jsonify({"message": "Validation failed", "errors": errors}), 422

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 409

    # Create user
    user = User(email=email, role=Role.STUDENT)
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()  # get user.id without committing

    # Create student profile
    student = Student(
        user_id    = user.id,
        full_name  = data["full_name"].strip(),
        roll_number= data.get("roll_number"),
        department = data.get("department"),
        year       = data.get("year"),
        cgpa       = float(data.get("cgpa", 0.0)),
        phone      = data.get("phone"),
        skills     = data.get("skills"),
    )
    db.session.add(student)
    db.session.commit()

    token = make_token(user)
    return jsonify({
        "access_token": token,
        "role":         user.role,
        "user_id":      user.id,
        "profile":      student.to_dict(),
        "message":      "Student registered successfully"
    }), 201


# ─── Company Registration ─────────────────────────────────────────────────────

@auth_bp.route("/register/company", methods=["POST"])
def register_company():
    data = request.get_json()

    errors = validate(data, {
        "name":             [rules.required, rules.min_length(2)],
        "email":            [rules.required, rules.email],
        "password":         [rules.required, rules.min_length(6)],
        "website":          [rules.url],
        "hr_contact_phone": [rules.phone],
    })
    if errors:
        return jsonify({"message": "Validation failed", "errors": errors}), 422

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 409

    # Create user
    user = User(email=email, role=Role.COMPANY)
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()

    # Create company profile (approval pending)
    company = Company(
        user_id         = user.id,
        name            = data["name"].strip(),
        industry        = data.get("industry"),
        location        = data.get("location"),
        website         = data.get("website"),
        hr_contact_name = data.get("hr_contact_name"),
        hr_contact_phone= data.get("hr_contact_phone"),
        description     = data.get("description"),
        approval_status = ApprovalStatus.PENDING,
    )
    db.session.add(company)
    db.session.commit()

    return jsonify({
        "message":         "Company registered. Awaiting admin approval.",
        "approval_status": ApprovalStatus.PENDING,
        "company_id":      company.id,
    }), 201


# ─── Get current user info ────────────────────────────────────────────────────

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = int(get_jwt_identity())
    user    = User.query.get_or_404(user_id)

    profile = {}
    if user.role == Role.COMPANY:
        c = Company.query.filter_by(user_id=user.id).first()
        profile = c.to_dict() if c else {}
    elif user.role == Role.STUDENT:
        s = Student.query.filter_by(user_id=user.id).first()
        profile = s.to_dict() if s else {}

    return jsonify({
        "user":    user.to_dict(),
        "role":    user.role,
        "profile": profile,
    }), 200


# ─── Change password ──────────────────────────────────────────────────────────

@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    user    = User.query.get_or_404(user_id)
    data    = request.get_json()

    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"message": "Both old and new passwords are required"}), 400

    if not user.check_password(old_password):
        return jsonify({"message": "Current password is incorrect"}), 401

    if len(new_password) < 6:
        return jsonify({"message": "New password must be at least 6 characters"}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password changed successfully"}), 200
