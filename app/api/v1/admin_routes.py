import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from app.models import db, ScrapeTarget
from app.services.scraper_service import ScraperService

admin_api = Blueprint('admin_api', __name__)

@admin_api.route('/targets', methods=['GET'])
@jwt_required()
def get_targets():
    targets = ScrapeTarget.query.all()
    result = []
    for t in targets:
        result.append({
            "id": str(t.id),
            "nama_tempat": t.nama_tempat,
            "url_maps": t.url_maps
        })
    return jsonify({"status": "success", "data": result}), 200

@admin_api.route('/targets', methods=['POST'])
@jwt_required()
def add_target():
    data = request.get_json()
    if not data or 'nama_tempat' not in data or 'url_maps' not in data:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
    
    url_maps = data['url_maps']
    if not ScraperService.validate_url(url_maps):
        return jsonify({"status": "error", "message": "Invalid Google Maps URL pattern"}), 400

    new_target = ScrapeTarget(
        id=uuid.uuid4(), # type: ignore
        nama_tempat=data['nama_tempat'], # type: ignore
        url_maps=url_maps # type: ignore
    )
    db.session.add(new_target)
    db.session.commit()
    return jsonify({"status": "success", "message": "Target added"}), 201

@admin_api.route('/targets/<uuid:target_id>', methods=['DELETE'])
@jwt_required()
def delete_target(target_id):
    target = ScrapeTarget.query.get(target_id)
    if not target:
        return jsonify({"status": "error", "message": "Target not found"}), 404
    
    db.session.delete(target)
    db.session.commit()
    return jsonify({"status": "success", "message": "Target deleted"}), 200

@admin_api.route('/scrape/trigger', methods=['POST'])
@jwt_required()
def trigger_scrape():
    mongo_uri = current_app.config.get('MONGO_URI') # type: ignore
    if ScraperService.progress["running"]:
        return jsonify({"status": "error", "message": "Scraper is already running"}), 400
    
    ScraperService.run_scraping_job(mongo_uri) # type: ignore
    return jsonify({"status": "success", "message": "Scraper started in background"}), 202

@admin_api.route('/scrape/status', methods=['GET'])
@jwt_required()
def get_scrape_status():
    return jsonify({"status": "success", "data": ScraperService.progress}), 200

@admin_api.route('/scrape/wordcloud/<string:location_name>', methods=['GET'])
@jwt_required()
def get_word_cloud_data(location_name):
    mongo_uri = current_app.config.get('MONGO_URI') # type: ignore
    result = ScraperService.get_word_frequencies(location_name, mongo_uri) # type: ignore
    return jsonify({"status": "success", "data": result}), 200