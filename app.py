from flask import Flask
from flask_migrate import Migrate
from app.models import db
from config import Config

migrate = Migrate()

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.api.v1_routes import api_v1
    from app.web.admin_routes import admin_bp

    app.register_blueprint(api_v1)
    app.register_blueprint(admin_bp)

    return app