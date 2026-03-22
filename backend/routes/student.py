from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import os
from app import db
from models.models import (Student, PlacementDrive, Application, Placement,
                            DriveStatus, ApplicationStatus)
from utils.decorators import student_required, not_blacklisted

student_bp = Blueprint("student", __name__)


def get_student_or_404():
    user_id = int(get_jwt_identity())
    return Student.query.filter_by(user_id=user_id).first_or_404()


def check_eligibility(student, drive):
    """Return (eligible: bool, reason: str)."""
    if drive.min_cgpa and student.cgpa < drive.min_cgpa:
        return False, f"Minimum CGPA required: {drive.min_cgpa}"
    if drive.eligible_branches:
        branches = [b.strip().lower() for b in drive.eligible_branches.split(",")]
        if student.department and student.department.lower() not in branches:
            return False, f"Your branch is not eligible. Eligible: {drive.eligible_branches}"
    if drive.eligible_years:
        years = [int(y.strip()) for y in drive.eligible_years.split(",")]
        if student.year and student.year not in years:
            return False, f"Your year is not eligible. Eligible years: {drive.eligible_years}"
    return True, "Eligible"


# ─── Dashboard ────────────────────────────────────────────────────────────────

@student_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@student_required
def dashboard():
    student = get_student_or_404()

    # All approved drives
    approved_drives = PlacementDrive.query.filter_by(status=DriveStatus.APPROVED).all()

    # Student's applications
    apps = Application.query.filter_by(student_id=student.id).all()
    applied_drive_ids = {a.drive_id for a in apps}

    drives_with_eligibility = []
    for drive in approved_drives:
        d = drive.to_dict()
        eligible, reason = check_eligibility(student, drive)
        d["eligible"]        = eligible
        d["eligibility_note"]= reason
        d["already_applied"] = drive.id in applied_drive_ids
        drives_with_eligibility.append(d)

    return jsonify({
        "student":       student.to_dict(),
        "drives":        drives_with_eligibility,
        "applications":  [a.to_dict() for a in apps],
        "placements":    [p.to_dict() for p in student.placements],
    }), 200


# ─── Student profile ──────────────────────────────────────────────────────────

@student_bp.route("/profile", methods=["GET"])
@jwt_required()
@student_required
def get_profile():
    student = get_student_or_404()
    return jsonify(student.to_dict()), 200


@student_bp.route("/profile", methods=["PUT"])
@jwt_required()
@student_required
@not_blacklisted
def update_profile():
    student = get_student_or_404()
    data    = request.get_json()

    updatable = ["full_name", "phone", "department", "year", "cgpa",
                 "skills", "about", "address", "gender"]
    for f in updatable:
        if f in data:
            setattr(student, f, data[f])

    if "dob" in data and data["dob"]:
        student.dob = datetime.strptime(data["dob"], "%Y-%m-%d").date()

    db.session.commit()
    return jsonify({"message": "Profile updated", "student": student.to_dict()}), 200


# ─── Resume upload ────────────────────────────────────────────────────────────

@student_bp.route("/resume", methods=["POST"])
@jwt_required()
@student_required
@not_blacklisted
def upload_resume():
    student = get_student_or_404()

    if "resume" not in request.files:
        return jsonify({"message": "No file uploaded"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"message": "No file selected"}), 400

    allowed = {".pdf", ".doc", ".docx"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        return jsonify({"message": "Only PDF and DOC files are allowed"}), 400

    filename = f"resume_student_{student.id}{ext}"
    path     = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    student.resume_url = f"/uploads/{filename}"
    db.session.commit()

    return jsonify({"message": "Resume uploaded", "resume_url": student.resume_url}), 200


# ─── Drives listing ──────────────────────────────────────────────────────────

@student_bp.route("/drives", methods=["GET"])
@jwt_required()
@student_required
def list_drives():
    student = get_student_or_404()
    q       = request.args.get("q", "")
    query   = PlacementDrive.query.filter_by(status=DriveStatus.APPROVED)

    if q:
        query = query.filter(
            PlacementDrive.job_title.ilike(f"%{q}%") |
            PlacementDrive.skills_required.ilike(f"%{q}%")
        )

    drives = query.order_by(PlacementDrive.created_at.desc()).all()
    applied_ids = {a.drive_id for a in student.applications}

    result = []
    for drive in drives:
        d = drive.to_dict()
        eligible, reason = check_eligibility(student, drive)
        d["eligible"]        = eligible
        d["eligibility_note"]= reason
        d["already_applied"] = drive.id in applied_ids
        result.append(d)

    return jsonify(result), 200


# ─── Apply for drive ──────────────────────────────────────────────────────────

@student_bp.route("/drives/<int:drive_id>/apply", methods=["POST"])
@jwt_required()
@student_required
@not_blacklisted
def apply_for_drive(drive_id):
    student = get_student_or_404()
    drive   = PlacementDrive.query.get_or_404(drive_id)

    if drive.status != DriveStatus.APPROVED:
        return jsonify({"message": "Drive is not open for applications"}), 400

    # Check deadline
    if drive.application_deadline and datetime.utcnow() > drive.application_deadline:
        return jsonify({"message": "Application deadline has passed"}), 400

    # Prevent duplicate application
    existing = Application.query.filter_by(student_id=student.id, drive_id=drive_id).first()
    if existing:
        return jsonify({"message": "You have already applied to this drive"}), 409

    # Eligibility check
    eligible, reason = check_eligibility(student, drive)
    if not eligible:
        return jsonify({"message": f"Not eligible: {reason}"}), 403

    app = Application(
        student_id = student.id,
        drive_id   = drive_id,
        status     = ApplicationStatus.APPLIED,
    )
    db.session.add(app)
    db.session.commit()

    return jsonify({"message": "Application submitted successfully",
                    "application": app.to_dict()}), 201


# ─── Application history ──────────────────────────────────────────────────────

@student_bp.route("/applications", methods=["GET"])
@jwt_required()
@student_required
def get_applications():
    student = get_student_or_404()
    apps    = Application.query.filter_by(student_id=student.id)\
                               .order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict() for a in apps]), 200


# ─── Placement history ────────────────────────────────────────────────────────

@student_bp.route("/placements", methods=["GET"])
@jwt_required()
@student_required
def get_placements():
    student    = get_student_or_404()
    placements = Placement.query.filter_by(student_id=student.id).all()
    return jsonify([p.to_dict() for p in placements]), 200
