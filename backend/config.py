import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ppa-secret-key-change-in-prod")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///ppa.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "ppa-jwt-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours

    # Redis
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300

    # Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@ppa.com")

    # Admin credentials (pre-seeded)
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@ppa.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@1234")
    ADMIN_NAME = os.environ.get("ADMIN_NAME", "Institute Admin")

    # Upload folder
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    # Export folder
    EXPORT_FOLDER = os.path.join(os.path.dirname(__file__), "exports")

    # Google Chat webhook (optional)
    GCHAT_WEBHOOK_URL = os.environ.get("GCHAT_WEBHOOK_URL", "")

    # Celery beat db
    CELERYBEAT_SCHEDULE_FILENAME = "celerybeat-schedule"

