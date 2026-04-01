"""
routes/analytics.py
--------------------
Public read-only stats (no auth required) + role-specific chart data.

Public  : GET /api/analytics/public
Admin   : GET /api/analytics/admin
Company : GET /api/analytics/company
Student : GET /api/analytics/student
ATS     : POST /api/analytics/ats/screen
"""
import re
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from sqlalchemy import func

from app import db
from models.models import (User, Student, Company, PlacementDrive,
                            Application, Placement,
                            ApprovalStatus, DriveStatus, ApplicationStatus)
from utils.cache import cached_response, TTL
from utils.decorators import admin_required, company_required, student_required

analytics_bp = Blueprint("analytics", __name__)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _last_n_months(n=6):
    """Return list of (year, month) tuples for the last n months."""
    now = datetime.now(timezone.utc)
    months = []
    for i in range(n - 1, -1, -1):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))
    return months


def _month_label(year, month):
    return datetime(year, month, 1).strftime("%b %Y")


def _skill_frequency(drives):
    """Count how often each skill appears across drives."""
    counter = Counter()
    for d in drives:
        if d.skills_required:
            for sk in d.skills_required.split(","):
                sk = sk.strip().lower()
                if sk:
                    counter[sk] += 1
    return counter


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC endpoint — pre-login landing page stats
# ═══════════════════════════════════════════════════════════════════════════════

@analytics_bp.route("/public", methods=["GET"])
@cached_response("analytics:public", ttl=TTL["long"])
def public_stats():
    """
    Aggregated, anonymised placement statistics for the public landing page.
    No PII, no company details, no individual student data.
    """
    months = _last_n_months(6)

    # Monthly drive counts
    monthly_drives = []
    monthly_placements = []
    for y, m in months:
        start = datetime(y, m, 1, tzinfo=timezone.utc)
        if m == 12:
            end = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(y, m + 1, 1, tzinfo=timezone.utc)

        drives_count = PlacementDrive.query.filter(
            PlacementDrive.created_at >= start,
            PlacementDrive.created_at < end,
            PlacementDrive.status == DriveStatus.APPROVED,
        ).count()

        placed_count = Placement.query.filter(
            Placement.created_at >= start,
            Placement.created_at < end,
        ).count()

        monthly_drives.append(drives_count)
        monthly_placements.append(placed_count)

    labels = [_month_label(y, m) for y, m in months]

    # Top skill demands
    all_drives = PlacementDrive.query.filter_by(
        status=DriveStatus.APPROVED).all()
    skill_freq  = _skill_frequency(all_drives)
    top_skills  = skill_freq.most_common(10)

    # Funnel totals (anonymised)
    total_drives       = PlacementDrive.query.filter_by(
        status=DriveStatus.APPROVED).count()
    total_applications = Application.query.count()
    total_shortlisted  = Application.query.filter(
        Application.status.in_(["shortlisted", "interview"])).count()
    total_placed       = Placement.query.count()
    total_companies    = Company.query.filter_by(
        approval_status=ApprovalStatus.APPROVED).count()
    total_students     = Student.query.count()

    placement_rate = round(
        total_placed / total_applications * 100, 1
    ) if total_applications else 0

    return jsonify({
        "labels":             labels,
        "monthly_drives":     monthly_drives,
        "monthly_placements": monthly_placements,
        "top_skills":         [{"skill": s, "count": c} for s, c in top_skills],
        "funnel": {
            "drives":       total_drives,
            "applications": total_applications,
            "shortlisted":  total_shortlisted,
            "placed":       total_placed,
        },
        "highlights": {
            "total_companies":   total_companies,
            "total_students":    total_students,
            "placement_rate":    placement_rate,
            "total_placed":      total_placed,
        },
    }), 200


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN analytics
# ═══════════════════════════════════════════════════════════════════════════════

@analytics_bp.route("/admin", methods=["GET"])
@jwt_required()
@admin_required
@cached_response("analytics:admin", ttl=TTL["short"])
def admin_analytics():
    months  = _last_n_months(6)
    labels  = [_month_label(y, m) for y, m in months]

    # Applications per month
    monthly_apps = []
    monthly_placed = []
    for y, m in months:
        start = datetime(y, m, 1, tzinfo=timezone.utc)
        end   = (datetime(y + 1, 1, 1, tzinfo=timezone.utc)
                 if m == 12 else datetime(y, m + 1, 1, tzinfo=timezone.utc))
        apps = Application.query.filter(
            Application.applied_at >= start,
            Application.applied_at < end).count()
        placed = Placement.query.filter(
            Placement.created_at >= start,
            Placement.created_at < end).count()
        monthly_apps.append(apps)
        monthly_placed.append(placed)

    # Application status breakdown (doughnut)
    status_data = {}
    for s in [ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED,
              ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER,
              ApplicationStatus.SELECTED, ApplicationStatus.REJECTED,
              ApplicationStatus.WAITING]:
        status_data[s] = Application.query.filter_by(status=s).count()

    # Top companies by placements (bar)
    company_placements = (
        db.session.query(Company.name,
                         func.count(Placement.id).label("cnt"))
        .join(Placement, Placement.company_id == Company.id)
        .group_by(Company.id)
        .order_by(func.count(Placement.id).desc())
        .limit(8).all()
    )

    # Skill demand (top 12)
    all_drives = PlacementDrive.query.all()
    skill_freq = _skill_frequency(all_drives)
    top_skills = skill_freq.most_common(12)

    # Department placement rate
    dept_data = defaultdict(lambda: {"applied": 0, "placed": 0})
    students = Student.query.all()
    for s in students:
        dept = s.department or "Other"
        dept_data[dept]["applied"] += len(s.applications)
        dept_data[dept]["placed"]  += len(s.placements)

    dept_labels   = list(dept_data.keys())[:8]
    dept_applied  = [dept_data[d]["applied"]  for d in dept_labels]
    dept_placed   = [dept_data[d]["placed"]   for d in dept_labels]

    return jsonify({
        "labels":            labels,
        "monthly_apps":      monthly_apps,
        "monthly_placed":    monthly_placed,
        "status_breakdown":  status_data,
        "company_placements": {
            "labels": [r[0] for r in company_placements],
            "data":   [r[1] for r in company_placements],
        },
        "skill_demand": {
            "labels": [s for s, _ in top_skills],
            "data":   [c for _, c in top_skills],
        },
        "department_stats": {
            "labels":  dept_labels,
            "applied": dept_applied,
            "placed":  dept_placed,
        },
    }), 200


# ═══════════════════════════════════════════════════════════════════════════════
# COMPANY analytics
# ═══════════════════════════════════════════════════════════════════════════════

@analytics_bp.route("/company", methods=["GET"])
@jwt_required()
@company_required
@cached_response("analytics:company", ttl=TTL["short"])
def company_analytics():
    from models.models import Company as Co
    user_id = int(get_jwt_identity())
    company = Co.query.filter_by(user_id=user_id).first()
    if not company:
        return jsonify({"message": "Company not found"}), 404

    drives     = company.placement_drives
    drive_ids  = [d.id for d in drives]
    all_apps   = (Application.query
                  .filter(Application.drive_id.in_(drive_ids))
                  .all()) if drive_ids else []

    # Application funnel per drive
    funnel_labels = [d.job_title[:20] for d in drives]
    funnel_data   = {
        "applied":     [sum(1 for a in d.applications) for d in drives],
        "shortlisted": [sum(1 for a in d.applications
                            if a.status in ["shortlisted", "interview"])
                        for d in drives],
        "selected":    [sum(1 for a in d.applications
                            if a.status in ["selected", "placed"])
                        for d in drives],
    }

    # Status doughnut for all apps
    status_data = Counter(a.status for a in all_apps)

    # CGPA distribution of applicants (histogram buckets)
    cgpa_buckets = {"0-6": 0, "6-7": 0, "7-8": 0, "8-9": 0, "9-10": 0}
    for a in all_apps:
        if a.student and a.student.cgpa:
            cgpa = float(a.student.cgpa)
            if cgpa < 6:   cgpa_buckets["0-6"]  += 1
            elif cgpa < 7: cgpa_buckets["6-7"]  += 1
            elif cgpa < 8: cgpa_buckets["7-8"]  += 1
            elif cgpa < 9: cgpa_buckets["8-9"]  += 1
            else:          cgpa_buckets["9-10"] += 1

    # Department breakdown of applicants (pie)
    dept_counter = Counter(
        a.student.department or "Other"
        for a in all_apps if a.student)
    top_depts = dept_counter.most_common(6)

    return jsonify({
        "funnel": {
            "labels":      funnel_labels,
            "applied":     funnel_data["applied"],
            "shortlisted": funnel_data["shortlisted"],
            "selected":    funnel_data["selected"],
        },
        "status_breakdown": dict(status_data),
        "cgpa_distribution": {
            "labels": list(cgpa_buckets.keys()),
            "data":   list(cgpa_buckets.values()),
        },
        "department_breakdown": {
            "labels": [d for d, _ in top_depts],
            "data":   [c for _, c in top_depts],
        },
    }), 200


# ═══════════════════════════════════════════════════════════════════════════════
# STUDENT analytics
# ═══════════════════════════════════════════════════════════════════════════════

@analytics_bp.route("/student", methods=["GET"])
@jwt_required()
@student_required
def student_analytics():
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404

    apps = student.applications

    # Personal application funnel
    status_counts = Counter(a.status for a in apps)

    # Application timeline (applications over last 6 months)
    months = _last_n_months(6)
    labels = [_month_label(y, m) for y, m in months]
    monthly_apps = []
    for y, m in months:
        start = datetime(y, m, 1, tzinfo=timezone.utc)
        end   = (datetime(y + 1, 1, 1, tzinfo=timezone.utc)
                 if m == 12 else datetime(y, m + 1, 1, tzinfo=timezone.utc))
        cnt = sum(
            1 for a in apps
            if a.applied_at and
               start <= a.applied_at.replace(tzinfo=timezone.utc) < end
        )
        monthly_apps.append(cnt)

    # Skill match — compare student skills vs top demanded skills
    all_drives  = PlacementDrive.query.filter_by(
        status=DriveStatus.APPROVED).all()
    skill_freq  = _skill_frequency(all_drives)
    top_demanded = [s for s, _ in skill_freq.most_common(10)]

    student_skills = set()
    if student.skills:
        student_skills = {s.strip().lower()
                         for s in student.skills.split(",")}

    skill_match = {
        "labels":  top_demanded,
        "demand":  [skill_freq[s] for s in top_demanded],
        "has":     [1 if s in student_skills else 0
                    for s in top_demanded],
    }

    return jsonify({
        "labels":       labels,
        "monthly_apps": monthly_apps,
        "status_counts": dict(status_counts),
        "skill_match":  skill_match,
        "totals": {
            "applied":     len(apps),
            "shortlisted": status_counts.get("shortlisted", 0)
                         + status_counts.get("interview", 0),
            "placed":      status_counts.get("selected", 0)
                         + status_counts.get("placed", 0),
            "rejected":    status_counts.get("rejected", 0),
        },
    }), 200


# ═══════════════════════════════════════════════════════════════════════════════
# ATS RESUME SCREENER
# ═══════════════════════════════════════════════════════════════════════════════

@analytics_bp.route("/ats/screen", methods=["POST"])
@jwt_required()
def ats_screen():
    """
    ATS-style resume screener.

    Accepts:
      {
        "resume_text": "<plain text of the resume>",
        "job_description": "<JD text>",
        "required_skills": "Python, SQL, React",   // optional
        "min_cgpa": 7.0                             // optional
      }

    Returns a detailed score report.
    """
    data           = request.get_json() or {}
    resume_text    = data.get("resume_text", "").lower()
    jd_text        = data.get("job_description", "").lower()
    required_skills= data.get("required_skills", "")
    min_cgpa       = data.get("min_cgpa")

    if not resume_text:
        return jsonify({"message": "'resume_text' is required"}), 400

    # ── 1. Skill matching ────────────────────────────────────────────────────
    skill_list = []
    if required_skills:
        skill_list = [s.strip().lower()
                      for s in required_skills.split(",") if s.strip()]
    elif jd_text:
        # Extract candidate skills from JD if no explicit list
        common_skills = [
            "python", "java", "javascript", "typescript", "react", "vue",
            "angular", "node", "express", "flask", "django", "sql", "mysql",
            "postgresql", "mongodb", "redis", "docker", "kubernetes", "aws",
            "azure", "gcp", "git", "linux", "machine learning", "deep learning",
            "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn",
            "data analysis", "power bi", "tableau", "c", "c++", "go", "rust",
            "spring", "hibernate", "rest api", "graphql", "microservices",
        ]
        skill_list = [s for s in common_skills if s in jd_text]

    matched_skills  = [s for s in skill_list if s in resume_text]
    missing_skills  = [s for s in skill_list if s not in resume_text]
    skill_score     = (len(matched_skills) / len(skill_list) * 100
                       if skill_list else 0)

    # ── 2. JD keyword overlap ─────────────────────────────────────────────────
    jd_score = 0.0
    jd_matched_kw = []
    if jd_text:
        jd_words  = set(re.findall(r'\b[a-z]{4,}\b', jd_text))
        res_words = set(re.findall(r'\b[a-z]{4,}\b', resume_text))
        stop      = {"this","that","with","have","will","from","been","they",
                     "your","also","more","some","than","when","then","into",
                     "their","were","what","which","about","would","there",
                     "other","these","those","such","each","both","work",
                     "able","take","make","well","good","very","only","need"}
        jd_kw          = jd_words - stop
        jd_matched_kw  = sorted(jd_kw & res_words)
        jd_score       = min(len(jd_matched_kw) / max(len(jd_kw), 1) * 100, 100)

    # ── 3. Resume quality signals ─────────────────────────────────────────────
    quality_checks = {
        "has_email":        bool(re.search(r'[\w.+-]+@[\w-]+\.\w+', resume_text)),
        "has_phone":        bool(re.search(r'[\+\d][\d\s\-()]{8,15}', resume_text)),
        "has_education":    any(w in resume_text for w in
                                ["bachelor", "master", "b.tech", "b.e", "m.tech",
                                 "degree", "university", "college"]),
        "has_experience":   any(w in resume_text for w in
                                ["experience", "internship", "worked", "project",
                                 "developed", "built", "implemented", "designed"]),
        "has_github":       "github" in resume_text or "gitlab" in resume_text,
        "has_linkedin":     "linkedin" in resume_text,
        "has_certifications": any(w in resume_text for w in
                                  ["certified", "certification", "certificate",
                                   "aws", "google cloud", "microsoft"]),
        "adequate_length":  len(resume_text.split()) >= 150,
    }
    quality_score = sum(quality_checks.values()) / len(quality_checks) * 100

    # ── 4. CGPA check ─────────────────────────────────────────────────────────
    cgpa_ok    = True
    found_cgpa = None
    cgpa_match = re.search(r'cgpa[:\s]*([0-9]+\.[0-9]+)', resume_text)
    if cgpa_match:
        found_cgpa = float(cgpa_match.group(1))
        if min_cgpa and found_cgpa < float(min_cgpa):
            cgpa_ok = False

    # ── 5. Overall ATS score (weighted) ──────────────────────────────────────
    weights = {"skill": 0.45, "jd": 0.30, "quality": 0.25}
    overall = (skill_score   * weights["skill"] +
               jd_score      * weights["jd"]    +
               quality_score * weights["quality"])

    # ── 6. Verdict ────────────────────────────────────────────────────────────
    if overall >= 75:
        verdict = "Strong Match"
        verdict_color = "success"
    elif overall >= 50:
        verdict = "Good Match"
        verdict_color = "info"
    elif overall >= 30:
        verdict = "Partial Match"
        verdict_color = "warning"
    else:
        verdict = "Weak Match"
        verdict_color = "danger"

    # ── 7. Improvement tips ───────────────────────────────────────────────────
    tips = []
    if missing_skills:
        tips.append(f"Add these missing skills to your resume: {', '.join(missing_skills[:5])}")
    if not quality_checks["has_github"]:
        tips.append("Include a GitHub/GitLab profile link to showcase projects.")
    if not quality_checks["has_linkedin"]:
        tips.append("Add your LinkedIn profile URL.")
    if not quality_checks["has_certifications"]:
        tips.append("Mention relevant certifications to stand out.")
    if not quality_checks["adequate_length"]:
        tips.append("Resume seems too short — expand on projects and experience.")
    if jd_score < 40 and jd_text:
        tips.append("Tailor your resume language to more closely match the job description.")

    return jsonify({
        "overall_score":   round(overall, 1),
        "verdict":         verdict,
        "verdict_color":   verdict_color,
        "scores": {
            "skill_match":  round(skill_score, 1),
            "jd_overlap":   round(jd_score, 1),
            "resume_quality": round(quality_score, 1),
        },
        "skills": {
            "required": skill_list,
            "matched":  matched_skills,
            "missing":  missing_skills,
        },
        "jd_keywords_matched": jd_matched_kw[:20],
        "quality_checks":      quality_checks,
        "cgpa": {
            "found":    found_cgpa,
            "required": min_cgpa,
            "passes":   cgpa_ok,
        },
        "improvement_tips": tips,
    }), 200
