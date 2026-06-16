import os
from flask import Flask
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from flasgger import Swagger
from app.models import db, Event
from config import Config
from datetime import date, timedelta

migrate = Migrate()
scheduler = APScheduler()

def update_recurring_events():
    with scheduler.app.app_context(): # type: ignore
        from app.web.admin_routes import format_indo_date
        today = date.today()
        events = Event.query.filter(Event.is_recurring == True, Event.raw_date < today).all()
        for e in events:
            while e.raw_date < today:
                e.raw_date += timedelta(days=7)
            e.tanggal_lengkap = format_indo_date(str(e.raw_date))
        db.session.commit()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    app.secret_key = os.getenv('JWT_SECRET_KEY', 'tegal_culture_secret_key')

    app.config['SWAGGER'] = {
        'title': 'Tegal Culture API',
        'uiversion': 3,
        'description': 'Dokumentasi REST API untuk aplikasi mobile Tegal Culture.'
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Tegal Culture API",
            "description": "Dokumentasi REST API untuk aplikasi mobile Tegal Culture.",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Format pengisian: Bearer <Token_JWT_Supabase>"
            }
        }
    }

    db.init_app(app)
    migrate.init_app(app, db)
    
    Swagger(app, template=swagger_template)

    if not scheduler.running:
        scheduler.init_app(app)
        scheduler.add_job(id='recurring_task', func=update_recurring_events, trigger='cron', hour=0, minute=1)
        scheduler.start()

    from app.api.v1_routes import api_v1
    from app.api.auth_routes import auth_api
    from app.web.public_routes import public_bp
    from app.web.admin_routes import admin_bp
    from app.api.v1 import v1_bp

    app.register_blueprint(v1_bp)
    app.register_blueprint(api_v1)
    app.register_blueprint(auth_api)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    return app