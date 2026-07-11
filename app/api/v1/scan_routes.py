from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.scan_service import ScanService
from app.services.ai_scan_service import AIScanService

scan_bp = Blueprint('scan', __name__)

@scan_bp.route('/qr', methods=['POST'])
@jwt_required()
def scan_qr():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data or 'site_id' not in data:
        return jsonify({"message": "site_id is required"}), 400
    
    site_id = data['site_id']
    result, error = ScanService.scan_via_qr(user_id, site_id)
    if error:
        return jsonify({"message": error}), 400
    
    return jsonify(result), 200

@scan_bp.route('/geofence', methods=['POST'])
@jwt_required()
def scan_geofence():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data or 'site_id' not in data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({"message": "site_id, latitude, and longitude are required"}), 400
    
    site_id = data['site_id']
    user_lat = float(data['latitude'])
    user_lon = float(data['longitude'])
    
    result, error = ScanService.scan_via_geofence(user_id, site_id, user_lat, user_lon)
    if error:
        return jsonify({"message": error}), 400
    
    return jsonify(result), 200

@scan_bp.route('/ai', methods=['POST'])
@jwt_required()
def scan_ai():
    user_id = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    result, error = AIScanService.process_food_scan(user_id, file)
    if error:
        return jsonify({"status": "error", "message": error}), 400
    
    return jsonify({
        "status": "success",
        "data": result
    }), 200

@scan_bp.route('/ai/history', methods=['GET'])
@jwt_required()
def get_ai_scan_history():
    user_id = get_jwt_identity()
    result, error = AIScanService.get_user_ai_history(user_id)
    if error:
        return jsonify({"status": "error", "message": error}), 400
    
    return jsonify({
        "status": "success",
        "data": result
    }), 200