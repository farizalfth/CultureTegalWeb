from flask import Blueprint
from .user_routes import user_api

v1_bp = Blueprint('v1', __name__, url_prefix='/api/v1')

v1_bp.register_blueprint(user_api, url_prefix='/users')