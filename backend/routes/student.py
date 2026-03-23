from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import os
from app import db
from models.models import (User, Student, PlacementDrive, Application,
                            Placement, DriveStatus, ApplicationStatus)
from utils.decorators import student_required, not_blacklisted

student_bp = Blueprint("student", __name__)


# ─── Helper ───────────────────────────────────────────────────────────────────

def get_student():
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return None, (jsonify({"message": "Student profile not found"}), 404)
    user = User.query.get(user_id)
    if user and user.is_blacklisted:
        return None, (jsonify({"message": "Account is blacklisted. Contact admin."}), 403)
    return student, None


def check_eligibility(student, drive):
    """Return (eligible: bool, reason: str)."""
    if drive.min_cgpa and student.cgpa < drive.min_cgpa:
        return False, f"Min CGPA required: {drive.min_cgpa} (yours: {student.cgpa})"
    if drive.eligible_branches:
        branches = [b.strip().lower() for b in drive.eligible_branches.split(",")]
        if student.department and student.department.lower() not in branches:
            return False, f"Your branch is not eligible. Eligible: {drive.eligible_branches}"
    if drive.eligible_years:
        years = [int(y.strip()) for y in drive.eligible_years.split(",") if y.strip()]
        if student.year and student.year not in years:
            return False, f"Your year is not eligible. Eligible years: {drive.eligible_years}"
    return True, "Eligible"


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@student_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@student_required
def dashboard():
    student, err = get_student()
    if err:
        return err

    # All approved drives
    approved_drives = (PlacementDrive.query
                       .filter_by(status=DriveStatus.APPROVED)
                       .order_by(PlacementDrive.created_at.desc()).all())

    applied_ids = {a.drive_id for a in student.applications}

    drives_data = []
    for drive in approved_drives:
        d = drive.to_dict()
        eligible, reason = check_eligibility(student, drive)
        d["eligible"]         = eligible
        d["eligibility_note"] = reason
        d["already_applied"]  = drive.id in applied_ids
        drives_data.append(d)

    # Application stats
    apps = student.applications
    status_counts = {}
    for s in [ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED,
              ApplicationStatus.SELECTED, ApplicationStatus.REJECTED,
              ApplicationStatus.WAITING]:
        status_counts[s] = sum(1 for a in apps if a.status == s)

    # Upcoming interviews (scheduled)
    upcoming_interviews = [
        a.to_dict() for a in apps
        if a.interview_date and a.interview_date >= datetime.utcnow()
        and a.status in [ApplicationStatus.SHORTLISTED, ApplicationStatus.WAITING]
    ]

    return jsonify({
        "student":             student.to_dict(),
        "drives":              drives_data,
        "applications":        [a.to_dict() for a in
                                sorted(apps, key=lambda x: x.applied_at, reverse=True)],
        "placements":          [p.to_dict() for p in student.placements],
        "stats":               {
            "total_drives":     len(approved_drives),
            "total_applied":    len(apps),
            **status_counts,
        },
        "upcoming_interviews": upcoming_interviews,
    }), 200


# ══════════════════════════════════════════════════════════════════════════════
# PROFILE
# ══════════════════════════════════════════════════════════════════════════════

@student_bp.route("/profile", methods=["GET"])
@jwt_required()
@student_required
def get_profile():
    student, err = get_student()
    if err:
        return err
    return jsonify(student.to_dict()), 200


@student_bp.route("/profile", methods=["PUT"])
@jwt_required()
@student_required
@not_blacklisted
def update_profile():
    student, err = get_student()
    if err:
        return err
    data = request.get_json()

    updatable = ["full_name", "phone", "department", "year",
                 "cgpa", "skills", "about", "address", "gender"]
    for f in updatable:
        if f in data:
            setattr(student, f, data[f])
    if "dob" in data and data["dob"]:
        student.dob = datetime.strptime(data["dob"], "%Y-%m-%d").date()

    db.session.commit()
    return jsonify({"message": "Profile updated", "student": student.to_dict()}), 200


# ══════════════════════════════════════════════════════════════════════════════
# RESUME UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

@student_bp.route("/resume", methods=["POST"])
@jwt_required()
@student_required
@not_blacklisted
def upload_resume():
    student, err = get_student()
    if err:
        return err

    if "resume" not in request.files:
        return jsonify({"message": "No file part in request"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"message": "No file selected"}), 400

    allowed_ext = {".pdf", ".doc", ".docx"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_ext:
        return jsonify({"message": "Only PDF and DOC/DOCX files allowed"}), 400

    # Remove old resume if exists
    if student.resume_url:
        old_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            os.path.basename(student.resume_url))
        if os.path.exists(old_path):
            os.remove(old_path)

    filename = f"resume_student_{student.id}{ext}"
    path     = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    student.resume_url = f"/api/student/resume/{filename}"
    db.session.commit()
    return jsonify({
        "message":    "Resume uploaded successfully",
        "resume_url": student.resume_url
    }), 200


@student_bp.route("/resume/<filename>", methods=["GET"])
@jwt_required()
def serve_resume(filename):
    """Serve resume file — accessible by student, company, and admin."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, filename)


# ══════════════════════════════════════════════════════════════════════════════
# DRIVES — browse, search, filter
# ══════════════════════════════════════════════════════════════════════════════

@student_bp.route("/drives", methods=["GET"])
@jwt_required()
@student_required
def list_drives():
    student, err = get_student()
    if err:
        return err

    q        = request.args.get("q", "").strip()
    company  = request.args.get("company", "").strip()
    skills   = request.args.get("skills", "").strip()
    eligible_only = request.args.get("eligible_only", "false").lower() == "true"

    query = PlacementDrive.query.filter_by(status=DriveStatus.APPROVED)

    if q:
        query = query.filter(
            PlacementDrive.job_title.ilike(f"%{q}%") |
            PlacementDrive.job_description.ilike(f"%{q}%")
        )
    if skills:
        query = query.filter(
            PlacementDrive.skills_required.ilike(f"%{skills}%")
        )
    if company:
        from models.models import Company
        matched = Company.query.filter(
            Company.name.ilike(f"%{company}%")).all()
        ids = [c.id for c in matched]
        if ids:
            query = query.filter(PlacementDrive.company_id.in_(ids))
        else:
            return jsonify([]), 200

    drives = query.order_by(PlacementDrive.created_at.desc()).all()
    applied_ids = {a.drive_id for a in student.applications}

    result = []
    for drive in drives:
        d = drive.to_dict()
        el, reason = check_eligibility(student, drive)
        d["eligible"]         = el
        d["eligibility_note"] = reason
        d["already_applied"]  = drive.id in applied_ids
        if eligible_only and not el:
            continue
        result.append(d)

    return jsonify(result), 200


@student_bp.route("/drives/<int:drive_id>", methods=["GET"])
@jwt_required()
@student_required
def get_drive(drive_id):
    student, err = get_student()
    if err:
        return err

    drive = PlacementDrive.query.get_or_404(drive_id)
    d     = drive.to_dict()
    el, reason = check_eligibility(student, drive)
    d["eligible"]         = el
    d["eligibility_note"] = reason
    existing = Application.query.filter_by(
        student_id=student.id, drive_id=drive_id).first()
    d["already_applied"]  = existing is not None
    d["application"]      = existing.to_dict() if existing else None
    return jsonify(d), 200


# ══════════════════════════════════════════════════════════════════════════════
# APPLICATIONS — apply, view, track
# ══════════════════════════════════════════════════════════════════════════════

@student_bp.route("/drives/<int:drive_id>/apply", methods=["POST"])
@jwt_required()
@student_required
@not_blacklisted
def apply_for_drive(drive_id):
    student, err = get_student()
    if err:
        return err

    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.status != DriveStatus.APPROVED:
        return jsonify({"message": "This drive is not open for applications"}), 400

    if (drive.application_deadline and
            datetime.utcnow() > drive.application_deadline):
        return jsonify({"message": "Application deadline has passed"}), 400

    existing = Application.query.filter_by(
        student_id=student.id, drive_id=drive_id).first()
    if existing:
        return jsonify({"message": "You have already applied to this drive"}), 409

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
    return jsonify({
        "message":     "Application submitted successfully",
        "application": app.to_dict()
    }), 201


@student_bp.route("/applications", methods=["GET"])
@jwt_required()
@student_required
def get_applications():
    student, err = get_student()
    if err:
        return err

    status = request.args.get("status")
    query  = Application.query.filter_by(student_id=student.id)
    if status:
        query = query.filter_by(status=status)
    apps = query.order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict() for a in apps]), 200


@student_bp.route("/applications/<int:app_id>", methods=["GET"])
@jwt_required()
@student_required
def get_application_detail(app_id):
    student, err = get_student()
    if err:
        return err

    app = Application.query.filter_by(
        id=app_id, student_id=student.id).first_or_404()
    data = app.to_dict()
    # Include drive details for context
    if app.drive:
        data["drive_detail"] = app.drive.to_dict()
    if app.placement:
        data["placement"] = app.placement.to_dict()
    return jsonify(data), 200


# ══════════════════════════════════════════════════════════════════════════════
# INTERVIEWS
# ══════════════════════════════════════════════════════════════════════════════

@student_bp.route("/interviews", methods=["GET"])
@jwt_required()
@student_required
def get_interviews():
    """All applications that have an interview scheduled."""
    student, err = get_student()
    if err:
        return err

    apps = (Application.query
            .filter_by(student_id=student.id)
            .filter(Application.interview_date.isnot(None))
            .order_by(Application.interview_date.asc()).all())
    return jsonify([a.to_dict() for a in apps]), 200


# ══════════════════════════════════════════════════════════════════════════════
# PLACEMENTS  (offer letters & confirmations)
# ══════════════════════════════════════════════════════════════════════════════

@student_bp.route("/placements", methods=["GET"])
@jwt_required()
@student_required
def get_placements():
    student, err = get_student()
    if err:
        return err
    placements = Placement.query.filter_by(student_id=student.id).all()
    return jsonify([p.to_dict() for p in placements]), 200


@student_bp.route("/placements/<int:placement_id>", methods=["GET"])
@jwt_required()
@student_required
def get_placement_detail(placement_id):
    student, err = get_student()
    if err:
        return err
    placement = Placement.query.filter_by(
        id=placement_id, student_id=student.id).first_or_404()
    return jsonify(placement.to_dict()), 200
