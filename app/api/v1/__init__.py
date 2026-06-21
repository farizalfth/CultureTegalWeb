from flask import Blueprint
from .user_routes import user_api
from .culture_routes import culture_v1_bp 
from .event_routes import event_v1_bp
from .news_routes import news_v1_bp


v1_bp = Blueprint('v1', __name__, url_prefix='/api/v1')

v1_bp.register_blueprint(user_api, url_prefix='/users')
v1_bp.register_blueprint(culture_v1_bp, url_prefix='/explore')
v1_bp.register_blueprint(event_v1_bp, url_prefix='/events')
v1_bp.register_blueprint(news_v1_bp, url_prefix='/news')
