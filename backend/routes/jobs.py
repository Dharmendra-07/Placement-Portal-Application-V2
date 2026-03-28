"""
routes/jobs.py
--------------
REST endpoints that trigger async Celery jobs and
allow the frontend to poll job status + download results.

Endpoints:
  POST /api/jobs/export/student          — student triggers CSV export
  POST /api/jobs/export/company          — company triggers CSV export
  POST /api/jobs/report/trigger          — admin triggers monthly report manually
  GET  /api/jobs/status/<task_id>        — poll Celery task status
  GET  /api/jobs/download/<filename>     — download generated file
"""

import os
from flask import Blueprint, jsonify, request, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from celery.result import AsyncResult

from celery_app import celery
from utils.decorators import student_required, company_required, admin_required

jobs_bp = Blueprint("jobs", __name__)


# ── Student: trigger application CSV export ───────────────────────────────────

@jobs_bp.route("/export/student", methods=["POST"])
@jwt_required()
@student_required
def trigger_student_export():
    """Student triggers their own application history export."""
    from models.models import Student
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"message": "Student profile not found"}), 404

    from celery_tasks.exports import export_student_applications
    task = export_student_applications.delay(student.id)

    return jsonify({
        "message": "Export started. You will receive an email when it is ready.",
        "task_id": task.id,
        "status":  "PENDING",
    }), 202


# ── Company: trigger application CSV export ───────────────────────────────────

@jobs_bp.route("/export/company", methods=["POST"])
@jwt_required()
@company_required
def trigger_company_export():
    """Company triggers their applicants export."""
    from models.models import Company
    user_id = int(get_jwt_identity())
    company = Company.query.filter_by(user_id=user_id).first()
    if not company:
        return jsonify({"message": "Company profile not found"}), 404

    from celery_tasks.exports import export_company_applications
    task = export_company_applications.delay(company.id)

    return jsonify({
        "message": "Export started. You will receive an email when it is ready.",
        "task_id": task.id,
        "status":  "PENDING",
    }), 202


# ── Admin: manually trigger monthly report ────────────────────────────────────

@jobs_bp.route("/report/trigger", methods=["POST"])
@jwt_required()
@admin_required
def trigger_monthly_report():
    """Admin manually fires the monthly placement report job."""
    from celery_tasks.reports import generate_monthly_placement_report
    task = generate_monthly_placement_report.delay()

    return jsonify({
        "message": "Monthly report generation started.",
        "task_id": task.id,
        "status":  "PENDING",
    }), 202


# ── Admin: manually trigger interview reminders ───────────────────────────────

@jobs_bp.route("/reminders/trigger", methods=["POST"])
@jwt_required()
@admin_required
def trigger_reminders():
    """Admin manually fires the interview reminder job."""
    from celery_tasks.reminders import send_interview_reminders
    task = send_interview_reminders.delay()

    return jsonify({
        "message": "Interview reminders job started.",
        "task_id": task.id,
        "status":  "PENDING",
    }), 202


# ── Poll Celery task status ───────────────────────────────────────────────────

@jobs_bp.route("/status/<task_id>", methods=["GET"])
@jwt_required()
def get_task_status(task_id):
    """
    Returns the current state of a Celery task.
    States: PENDING → STARTED → SUCCESS | FAILURE
    """
    result = AsyncResult(task_id, app=celery)

    response = {
        "task_id": task_id,
        "status":  result.state,
    }

    if result.state == "SUCCESS":
        response["result"] = result.result
    elif result.state == "FAILURE":
        response["error"] = str(result.result)
    elif result.state == "STARTED":
        response["info"] = result.info

    return jsonify(response), 200


# ── Download generated file ───────────────────────────────────────────────────

@jobs_bp.route("/download/<filename>", methods=["GET"])
@jwt_required()
def download_file(filename):
    """
    Serves a generated CSV or HTML report file.
    Basic security: only alphanumeric, underscores, hyphens, dots.
    """
    import re
    if not re.match(r'^[\w\-\.]+$', filename):
        return jsonify({"message": "Invalid filename"}), 400

    export_dir = current_app.config.get(
        "EXPORT_FOLDER",
        os.path.join(os.path.dirname(__file__), "..", "exports")
    )

    if not os.path.exists(os.path.join(export_dir, filename)):
        return jsonify({"message": "File not found or has expired"}), 404

    return send_from_directory(export_dir, filename, as_attachment=True)
