import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from config import Config

db   = SQLAlchemy()
jwt  = JWTManager()
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config.get("EXPORT_FOLDER",
                os.path.join(os.path.dirname(__file__), "exports")),
                exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app,
         origins=["http://localhost:5173", "http://localhost:8080"],
         supports_credentials=True)

    from routes.auth    import auth_bp
    from routes.admin   import admin_bp
    from routes.company import company_bp
    from routes.student import student_bp
    from routes.jobs       import jobs_bp
    from routes.analytics  import analytics_bp

    app.register_blueprint(auth_bp,    url_prefix="/api/auth")
    app.register_blueprint(admin_bp,   url_prefix="/api/admin")
    app.register_blueprint(company_bp, url_prefix="/api/company")
    app.register_blueprint(student_bp, url_prefix="/api/student")
    app.register_blueprint(jobs_bp,      url_prefix="/api/jobs")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(ats_bp,        url_prefix="/api/ats")

    # Attach celery's Flask context
    from celery_app import make_celery
    make_celery(app)

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
