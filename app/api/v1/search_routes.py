import os
from flask import Blueprint, request, jsonify, current_app
from app.services.search_service import SearchService
from app.services.scraper_service import ScraperService
from app.services.auth_service import token_required

search_bp = Blueprint('search_bp', __name__)

@search_bp.route('', methods=['GET'])
@token_required
def search_map(current_user):
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

@search_bp.route('/public-analytics', methods=['GET'])
@token_required
def public_analytics(current_user):
    try:
        mongo_uri = os.getenv('MONGO_URI')
        location = request.args.get('location', 'global_all')
        
        data = ScraperService.get_global_analytics(location, mongo_uri)
        wordcloud = ScraperService.get_word_frequencies(location, mongo_uri)
        data['wordcloud'] = wordcloud
        
        return jsonify({
            "status": "success",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500