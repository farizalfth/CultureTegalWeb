from flask import Blueprint
from .user_routes import user_api
from .culture_routes import culture_v1_bp 

v1_bp = Blueprint('v1', __name__, url_prefix='/api/v1')

v1_bp.register_blueprint(user_api, url_prefix='/users')
v1_bp.register_blueprint(culture_v1_bp, url_prefix='/explore')
