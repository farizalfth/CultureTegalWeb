from flask import Blueprint, jsonify, request
from app.services.event_service import EventService
from app.services.auth_service import token_required

event_v1_bp = Blueprint('event_v1', __name__)

@event_v1_bp.route('', methods=['GET'])
@token_required
def get_events(current_user):
    try:
        kategori = request.args.get('kategori', None)
        status = request.args.get('status', None)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        data = EventService.get_paginated_events(
            kategori=kategori, 
            status=status, 
            page=page, 
            per_page=per_page
        )
        return jsonify({
            "status": "success",
            "message": "Data event berhasil dimuat",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Terjadi kesalahan internal pada server",
            "error": str(e)
        }), 500