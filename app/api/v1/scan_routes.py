from flask import Blueprint, request, jsonify
from app.services.scan_service import ScanService
from app.services.ai_scan_service import AIScanService
from app.services.auth_service import token_required

scan_bp = Blueprint('scan', __name__)

@scan_bp.route('/qr', methods=['POST'])
@token_required
def scan_qr(current_user):
    data = request.get_json()
    if not data or 'site_id' not in data:
        return jsonify({"message": "site_id is required"}), 400
    
    site_id = data['site_id']
    result, error = ScanService.scan_via_qr(current_user.id, site_id)
    if error:
        return jsonify({"message": error}), 400
    
    return jsonify(result), 200

@scan_bp.route('/geofence', methods=['POST'])
@token_required
def scan_geofence(current_user):
    data = request.get_json()
    if not data or 'site_id' not in data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({"message": "site_id, latitude, and longitude are required"}), 400
    
    site_id = data['site_id']
    user_lat = float(data['latitude'])
    user_lon = float(data['longitude'])
    
    result, error = ScanService.scan_via_geofence(current_user.id, site_id, user_lat, user_lon)
    if error:
        return jsonify({"message": error}), 400
    
    return jsonify(result), 200

@scan_bp.route('/read', methods=['POST'])
@token_required
def scan_read(current_user):
    data = request.get_json()
    if not data or 'site_id' not in data:
        return jsonify({"message": "site_id is required"}), 400
    
    site_id = data['site_id']
    result, error = ScanService.explore_via_read(current_user.id, site_id)
    if error:
        return jsonify({"message": error}), 400
    
    return jsonify(result), 200

@scan_bp.route('/ai', methods=['POST'])
@token_required
def scan_ai(current_user):
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    result, error = AIScanService.process_food_scan(current_user.id, file)
    if error:
        return jsonify({"status": "error", "message": error}), 400
    
    return jsonify({
        "status": "success",
        "data": result
    }), 200

@scan_bp.route('/ai/history', methods=['GET'])
@token_required
def get_ai_scan_history(current_user):
    result, error = AIScanService.get_user_ai_history(current_user.id)
    if error:
        return jsonify({"status": "error", "message": error}), 400
    
    return jsonify({
        "status": "success",
        "data": result
    }), 200