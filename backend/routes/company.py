from flask import Blueprint, request, jsonify, current_app
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import os
from app import db
from models.models import (Company, PlacementDrive, Application, Placement, User,
                            ApprovalStatus, DriveStatus, ApplicationStatus)
from utils.decorators import company_required, not_blacklisted
from utils.cache import cached_response, invalidate, TTL

company_bp = Blueprint("company", __name__)


# ─── Helper ───────────────────────────────────────────────────────────────────

def get_approved_company():
    user_id = int(get_jwt_identity())
    company = Company.query.filter_by(user_id=user_id).first()
    if not company:
        return None, (jsonify({"message": "Company profile not found"}), 404)
    if company.approval_status != ApprovalStatus.APPROVED:
        return None, (jsonify({
            "message": "Company not yet approved by admin.",
            "approval_status": company.approval_status
        }), 403)
    user = User.query.get(user_id)
    if user and user.is_blacklisted:
        return None, (jsonify({"message": "Company account is blacklisted"}), 403)
    return company, None


# ══════════════════════════════════════════════════════════════════════════════
# PROFILE
# ══════════════════════════════════════════════════════════════════════════════

@company_bp.route("/profile", methods=["GET"])
@jwt_required()
@company_required
def get_profile():
    user_id = int(get_jwt_identity())
    company = Company.query.filter_by(user_id=user_id).first_or_404()
    return jsonify(company.to_dict()), 200


@company_bp.route("/profile", methods=["PUT"])
@jwt_required()
@company_required
@not_blacklisted
def update_profile():
    user_id = int(get_jwt_identity())
    company = Company.query.filter_by(user_id=user_id).first_or_404()
    data    = request.get_json()
    for field in ["name", "industry", "location", "website",
                  "hr_contact_name", "hr_contact_phone", "description"]:
        if field in data:
            setattr(company, field, data[field])
    db.session.commit()
    return jsonify({"message": "Profile updated", "company": company.to_dict()}), 200


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@company_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@company_required
@cached_response("company:dashboard", ttl=TTL["short"], vary_on_query=False)
def dashboard():
    company, err = get_approved_company()
    if err:
        return err

    all_drives = PlacementDrive.query.filter_by(company_id=company.id).all()

    active_drives  = [d for d in all_drives if d.status == DriveStatus.APPROVED]
    closed_drives  = [d for d in all_drives if d.status == DriveStatus.CLOSED]
    pending_drives = [d for d in all_drives if d.status == DriveStatus.PENDING]

    # Aggregate application counts across all drives
    total_applications = sum(len(d.applications) for d in all_drives)
    shortlisted = sum(
        sum(1 for a in d.applications if a.status == ApplicationStatus.SHORTLISTED)
        for d in all_drives
    )
    selected = sum(
        sum(1 for a in d.applications if a.status == ApplicationStatus.SELECTED)
        for d in all_drives
    )

    # Recent 5 applications across all drives
    all_app_ids = [a.id for d in all_drives for a in d.applications]
    recent_apps = (Application.query
                   .filter(Application.id.in_(all_app_ids))
                   .order_by(Application.applied_at.desc())
                   .limit(5).all()) if all_app_ids else []

    return jsonify({
        "company":            company.to_dict(),
        "active_drives":      [d.to_dict() for d in active_drives],
        "closed_drives":      [d.to_dict() for d in closed_drives],
        "pending_drives":     [d.to_dict() for d in pending_drives],
        "stats": {
            "total_drives":       len(all_drives),
            "active_drives":      len(active_drives),
            "closed_drives":      len(closed_drives),
            "pending_drives":     len(pending_drives),
            "total_applications": total_applications,
            "shortlisted":        shortlisted,
            "selected":           selected,
        },
        "recent_applications": [a.to_dict() for a in recent_apps],
    }), 200


# ══════════════════════════════════════════════════════════════════════════════
# PLACEMENT DRIVES  (Job Postings)
# ══════════════════════════════════════════════════════════════════════════════

@company_bp.route("/drives", methods=["GET"])
@jwt_required()
@company_required
@cached_response("company:drives", ttl=TTL["medium"], vary_on_query=True)
def list_drives():
    company, err = get_approved_company()
    if err:
        return err

    status = request.args.get("status")   # filter by drive status
    query  = PlacementDrive.query.filter_by(company_id=company.id)
    if status:
        query = query.filter_by(status=status)
    drives = query.order_by(PlacementDrive.created_at.desc()).all()
    return jsonify([d.to_dict() for d in drives]), 200


@company_bp.route("/drives/<int:drive_id>", methods=["GET"])
@jwt_required()
@company_required
def get_drive(drive_id):
    company, err = get_approved_company()
    if err:
        return err
    drive = PlacementDrive.query.filter_by(
        id=drive_id, company_id=company.id).first_or_404()
    data = drive.to_dict()
    data["applications"] = [a.to_dict() for a in drive.applications]
    return jsonify(data), 200


@company_bp.route("/drives", methods=["POST"])
@jwt_required()
@company_required
@not_blacklisted
def create_drive():
    company, err = get_approved_company()
    if err:
        return err

    data = request.get_json()
    if not data.get("job_title"):
        return jsonify({"message": "'job_title' is required"}), 400

    deadline   = None
    drive_date = None
    if data.get("application_deadline"):
        deadline = datetime.fromisoformat(data["application_deadline"])
    if data.get("drive_date"):
        drive_date = datetime.fromisoformat(data["drive_date"])

    drive = PlacementDrive(
        company_id           = company.id,
        job_title            = data["job_title"].strip(),
        job_description      = data.get("job_description"),
        skills_required      = data.get("skills_required"),
        salary_min           = data.get("salary_min"),
        salary_max           = data.get("salary_max"),
        location             = data.get("location"),
        job_type             = data.get("job_type", "Full-time"),
        eligible_branches    = data.get("eligible_branches"),
        min_cgpa             = float(data.get("min_cgpa", 0.0)),
        eligible_years       = data.get("eligible_years"),
        application_deadline = deadline,
        drive_date           = drive_date,
        status               = DriveStatus.PENDING,
    )
    db.session.add(drive)
    db.session.commit()
    invalidate("company:drives:*", "company:dashboard:*", "admin:drives:*")
    return jsonify({
        "message": "Drive submitted for admin approval",
        "drive":   drive.to_dict()
    }), 201


@company_bp.route("/drives/<int:drive_id>", methods=["PUT"])
@jwt_required()
@company_required
@not_blacklisted
def update_drive(drive_id):
    company, err = get_approved_company()
    if err:
        return err
    drive = PlacementDrive.query.filter_by(
        id=drive_id, company_id=company.id).first_or_404()
    data  = request.get_json()

    updatable = ["job_title", "job_description", "skills_required",
                 "salary_min", "salary_max", "location", "job_type",
                 "eligible_branches", "min_cgpa", "eligible_years"]
    for f in updatable:
        if f in data:
            setattr(drive, f, data[f])
    if "application_deadline" in data and data["application_deadline"]:
        drive.application_deadline = datetime.fromisoformat(data["application_deadline"])
    if "drive_date" in data and data["drive_date"]:
        drive.drive_date = datetime.fromisoformat(data["drive_date"])

    db.session.commit()
    invalidate("company:drives:*", "company:dashboard:*", "drives:approved:*")
    return jsonify({"message": "Drive updated", "drive": drive.to_dict()}), 200


@company_bp.route("/drives/<int:drive_id>/close", methods=["PUT"])
@jwt_required()
@company_required
def close_drive(drive_id):
    company, err = get_approved_company()
    if err:
        return err
    drive = PlacementDrive.query.filter_by(
        id=drive_id, company_id=company.id).first_or_404()
    drive.status = DriveStatus.CLOSED
    db.session.commit()
    invalidate("company:drives:*", "company:dashboard:*", "drives:approved:*", "admin:drives:*")
    return jsonify({"message": "Drive closed", "drive": drive.to_dict()}), 200


# ══════════════════════════════════════════════════════════════════════════════
# APPLICATIONS  (per drive)
# ══════════════════════════════════════════════════════════════════════════════

@company_bp.route("/drives/<int:drive_id>/applications", methods=["GET"])
@jwt_required()
@company_required
def get_drive_applications(drive_id):
    company, err = get_approved_company()
    if err:
        return err
    PlacementDrive.query.filter_by(
        id=drive_id, company_id=company.id).first_or_404()

    status = request.args.get("status")
    query  = Application.query.filter_by(drive_id=drive_id)
    if status:
        query = query.filter_by(status=status)
    apps = query.order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict() for a in apps]), 200


@company_bp.route("/applications/<int:app_id>", methods=["GET"])
@jwt_required()
@company_required
def get_application(app_id):
    company, err = get_approved_company()
    if err:
        return err
    app = Application.query.get_or_404(app_id)
    # Verify this app belongs to one of the company's drives
    drive = PlacementDrive.query.filter_by(
        id=app.drive_id, company_id=company.id).first()
    if not drive:
        return jsonify({"message": "Application not found"}), 404
    data = app.to_dict()
    # Include full student info for detailed view
    if app.student:
        data["student_detail"] = app.student.to_dict()
    return jsonify(data), 200


@company_bp.route("/applications/<int:app_id>/status", methods=["PUT"])
@jwt_required()
@company_required
def update_application_status(app_id):
    company, err = get_approved_company()
    if err:
        return err

    app  = Application.query.get_or_404(app_id)
    drive = PlacementDrive.query.filter_by(
        id=app.drive_id, company_id=company.id).first()
    if not drive:
        return jsonify({"message": "Application not found"}), 404

    data       = request.get_json()
    new_status = data.get("status")
    allowed    = [ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED,
                  ApplicationStatus.WAITING, ApplicationStatus.SELECTED,
                  ApplicationStatus.REJECTED]
    if new_status not in allowed:
        return jsonify({"message": f"Invalid status. Allowed: {allowed}"}), 400

    # Record status change in history log
    import json as _json
    try:
        history = _json.loads(app.status_history or "[]")
    except Exception:
        history = []
    history.append({
        "from":      app.status,
        "to":        new_status,
        "timestamp": datetime.utcnow().isoformat(),
        "remarks":   data.get("remarks", ""),
    })
    app.status         = new_status
    app.status_history = _json.dumps(history)
    if "remarks" in data:
        app.remarks = data["remarks"]
    if "interview_type" in data:
        app.interview_type = data["interview_type"]
    if data.get("interview_date"):
        app.interview_date = datetime.fromisoformat(data["interview_date"])

    # Auto-create Placement record on selection
    if new_status == ApplicationStatus.SELECTED:
        existing = Placement.query.filter_by(application_id=app.id).first()
        if not existing:
            placement = Placement(
                student_id     = app.student_id,
                company_id     = company.id,
                application_id = app.id,
                position       = drive.job_title,
                salary         = drive.salary_max,
            )
            db.session.add(placement)

    db.session.commit()
    invalidate("company:dashboard:*", "admin:dashboard")
    return jsonify({
        "message":     "Application updated",
        "application": app.to_dict()
    }), 200


# ──  Bulk status update for a drive  ─────────────────────────────────────────

@company_bp.route("/drives/<int:drive_id>/applications/bulk", methods=["PUT"])
@jwt_required()
@company_required
def bulk_update_applications(drive_id):
    company, err = get_approved_company()
    if err:
        return err
    PlacementDrive.query.filter_by(
        id=drive_id, company_id=company.id).first_or_404()

    data       = request.get_json()
    app_ids    = data.get("application_ids", [])
    new_status = data.get("status")
    remarks    = data.get("remarks", "")

    allowed = [ApplicationStatus.SHORTLISTED, ApplicationStatus.WAITING,
               ApplicationStatus.SELECTED, ApplicationStatus.REJECTED]
    if new_status not in allowed:
        return jsonify({"message": f"Invalid status. Allowed: {allowed}"}), 400

    updated = 0
    for app_id in app_ids:
        app = Application.query.filter_by(
            id=app_id, drive_id=drive_id).first()
        if app:
            app.status  = new_status
            app.remarks = remarks
            if new_status == ApplicationStatus.SELECTED:
                existing = Placement.query.filter_by(application_id=app.id).first()
                if not existing:
                    db.session.add(Placement(
                        student_id=app.student_id,
                        company_id=company.id,
                        application_id=app.id,
                        position=app.drive.job_title if app.drive else None,
                        salary=app.drive.salary_max if app.drive else None,
                    ))
            updated += 1

    db.session.commit()
    return jsonify({"message": f"{updated} applications updated to '{new_status}'"}), 200


# ══════════════════════════════════════════════════════════════════════════════
# INTERVIEW SCHEDULING
# ══════════════════════════════════════════════════════════════════════════════

@company_bp.route("/applications/<int:app_id>/schedule", methods=["PUT"])
@jwt_required()
@company_required
def schedule_interview(app_id):
    company, err = get_approved_company()
    if err:
        return err

    app = Application.query.get_or_404(app_id)
    drive = PlacementDrive.query.filter_by(
        id=app.drive_id, company_id=company.id).first()
    if not drive:
        return jsonify({"message": "Application not found"}), 404

    # Only shortlisted candidates can be scheduled
    if app.status not in [ApplicationStatus.SHORTLISTED, ApplicationStatus.WAITING]:
        return jsonify({
            "message": "Only shortlisted or waiting candidates can be scheduled for interview"
        }), 400

    data = request.get_json()
    if not data.get("interview_date"):
        return jsonify({"message": "'interview_date' is required"}), 400

    app.interview_date = datetime.fromisoformat(data["interview_date"])
    app.interview_type = data.get("interview_type", "In-person")
    app.remarks        = data.get("remarks", app.remarks)

    db.session.commit()
    return jsonify({
        "message":     "Interview scheduled",
        "application": app.to_dict()
    }), 200


# ══════════════════════════════════════════════════════════════════════════════
# PLACEMENT RECORDS (selected students)
# ══════════════════════════════════════════════════════════════════════════════

@company_bp.route("/placements", methods=["GET"])
@jwt_required()
@company_required
def list_placements():
    company, err = get_approved_company()
    if err:
        return err
    placements = Placement.query.filter_by(company_id=company.id).all()
    return jsonify([p.to_dict() for p in placements]), 200


@company_bp.route("/placements/<int:placement_id>", methods=["PUT"])
@jwt_required()
@company_required
def update_placement(placement_id):
    company, err = get_approved_company()
    if err:
        return err
    placement = Placement.query.filter_by(
        id=placement_id, company_id=company.id).first_or_404()
    data = request.get_json()
    for f in ["position", "salary", "offer_letter_url"]:
        if f in data:
            setattr(placement, f, data[f])
    if "joining_date" in data and data["joining_date"]:
        from datetime import date
        placement.joining_date = datetime.strptime(
            data["joining_date"], "%Y-%m-%d").date()
    db.session.commit()
    return jsonify({
        "message":   "Placement updated",
        "placement": placement.to_dict()
    }), 200


# ══════════════════════════════════════════════════════════════════════════════
# CROSS-ROLE: Company views student profile
# ══════════════════════════════════════════════════════════════════════════════

@company_bp.route("/students/<int:student_id>", methods=["GET"])
@jwt_required()
@company_required
def view_student_profile(student_id):
    """
    Company can view a student's profile only if that student
    has applied to one of their drives.
    """
    company, err = get_approved_company()
    if err:
        return err

    from models.models import Student, Application
    student = Student.query.get_or_404(student_id)

    # Verify the student applied to one of this company's drives
    drive_ids = [d.id for d in company.placement_drives]
    applied   = Application.query.filter(
        Application.student_id == student_id,
        Application.drive_id.in_(drive_ids)
    ).first() if drive_ids else None

    if not applied:
        return jsonify({"message": "Student has not applied to any of your drives"}), 403

    data = student.to_dict()
    # Include their application(s) to this company's drives only
    data["applications"] = [
        a.to_dict() for a in student.applications
        if a.drive_id in drive_ids
    ]
    return jsonify(data), 200
