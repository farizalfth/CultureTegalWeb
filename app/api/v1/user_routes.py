from flask import Blueprint, jsonify, request
from app.services.auth_service import token_required

user_api = Blueprint('user_api', __name__)

@user_api.route('/profile', methods=['GET'])
@token_required
def get_profile(local_user):
    try:
        formatted_poin = "{:,.0f}".format(local_user.poin).replace(',', '.')
        
        profile_url = local_user.profile_picture
        if profile_url:
            if not (profile_url.startswith('http://') or profile_url.startswith('https://')):
                base_host = request.host_url.rstrip('/')
                profile_url = f"{base_host}/static/uploads/{profile_url}"
                
        return jsonify({
            "status": "success",
            "data": {
                "id": str(local_user.id),
                "nama": local_user.nama,
                "email": local_user.email,
                "profile_picture": profile_url, # Mengembalikan URL lengkap yang siap pakai di Flutter
                "points": formatted_poin,
                "level": local_user.level
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500