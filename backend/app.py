from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from config import Config
import os

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app, origins=["http://localhost:5173", "http://localhost:8080"],
         supports_credentials=True)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.company import company_bp
    from routes.student import student_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(company_bp, url_prefix="/api/company")
    app.register_blueprint(student_bp, url_prefix="/api/student")

    # JWT error handlers
    @jwt.unauthorized_loader
    def unauthorized_response(cb):
        return {"message": "Missing or invalid token"}, 401

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return {"message": "Token has expired"}, 401

    @jwt.invalid_token_loader
    def invalid_token_response(cb):
        return {"message": "Invalid token"}, 422

    return app
