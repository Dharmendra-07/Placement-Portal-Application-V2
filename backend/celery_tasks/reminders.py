"""
celery_tasks/reminders.py
--------------------------
Scheduled daily at 08:00 IST via Celery Beat.

Sends interview reminders to students who have an interview
scheduled within the next 24 hours.

Delivery channels (configured via .env):
  • Email       — always attempted via Flask-Mail
  • Google Chat — if GCHAT_WEBHOOK_URL is set
"""

import logging
from datetime import datetime, timedelta, timezone

from celery_app import celery
from utils.notifications import send_email, send_gchat_message

logger = logging.getLogger(__name__)


@celery.task(name="celery_tasks.reminders.send_interview_reminders",
             bind=True, max_retries=3, default_retry_delay=300)
def send_interview_reminders(self):
    """
    Finds all upcoming interviews in the next 24 h and
    dispatches reminder emails (+ optional GChat messages).
    """
    try:
        from app import create_app, db
        from models.models import Application, Student, User

        app = create_app()
        with app.app_context():
            now      = datetime.now(timezone.utc)
            deadline = now + timedelta(hours=24)

            upcoming = (Application.query
                        .filter(Application.interview_date >= now)
                        .filter(Application.interview_date <= deadline)
                        .filter(Application.status.in_(
                            ["shortlisted", "interview", "waiting"]))
                        .all())

            sent = 0
            for app_record in upcoming:
                student = app_record.student
                if not student:
                    continue

                user = User.query.get(student.user_id)
                if not user or not user.is_active:
                    continue

                interview_dt = app_record.interview_date.strftime(
                    "%d %b %Y at %I:%M %p")
                company_name = (app_record.drive.company.name
                                if app_record.drive and app_record.drive.company
                                else "the company")
                job_title    = (app_record.drive.job_title
                                if app_record.drive else "the position")

                subject = f"Interview Reminder — {job_title} at {company_name}"
                body = f"""
Hi {student.full_name},

This is a reminder that you have an interview scheduled:

  Company   : {company_name}
  Position  : {job_title}
  Type      : {app_record.interview_type or 'In-person'}
  Date/Time : {interview_dt}
  Notes     : {app_record.remarks or '—'}

Please be on time and carry all necessary documents.

Best of luck!
— Placement Portal Team
""".strip()

                # Email
                send_email(to=user.email, subject=subject, body=body)

                # Google Chat (optional)
                send_gchat_message(
                    f"*Interview Reminder* — {student.full_name}\n"
                    f"*{job_title}* at *{company_name}*\n"
                    f"Scheduled: {interview_dt}"
                )

                sent += 1
                logger.info("Reminder sent to %s (%s)", user.email, company_name)

            logger.info("Interview reminders: %d sent out of %d upcoming",
                        sent, len(upcoming))
            return {"sent": sent, "total_upcoming": len(upcoming)}

    except Exception as exc:
        logger.error("send_interview_reminders failed: %s", exc)
        raise self.retry(exc=exc)
