from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.search_service import SearchService

search_bp = Blueprint('search_bp', __name__)

@search_bp.route('', methods=['GET'])
@jwt_required()
def search_map():
    query = request.args.get('q', '').strip()
    lat_str = request.args.get('lat')
    lon_str = request.args.get('lon')

    user_lat = None
    user_lon = None

    try:
        if lat_str:
            user_lat = float(lat_str)
        if lon_str:
            user_lon = float(lon_str)
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid latitude or longitude format"}), 400

    results = SearchService.search_map(query, user_lat, user_lon)
    return jsonify({
        "status": "success",
        "data": results
    }), 200