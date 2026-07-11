from flask import Blueprint
from .user_routes import user_api
from .culture_routes import culture_v1_bp
from .event_routes import event_v1_bp
from .news_routes import news_v1_bp
from .umkm_routes import umkm_v1_bp
from .quiz_routes import quiz_bp
from .scan_routes import scan_bp
from .search_routes import search_bp

v1_bp = Blueprint('v1', __name__, url_prefix='/api/v1')

v1_bp.register_blueprint(user_api, url_prefix='/users')
v1_bp.register_blueprint(culture_v1_bp, url_prefix='/explore')
v1_bp.register_blueprint(event_v1_bp, url_prefix='/events')
v1_bp.register_blueprint(news_v1_bp, url_prefix='/news')
v1_bp.register_blueprint(umkm_v1_bp, url_prefix='/umkm')
v1_bp.register_blueprint(quiz_bp, url_prefix='/quizzes')
v1_bp.register_blueprint(scan_bp, url_prefix='/scans')
v1_bp.register_blueprint(search_bp, url_prefix='/search')