"""
Run this script once to create all tables and seed the admin user.
    python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from models.models import User, Role
from config import Config


def seed_database():
    app = create_app()

    with app.app_context():
        # Create all tables
        db.create_all()
        print("[✓] All tables created.")

        # Check if admin already exists
        admin = User.query.filter_by(role=Role.ADMIN).first()
        if admin:
            print(f"[i] Admin already exists: {admin.email}")
            return

        # Create admin user programmatically (no registration allowed)
        admin = User(
            email=Config.ADMIN_EMAIL,
            role=Role.ADMIN,
            is_active=True,
            is_blacklisted=False,
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()

        print(f"[✓] Admin user created.")
        print(f"    Email   : {Config.ADMIN_EMAIL}")
        print(f"    Password: {Config.ADMIN_PASSWORD}")
        print(f"    Role    : {Role.ADMIN}")


if __name__ == "__main__":
    seed_database()
