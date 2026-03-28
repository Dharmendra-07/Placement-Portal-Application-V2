"""
celery_tasks/exports.py
------------------------
User-triggered async jobs for CSV export.

• Student triggers export → job runs async → CSV saved → email sent
• Company triggers export → same flow for their applications/placements

API endpoints (in routes/jobs.py) fire these tasks and return a task_id
immediately. The frontend polls /api/jobs/status/<task_id> for completion.
"""

import csv
import io
import logging
import os
from datetime import datetime, timezone

from celery_app import celery
from utils.notifications import send_email

logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _save_csv(rows, headers, filename, export_dir):
    os.makedirs(export_dir, exist_ok=True)
    filepath = os.path.join(export_dir, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        writer.writerows(rows)
    return filepath


# ══════════════════════════════════════════════════════════════════════════════
# STUDENT  — export application history
# ══════════════════════════════════════════════════════════════════════════════

@celery.task(name="celery_tasks.exports.export_student_applications",
             bind=True, max_retries=2, default_retry_delay=60)
def export_student_applications(self, student_id: int):
    """
    Exports a student's full application history as CSV.
    Emails the download link once done.
    """
    try:
        from app import create_app
        from models.models import Student, Application, User

        app = create_app()
        with app.app_context():
            student = Student.query.get(student_id)
            if not student:
                return {"error": "Student not found"}

            user = User.query.get(student.user_id)

            apps = (Application.query
                    .filter_by(student_id=student_id)
                    .order_by(Application.applied_at.desc()).all())

            headers = [
                "Application ID", "Student ID", "Student Name",
                "Company", "Job Title", "Job Type", "Location",
                "Applied On", "Status",
                "Interview Type", "Interview Date",
                "Remarks",
                "Placed", "Position", "Salary (LPA)", "Joining Date",
            ]

            rows = []
            for a in apps:
                placement = a.placement
                rows.append([
                    a.id,
                    student.id,
                    student.full_name,
                    a.company_name or "",
                    a.job_title    or "",
                    a.drive.job_type  if a.drive else "",
                    a.drive.location  if a.drive else "",
                    a.applied_at.strftime("%Y-%m-%d") if a.applied_at else "",
                    a.status,
                    a.interview_type  or "",
                    a.interview_date.strftime("%Y-%m-%d %H:%M")
                        if a.interview_date else "",
                    (a.remarks or "").replace("\n", " "),
                    "Yes" if placement else "No",
                    placement.position    if placement else "",
                    placement.salary      if placement else "",
                    str(placement.joining_date) if (placement and
                                                    placement.joining_date) else "",
                ])

            ts       = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"student_{student_id}_applications_{ts}.csv"
            filepath = _save_csv(
                rows, headers, filename,
                app.config.get("EXPORT_FOLDER",
                               os.path.join(os.path.dirname(__file__),
                                            "..", "exports"))
            )

            # Notify student by email
            download_url = f"/api/jobs/download/{filename}"
            if user:
                send_email(
                    to      = user.email,
                    subject = "Your application history export is ready",
                    body    = (
                        f"Hi {student.full_name},\n\n"
                        f"Your placement application history CSV has been generated.\n\n"
                        f"Download link: {download_url}\n\n"
                        f"(Link expires after 24 hours)\n\n"
                        f"— Placement Portal"
                    ),
                )

            logger.info("Student CSV export done: %s (%d rows)", filename, len(rows))
            return {
                "filename":     filename,
                "download_url": download_url,
                "total_rows":   len(rows),
                "student_name": student.full_name,
            }

    except Exception as exc:
        logger.error("export_student_applications failed: %s", exc)
        raise self.retry(exc=exc)


# ══════════════════════════════════════════════════════════════════════════════
# COMPANY  — export applicants + placements
# ══════════════════════════════════════════════════════════════════════════════

@celery.task(name="celery_tasks.exports.export_company_applications",
             bind=True, max_retries=2, default_retry_delay=60)
def export_company_applications(self, company_id: int):
    """
    Exports a company's received applications and placements as CSV.
    Emails the download link to the company's HR email.
    """
    try:
        from app import create_app
        from models.models import Company, Application, User

        app = create_app()
        with app.app_context():
            company = Company.query.get(company_id)
            if not company:
                return {"error": "Company not found"}

            user = User.query.get(company.user_id)

            # All applications across all drives
            drive_ids = [d.id for d in company.placement_drives]
            apps = (Application.query
                    .filter(Application.drive_id.in_(drive_ids))
                    .order_by(Application.applied_at.desc()).all()
                    if drive_ids else [])

            headers = [
                "Application ID", "Student Name", "Department", "CGPA",
                "Drive ID", "Job Title", "Job Type",
                "Applied On", "Status",
                "Interview Type", "Interview Date",
                "Remarks",
                "Placed", "Position", "Salary (LPA)", "Joining Date",
            ]

            rows = []
            for a in apps:
                placement = a.placement
                rows.append([
                    a.id,
                    a.student.full_name  if a.student else "",
                    a.student.department if a.student else "",
                    a.student.cgpa       if a.student else "",
                    a.drive_id,
                    a.job_title or "",
                    a.drive.job_type if a.drive else "",
                    a.applied_at.strftime("%Y-%m-%d") if a.applied_at else "",
                    a.status,
                    a.interview_type or "",
                    a.interview_date.strftime("%Y-%m-%d %H:%M")
                        if a.interview_date else "",
                    (a.remarks or "").replace("\n", " "),
                    "Yes" if placement else "No",
                    placement.position    if placement else "",
                    placement.salary      if placement else "",
                    str(placement.joining_date) if (placement and
                                                    placement.joining_date) else "",
                ])

            ts       = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"company_{company_id}_applications_{ts}.csv"
            filepath = _save_csv(
                rows, headers, filename,
                app.config.get("EXPORT_FOLDER",
                               os.path.join(os.path.dirname(__file__),
                                            "..", "exports"))
            )

            download_url = f"/api/jobs/download/{filename}"
            if user:
                send_email(
                    to      = user.email,
                    subject = "Your applications export is ready",
                    body    = (
                        f"Hi {company.hr_contact_name or company.name} team,\n\n"
                        f"Your applications CSV export ({len(rows)} records) "
                        f"is ready to download.\n\n"
                        f"Download link: {download_url}\n\n"
                        f"(Link expires after 24 hours)\n\n"
                        f"— Placement Portal"
                    ),
                )

            logger.info("Company CSV export done: %s (%d rows)", filename, len(rows))
            return {
                "filename":     filename,
                "download_url": download_url,
                "total_rows":   len(rows),
                "company_name": company.name,
            }

    except Exception as exc:
        logger.error("export_company_applications failed: %s", exc)
        raise self.retry(exc=exc)
