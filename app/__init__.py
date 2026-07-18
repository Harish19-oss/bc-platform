from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(app)

    from app import models

    from app.blueprints.main import main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.admin import admin_bp
    app.register_blueprint(admin_bp)

    from app.blueprints.genes import genes_bp
    app.register_blueprint(genes_bp)
    from app.blueprints.proteins import proteins_bp
    app.register_blueprint(proteins_bp)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.admin import AdminUser
        return AdminUser.query.get(int(user_id))

    login_manager.login_view = "admin.login"

    return app