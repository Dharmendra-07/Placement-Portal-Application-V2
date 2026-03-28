"""
utils/notifications.py
-----------------------
Shared notification helpers used by Celery tasks.

Channels:
  send_email()       — plain-text email via Flask-Mail
  send_email_html()  — HTML + fallback plain-text email
  send_gchat_message() — Google Chat incoming webhook
"""

import logging
import requests
from config import Config

logger = logging.getLogger(__name__)


# ── Email ──────────────────────────────────────────────────────────────────────

def send_email(to: str, subject: str, body: str):
    """
    Send a plain-text email.
    Silently logs on failure so one bad address never breaks a batch job.
    """
    try:
        from app import create_app, mail
        from flask_mail import Message

        app = create_app()
        with app.app_context():
            msg = Message(
                subject    = subject,
                recipients = [to],
                body       = body,
                sender     = Config.MAIL_DEFAULT_SENDER,
            )
            mail.send(msg)
            logger.debug("Email sent to %s: %s", to, subject)
    except Exception as exc:
        logger.warning("send_email failed (to=%s): %s", to, exc)


def send_email_html(to: str, subject: str, html: str, plain: str = ""):
    """
    Send an HTML email with a plain-text fallback.
    """
    try:
        from app import create_app, mail
        from flask_mail import Message

        app = create_app()
        with app.app_context():
            msg = Message(
                subject    = subject,
                recipients = [to],
                html       = html,
                body       = plain or "Please view this email in an HTML-capable client.",
                sender     = Config.MAIL_DEFAULT_SENDER,
            )
            mail.send(msg)
            logger.debug("HTML email sent to %s: %s", to, subject)
    except Exception as exc:
        logger.warning("send_email_html failed (to=%s): %s", to, exc)


# ── Google Chat ────────────────────────────────────────────────────────────────

def send_gchat_message(text: str):
    """
    Posts a plain-text card to a Google Chat Space via incoming webhook.
    No-op if GCHAT_WEBHOOK_URL is not configured.
    """
    webhook_url = Config.GCHAT_WEBHOOK_URL
    if not webhook_url:
        return

    try:
        payload  = {"text": text}
        response = requests.post(
            webhook_url, json=payload, timeout=10
        )
        response.raise_for_status()
        logger.debug("GChat message sent.")
    except Exception as exc:
        logger.warning("send_gchat_message failed: %s", exc)
