import os
import yaml
from flask import Blueprint, jsonify, request
from flasgger import swag_from
from app.services.event_service import EventService
from app.services.auth_service import token_required

event_v1_bp = Blueprint('event_v1', __name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
yml_path = os.path.abspath(os.path.join(base_dir, '..', 'docs', 'events.yml'))

with open(yml_path, 'r', encoding='utf-8') as f:
    event_specs = yaml.safe_load(f)

@event_v1_bp.route('', methods=['GET'])
@token_required
@swag_from(event_specs['get_events_paginated'])
def get_events(current_user):
    try:
        kategori = request.args.get('kategori', None)
        status = request.args.get('status', None)
        search = request.args.get('search', None)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        data = EventService.get_paginated_events(
            kategori=kategori, 
            status=status, 
            search=search,
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