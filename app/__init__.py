import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from flasgger import Swagger
from datetime import date, datetime, timedelta
from .models import db, Event, UserFavorite
from config import Config
from .services.notification_service import NotificationService

migrate = Migrate()
scheduler = APScheduler()

def update_recurring_events():
    with scheduler.app.app_context(): # type: ignore
        from .web.admin_routes import format_indo_date
        today = date.today()
        events = Event.query.filter(Event.is_recurring == True, Event.raw_date < today).all()
        for e in events:
            while e.raw_date < today:
                e.raw_date += timedelta(days=7)
            e.tanggal_lengkap = format_indo_date(str(e.raw_date))
        db.session.commit()

def run_daily_scrape():
    with scheduler.app.app_context(): # type: ignore
        mongo_uri = scheduler.app.config.get('MONGO_URI') # type: ignore
        from .services.scraper_service import ScraperService
        ScraperService.run_scraping_job(mongo_uri)

def check_and_send_event_reminders():
    with scheduler.app.app_context(): # type: ignore
        now = datetime.now()
        favorites = UserFavorite.query.filter_by(target_type='event').all()
        
        for fav in favorites:
            event = Event.query.get(fav.target_id)
            if not event or not event.raw_date:
                continue
                
            try:
                start_time_str = event.waktu_pelaksanaan.split('-')[0].strip()
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                event_datetime = datetime.combine(event.raw_date, start_time)
            except:
                continue
                
            time_diff = event_datetime - now
            
            if timedelta(minutes=0) < time_diff <= timedelta(minutes=60):
                if not getattr(fav, 'reminder_1h_sent', True):
                    success, err = NotificationService.send_to_user(
                        fav.user_id,
                        "Pengingat Event",
                        f"Event '{event.judul_event}' yang kamu simpan akan dimulai dalam 1 jam!"
                    )
                    if success:
                        fav.reminder_1h_sent = True # type: ignore
                        
            elif time_diff <= timedelta(minutes=0):
                if not getattr(fav, 'reminder_start_sent', True):
                    success, err = NotificationService.send_to_user(
                        fav.user_id,
                        "Event Dimulai!",
                        f"Event '{event.judul_event}' yang kamu simpan telah dimulai sekarang!"
                    )
                    if success:
                        fav.reminder_start_sent = True # type: ignore
                        
        db.session.commit()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    app.secret_key = os.getenv('JWT_SECRET_KEY', 'tegal_culture_secret_key')
    CORS(app, resources={r"/api/*": {"origins": "*"}})

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
        scheduler.add_job(id='daily_scrape_task', func=run_daily_scrape, trigger='cron', hour=0, minute=0)
        scheduler.add_job(id='event_reminders_task', func=check_and_send_event_reminders, trigger='interval', minutes=15)
        scheduler.start()

    from .api.v1_routes import api_v1
    from .api.auth_routes import auth_api
    from .web.public_routes import public_bp
    from .web.admin_routes import admin_bp
    from .api.v1 import v1_bp

    app.register_blueprint(v1_bp)
    app.register_blueprint(api_v1)
    app.register_blueprint(auth_api)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    return app