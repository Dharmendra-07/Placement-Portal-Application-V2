from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.models import (User, Company, Student, PlacementDrive, Application,
                            Placement, Role, ApprovalStatus, DriveStatus, ApplicationStatus)
from utils.decorators import admin_required
from utils.cache import cached_response, invalidate, cache_stats, TTL

admin_bp = Blueprint("admin", __name__)


# ─── Dashboard stats ──────────────────────────────────────────────────────────

@admin_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@admin_required
def dashboard():
    # ← cached 60s — stats invalidated on any approval/rejection
    total_students        = Student.query.count()
    total_companies       = Company.query.filter_by(approval_status=ApprovalStatus.APPROVED).count()
    total_drives          = PlacementDrive.query.count()
    total_applications    = Application.query.count()
    pending_companies     = Company.query.filter_by(approval_status=ApprovalStatus.PENDING).count()
    pending_drives        = PlacementDrive.query.filter_by(status=DriveStatus.PENDING).count()
    total_selected        = Placement.query.count()
    blacklisted_companies = User.query.filter_by(role=Role.COMPANY, is_blacklisted=True).count()
    blacklisted_students  = User.query.filter_by(role=Role.STUDENT,  is_blacklisted=True).count()

    status_counts = {}
    for status in [ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED,
                   ApplicationStatus.SELECTED, ApplicationStatus.REJECTED,
                   ApplicationStatus.WAITING]:
        status_counts[status] = Application.query.filter_by(status=status).count()

    recent_apps = (Application.query
                   .order_by(Application.applied_at.desc())
                   .limit(5).all())

    pending_co = (Company.query
                  .filter_by(approval_status=ApprovalStatus.PENDING)
                  .order_by(Company.created_at.desc())
                  .limit(5).all())

    return jsonify({
        "total_students":            total_students,
        "total_companies":           total_companies,
        "total_drives":              total_drives,
        "total_applications":        total_applications,
        "pending_companies":         pending_companies,
        "pending_drives":            pending_drives,
        "total_selected":            total_selected,
        "blacklisted_companies":     blacklisted_companies,
        "blacklisted_students":      blacklisted_students,
        "application_status_counts": status_counts,
        "recent_applications":       [a.to_dict() for a in recent_apps],
        "pending_company_list":      [c.to_dict() for c in pending_co],
    }), 200


# ─── Company management ───────────────────────────────────────────────────────

@admin_bp.route("/companies", methods=["GET"])
@jwt_required()
@admin_required
@cached_response("admin:companies", ttl=TTL["medium"], vary_on_query=True)
def list_companies():
    # cached per query-string combination
    status   = request.args.get("status")
    q        = request.args.get("q", "").strip()
    industry = request.args.get("industry", "").strip()
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    query = Company.query
    if status:
        query = query.filter_by(approval_status=status)
    if q:
        query = query.filter(
            Company.name.ilike(f"%{q}%") |
            Company.location.ilike(f"%{q}%") |
            Company.hr_contact_name.ilike(f"%{q}%")
        )
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))

    total     = query.count()
    companies = (query.order_by(Company.created_at.desc())
                 .offset((page - 1) * per_page).limit(per_page).all())

    return jsonify({
        "companies": [c.to_dict() for c in companies],
        "total": total, "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }), 200


@admin_bp.route("/companies/<int:company_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_company(company_id):
    company = Company.query.get_or_404(company_id)
    data    = company.to_dict()
    data["drives"] = [d.to_dict() for d in company.placement_drives]
    return jsonify(data), 200


@admin_bp.route("/companies/<int:company_id>/approve", methods=["PUT"])
@jwt_required()
@admin_required
def approve_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = ApprovalStatus.APPROVED
    db.session.commit()
    invalidate("admin:companies:*", "admin:dashboard")
    return jsonify({"message": "Company approved", "company": company.to_dict()}), 200


@admin_bp.route("/companies/<int:company_id>/reject", methods=["PUT"])
@jwt_required()
@admin_required
def reject_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = ApprovalStatus.REJECTED
    db.session.commit()
    invalidate("admin:companies:*", "admin:dashboard")
    return jsonify({"message": "Company rejected", "company": company.to_dict()}), 200


@admin_bp.route("/companies/<int:company_id>/blacklist", methods=["PUT"])
@jwt_required()
@admin_required
def blacklist_company(company_id):
    company = Company.query.get_or_404(company_id)
    user    = User.query.get(company.user_id)
    user.is_blacklisted = True
    for drive in company.placement_drives:
        drive.status = DriveStatus.CLOSED
    db.session.commit()
    return jsonify({"message": "Company blacklisted and all drives closed"}), 200


@admin_bp.route("/companies/<int:company_id>/unblacklist", methods=["PUT"])
@jwt_required()
@admin_required
def unblacklist_company(company_id):
    company = Company.query.get_or_404(company_id)
    user    = User.query.get(company.user_id)
    user.is_blacklisted = False
    db.session.commit()
    return jsonify({"message": "Company restored"}), 200


@admin_bp.route("/companies/<int:company_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    user    = User.query.get(company.user_id)
    db.session.delete(company)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Company removed from system"}), 200


# ─── Student management ───────────────────────────────────────────────────────

@admin_bp.route("/students", methods=["GET"])
@jwt_required()
@admin_required
@cached_response("admin:students", ttl=TTL["medium"], vary_on_query=True)
def list_students():
    q          = request.args.get("q", "").strip()
    department = request.args.get("department", "").strip()
    year       = request.args.get("year")
    blacklisted= request.args.get("blacklisted")
    page       = int(request.args.get("page", 1))
    per_page   = int(request.args.get("per_page", 20))

    query = Student.query
    if q:
        query = (query.join(User, Student.user_id == User.id)
                 .filter(
                     Student.full_name.ilike(f"%{q}%")   |
                     Student.roll_number.ilike(f"%{q}%") |
                     Student.phone.ilike(f"%{q}%")       |
                     User.email.ilike(f"%{q}%")
                 ))
    if department:
        query = query.filter(Student.department.ilike(f"%{department}%"))
    if year:
        query = query.filter(Student.year == int(year))
    if blacklisted == "true":
        query = (query.join(User, Student.user_id == User.id)
                 .filter(User.is_blacklisted == True))

    total    = query.count()
    students = (query.order_by(Student.created_at.desc())
                .offset((page - 1) * per_page).limit(per_page).all())

    return jsonify({
        "students": [s.to_dict() for s in students],
        "total": total, "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }), 200


@admin_bp.route("/students/<int:student_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    data    = student.to_dict()
    data["applications"] = [a.to_dict() for a in student.applications]
    data["placements"]   = [p.to_dict() for p in student.placements]
    return jsonify(data), 200


@admin_bp.route("/students/<int:student_id>/blacklist", methods=["PUT"])
@jwt_required()
@admin_required
def blacklist_student(student_id):
    student = Student.query.get_or_404(student_id)
    user    = User.query.get(student.user_id)
    user.is_blacklisted = True
    db.session.commit()
    return jsonify({"message": "Student blacklisted"}), 200


@admin_bp.route("/students/<int:student_id>/activate", methods=["PUT"])
@jwt_required()
@admin_required
def activate_student(student_id):
    student = Student.query.get_or_404(student_id)
    user    = User.query.get(student.user_id)
    user.is_blacklisted = False
    user.is_active      = True
    db.session.commit()
    return jsonify({"message": "Student re-activated"}), 200


@admin_bp.route("/students/<int:student_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    user    = User.query.get(student.user_id)
    db.session.delete(student)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Student removed from system"}), 200


# ─── Placement drive management ───────────────────────────────────────────────

@admin_bp.route("/drives", methods=["GET"])
@jwt_required()
@admin_required
@cached_response("admin:drives", ttl=TTL["medium"], vary_on_query=True)
def list_drives():
    status     = request.args.get("status")
    company_id = request.args.get("company_id")
    q          = request.args.get("q", "").strip()
    page       = int(request.args.get("page", 1))
    per_page   = int(request.args.get("per_page", 20))

    query = PlacementDrive.query
    if status:
        query = query.filter_by(status=status)
    if company_id:
        query = query.filter_by(company_id=int(company_id))
    if q:
        query = query.filter(PlacementDrive.job_title.ilike(f"%{q}%"))

    total  = query.count()
    drives = (query.order_by(PlacementDrive.created_at.desc())
              .offset((page - 1) * per_page).limit(per_page).all())

    return jsonify({
        "drives": [d.to_dict() for d in drives],
        "total": total, "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }), 200


@admin_bp.route("/drives/<int:drive_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    data  = drive.to_dict()
    data["applications"] = [a.to_dict() for a in drive.applications]
    return jsonify(data), 200


@admin_bp.route("/drives/<int:drive_id>/approve", methods=["PUT"])
@jwt_required()
@admin_required
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = DriveStatus.APPROVED
    db.session.commit()
    invalidate("admin:drives:*", "drives:approved:*", "admin:dashboard")
    return jsonify({"message": "Drive approved", "drive": drive.to_dict()}), 200


@admin_bp.route("/drives/<int:drive_id>/reject", methods=["PUT"])
@jwt_required()
@admin_required
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = DriveStatus.CLOSED
    db.session.commit()
    invalidate("admin:drives:*", "drives:approved:*", "admin:dashboard")
    return jsonify({"message": "Drive rejected"}), 200


@admin_bp.route("/drives/<int:drive_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    db.session.delete(drive)
    db.session.commit()
    return jsonify({"message": "Drive removed"}), 200


# ─── Applications (admin view) ────────────────────────────────────────────────

@admin_bp.route("/applications", methods=["GET"])
@jwt_required()
@admin_required
def list_applications():
    status   = request.args.get("status")
    drive_id = request.args.get("drive_id")
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    query = Application.query
    if status:
        query = query.filter_by(status=status)
    if drive_id:
        query = query.filter_by(drive_id=int(drive_id))

    total = query.count()
    apps  = (query.order_by(Application.applied_at.desc())
             .offset((page - 1) * per_page).limit(per_page).all())

    return jsonify({
        "applications": [a.to_dict() for a in apps],
        "total": total, "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }), 200


# ─── Global search ────────────────────────────────────────────────────────────

@admin_bp.route("/search", methods=["GET"])
@jwt_required()
@admin_required
def global_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"students": [], "companies": [], "drives": []}), 200

    students = (Student.query
                .join(User, Student.user_id == User.id)
                .filter(
                    Student.full_name.ilike(f"%{q}%")   |
                    Student.roll_number.ilike(f"%{q}%") |
                    User.email.ilike(f"%{q}%")
                ).limit(10).all())

    companies = (Company.query
                 .filter(
                     Company.name.ilike(f"%{q}%") |
                     Company.industry.ilike(f"%{q}%")
                 ).limit(10).all())

    drives = (PlacementDrive.query
              .filter(PlacementDrive.job_title.ilike(f"%{q}%"))
              .limit(10).all())

    return jsonify({
        "students":  [s.to_dict() for s in students],
        "companies": [c.to_dict() for c in companies],
        "drives":    [d.to_dict() for d in drives],
    }), 200


# ─── Placement records ────────────────────────────────────────────────────────

@admin_bp.route("/placements", methods=["GET"])
@jwt_required()
@admin_required
def list_placements():
    placements = Placement.query.order_by(Placement.created_at.desc()).all()
    return jsonify([p.to_dict() for p in placements]), 200


# ══════════════════════════════════════════════════════════════════════════════
# CROSS-ROLE: Admin views student profile + full history
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route("/students/<int:student_id>/history", methods=["GET"])
@jwt_required()
@admin_required
def student_history(student_id):
    from models.models import Student, Application, Placement
    student = Student.query.get_or_404(student_id)
    apps    = (Application.query
               .filter_by(student_id=student.id)
               .order_by(Application.applied_at.desc()).all())
    history = []
    for a in apps:
        entry = a.to_dict()
        if a.drive:
            entry["drive"] = a.drive.to_dict()
        if a.placement:
            entry["placement"] = a.placement.to_dict()
        history.append(entry)

    return jsonify({
        "student": student.to_dict(),
        "history": history,
        "summary": {
            "total":       len(apps),
            "placed":      sum(1 for a in apps if a.status in ("selected", "placed")),
            "rejected":    sum(1 for a in apps if a.status == "rejected"),
            "shortlisted": sum(1 for a in apps if a.status == "shortlisted"),
            "interview":   sum(1 for a in apps if a.status == "interview"),
        },
    }), 200


# ══════════════════════════════════════════════════════════════════════════════
# CACHE HEALTH + MANUAL FLUSH
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route("/cache/stats", methods=["GET"])
@jwt_required()
@admin_required
def get_cache_stats():
    """Returns Redis memory usage and key count."""
    return jsonify(cache_stats()), 200


@admin_bp.route("/cache/flush", methods=["DELETE"])
@jwt_required()
@admin_required
def flush_cache():
    """Flush ALL PPA cache keys (use sparingly)."""
    invalidate("*")
    return jsonify({"message": "Cache flushed"}), 200


@admin_bp.route("/cache/flush/<pattern>", methods=["DELETE"])
@jwt_required()
@admin_required
def flush_cache_pattern(pattern):
    """Flush keys matching a specific pattern e.g. 'drives:*'."""
    import re
    if not re.match(r'^[\w:\*]+$', pattern):
        return jsonify({"message": "Invalid pattern"}), 400
    invalidate(pattern)
    return jsonify({"message": f"Cache flushed for pattern: {pattern}"}), 200


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS  — Chart.js data endpoints
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route("/analytics", methods=["GET"])
@jwt_required()
@admin_required
@cached_response("admin:analytics", ttl=TTL["short"])
def get_analytics():
    """
    Returns aggregated data for all Chart.js dashboards.
    All data is scoped to the last 6 months unless ?months=N is passed.
    """
    from models.models import (PlacementDrive, Application, Placement,
                                Company, Student, DriveStatus, ApplicationStatus)
    from sqlalchemy import func
    from datetime import datetime, timedelta
    import json

    months     = min(int(request.args.get("months", 6)), 12)
    since      = datetime.utcnow() - timedelta(days=months * 30)

    # ── 1. Application funnel (all time) ──────────────────────────────────────
    funnel_counts = {}
    for s in [ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED,
              ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER,
              ApplicationStatus.SELECTED, "placed", ApplicationStatus.REJECTED]:
        funnel_counts[s] = Application.query.filter_by(status=s).count()

    funnel = {
        "labels": ["Applied", "Shortlisted", "Interview", "Offer", "Selected/Placed", "Rejected"],
        "data":   [
            funnel_counts.get(ApplicationStatus.APPLIED,     0),
            funnel_counts.get(ApplicationStatus.SHORTLISTED, 0),
            funnel_counts.get(ApplicationStatus.INTERVIEW,   0),
            funnel_counts.get(ApplicationStatus.OFFER,       0),
            funnel_counts.get(ApplicationStatus.SELECTED,    0) +
                funnel_counts.get("placed",                  0),
            funnel_counts.get(ApplicationStatus.REJECTED,    0),
        ],
    }

    # ── 2. Monthly placements trend ───────────────────────────────────────────
    from calendar import month_abbr
    monthly_labels = []
    monthly_apps   = []
    monthly_placed = []

    now = datetime.utcnow()
    for i in range(months - 1, -1, -1):
        # start of that month
        target = now.replace(day=1) - timedelta(days=i * 30)
        target = target.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if target.month == 12:
            next_m = target.replace(year=target.year + 1, month=1)
        else:
            next_m = target.replace(month=target.month + 1)

        apps_cnt = Application.query.filter(
            Application.applied_at >= target,
            Application.applied_at < next_m
        ).count()

        placed_cnt = Application.query.filter(
            Application.applied_at >= target,
            Application.applied_at < next_m,
            Application.status.in_([ApplicationStatus.SELECTED, "placed"])
        ).count()

        monthly_labels.append(f"{month_abbr[target.month]} {target.year}")
        monthly_apps.append(apps_cnt)
        monthly_placed.append(placed_cnt)

    monthly_trend = {
        "labels":  monthly_labels,
        "datasets": [
            {"label": "Applications", "data": monthly_apps},
            {"label": "Placements",   "data": monthly_placed},
        ],
    }

    # ── 3. Top skills in demand (from approved drives) ────────────────────────
    drives = PlacementDrive.query.filter_by(status=DriveStatus.APPROVED).all()
    skill_count = {}
    for d in drives:
        if d.skills_required:
            for sk in d.skills_required.split(","):
                sk = sk.strip().lower()
                if sk:
                    skill_count[sk] = skill_count.get(sk, 0) + 1

    top_skills = sorted(skill_count.items(), key=lambda x: -x[1])[:10]
    skills_chart = {
        "labels": [s[0].title() for s in top_skills],
        "data":   [s[1]         for s in top_skills],
    }

    # ── 4. Placement rate by department ──────────────────────────────────────
    dept_stats = {}
    students = Student.query.all()
    for s in students:
        dept = s.department or "Other"
        if dept not in dept_stats:
            dept_stats[dept] = {"total": 0, "placed": 0}
        dept_stats[dept]["total"] += 1
        if s.placements:
            dept_stats[dept]["placed"] += 1

    dept_items = sorted(dept_stats.items(), key=lambda x: -x[1]["total"])[:8]
    dept_chart = {
        "labels": [d[0] for d in dept_items],
        "total":  [d[1]["total"]  for d in dept_items],
        "placed": [d[1]["placed"] for d in dept_items],
    }

    # ── 5. Top companies by placements ───────────────────────────────────────
    company_placements = {}
    for p in Placement.query.all():
        name = p.company.name if p.company else "Unknown"
        company_placements[name] = company_placements.get(name, 0) + 1

    top_companies = sorted(company_placements.items(), key=lambda x: -x[1])[:8]
    companies_chart = {
        "labels": [c[0] for c in top_companies],
        "data":   [c[1] for c in top_companies],
    }

    # ── 6. Summary KPIs ──────────────────────────────────────────────────────
    total_apps   = Application.query.count()
    total_placed = Application.query.filter(
        Application.status.in_([ApplicationStatus.SELECTED, "placed"])).count()

    kpis = {
        "total_students":   Student.query.count(),
        "total_companies":  Company.query.filter_by(
            approval_status="approved").count(),
        "total_drives":     PlacementDrive.query.count(),
        "total_applications": total_apps,
        "total_placed":     total_placed,
        "placement_rate":   round(total_placed / total_apps * 100, 1)
                            if total_apps else 0,
        "avg_salary":       round(
            sum(p.salary for p in Placement.query.all() if p.salary) /
            max(Placement.query.count(), 1), 2),
    }

    return jsonify({
        "kpis":            kpis,
        "funnel":          funnel,
        "monthly_trend":   monthly_trend,
        "skills_demand":   skills_chart,
        "dept_placements": dept_chart,
        "top_companies":   companies_chart,
    }), 200


# ── Public analytics (no auth — aggregated, no sensitive data) ────────────────

@admin_bp.route("/analytics/public", methods=["GET"])
@cached_response("public:analytics", ttl=TTL["long"])
def public_analytics():
    """
    Read-only aggregated stats for the public landing page.
    No PII, no company details, no student names.
    """
    from models.models import (PlacementDrive, Application, Student,
                                Company, Placement, DriveStatus, ApplicationStatus)

    total_apps   = Application.query.count()
    total_placed = Application.query.filter(
        Application.status.in_([ApplicationStatus.SELECTED, "placed"])).count()

    return jsonify({
        "total_students":   Student.query.count(),
        "total_companies":  Company.query.filter_by(
            approval_status="approved").count(),
        "total_drives":     PlacementDrive.query.filter_by(
            status=DriveStatus.APPROVED).count(),
        "total_placed":     total_placed,
        "placement_rate":   round(total_placed / total_apps * 100, 1)
                            if total_apps else 0,
        "avg_salary":       round(
            sum(p.salary for p in Placement.query.all() if p.salary) /
            max(Placement.query.count(), 1), 2),
    }), 200
