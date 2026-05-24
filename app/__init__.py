import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from app.config import Config

db = SQLAlchemy()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance folder and upload folder exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    # Import models for Alembic / migration awareness
    from app.models.business import Business  # noqa
    from app.models.submission import DirectorySubmission  # noqa

    # Register blueprints
    from app.routes.dashboard import dashboard_bp
    from app.routes.business import business_bp
    from app.routes.directory import directory_bp
    from app.routes.submission import submission_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(directory_bp)
    app.register_blueprint(submission_bp)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    return app
