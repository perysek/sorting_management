from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_class='app.config.Config'):
    """Application factory for Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes.main import bp as main_bp
    from app.routes.reports import bp as reports_bp
    from app.routes.operators import bp as operators_bp
    from app.routes.categories import bp as categories_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(operators_bp, url_prefix='/operators')
    app.register_blueprint(categories_bp, url_prefix='/categories')

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    return app
