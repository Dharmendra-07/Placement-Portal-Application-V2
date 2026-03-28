"""
celery_app.py  —  Celery + Beat factory
----------------------------------------
Run worker:   celery -A celery_app.celery worker --loglevel=info
Run beat:     celery -A celery_app.celery beat   --loglevel=info
Monitor:      celery -A celery_app.celery flower
"""

from celery import Celery
from celery.schedules import crontab
from config import Config


def make_celery(app=None):
    cel = Celery(
        "ppa",
        broker=Config.REDIS_URL,
        backend=Config.REDIS_URL,
        include=[
            "celery_tasks.reminders",
            "celery_tasks.reports",
            "celery_tasks.exports",
        ],
    )

    cel.conf.update(
        task_serializer          = "json",
        result_serializer        = "json",
        accept_content           = ["json"],
        timezone                 = "Asia/Kolkata",
        enable_utc               = True,
        result_expires           = 3600,          # results kept 1 hour
        task_track_started       = True,
        worker_prefetch_multiplier = 1,

        # ── Beat schedule ──────────────────────────────────────────────────
        beat_schedule = {
            # Daily at 08:00 IST — interview reminders
            "daily-interview-reminders": {
                "task":     "celery_tasks.reminders.send_interview_reminders",
                "schedule": crontab(hour=8, minute=0),
                "args":     (),
            },
            # First day of every month at 07:00 IST — placement reports
            "monthly-placement-report": {
                "task":     "celery_tasks.reports.generate_monthly_placement_report",
                "schedule": crontab(day_of_month=1, hour=7, minute=0),
                "args":     (),
            },
        },
    )

    if app:
        # Push Flask app context into every task
        class ContextTask(cel.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        cel.Task = ContextTask

    return cel


celery = make_celery()
