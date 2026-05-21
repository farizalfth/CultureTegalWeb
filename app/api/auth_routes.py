import os
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.services.auth_controller import AuthController
from app.services.auth_service import supabase

auth_api = Blueprint('auth_api', __name__, url_prefix='/api/v1/auth')
base_dir = os.path.dirname(os.path.abspath(__file__))

@auth_api.route('/sync', methods=['POST'])
@swag_from(os.path.join(base_dir, 'docs/sync.yml'))
def sync_user():
    token = None
    if 'Authorization' in request.headers:
        parts = request.headers['Authorization'].split()
        if len(parts) == 2 and parts[0] == 'Bearer':
            token = parts[1]
    
    if not token:
        return jsonify({"status": "error", "message": "Token is missing"}), 401

    try:
        user_response = supabase.auth.get_user(token)
        current_user = user_response.user # type: ignore
        
        data = request.json or {}
        nama = data.get('nama', current_user.user_metadata.get('full_name', current_user.email.split('@')[0])) # type: ignore
        provider = data.get('provider', 'email')
        profile_picture = data.get('profile_picture', current_user.user_metadata.get('avatar_url', None))
        
        result = AuthController.sync_user_data(
            user_id=current_user.id,
            email=current_user.email,
            nama=nama,
            provider=provider,
            profile_picture=profile_picture
        )
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 401