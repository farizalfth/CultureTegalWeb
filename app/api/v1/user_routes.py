from flask import Blueprint, jsonify, request
import uuid
from app.models import db, ScanHistory, UserQuizHistory, UserFavorite
from app.services.auth_service import token_required
from app.services.user_service import UserService
from app.services.upload_service import save_image, delete_file

user_api = Blueprint('user_api', __name__)

@user_api.route('/profile', methods=['GET'])
@token_required
def get_profile(local_user):
    try:
        calculated_level = (local_user.poin // 1000) + 1
        if calculated_level > local_user.level:
            local_user.level = calculated_level
            db.session.commit()

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
                "profile_picture": profile_url,
                "points": formatted_poin,
                "level": calculated_level
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_api.route('/profile', methods=['PUT'])
@token_required
def update_profile(local_user):
    try:
        data = request.get_json()
        if not data or 'nama' not in data or 'no_telp' not in data:
            return jsonify({"status": "error", "message": "nama and no_telp are required"}), 400
        
        result, error = UserService.update_profile(local_user.id, data['nama'], data['no_telp'])
        if error:
            return jsonify({"status": "error", "message": error}), 400
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_api.route('/profile/picture', methods=['POST'])
@token_required
def update_profile_picture(local_user):
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"}), 400

        old_picture = local_user.profile_picture
        file_name = save_image(file)
        if not file_name:
            return jsonify({"status": "error", "message": "Failed to save image"}), 400

        result, error = UserService.update_profile_picture(local_user.id, file_name)
        if error:
            delete_file(file_name)
            return jsonify({"status": "error", "message": error}), 400
        
        if old_picture:
            delete_file(old_picture)
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_api.route('/favorites', methods=['GET'])
@token_required
def get_favorites(local_user):
    try:
        result, error = UserService.get_user_favorites(local_user.id)
        if error:
            return jsonify({"status": "error", "message": error}), 400
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_api.route('/favorites/toggle', methods=['POST'])
@token_required
def toggle_favorite(local_user):
    try:
        data = request.get_json()
        if not data or 'target_type' not in data or 'target_id' not in data:
            return jsonify({"status": "error", "message": "target_type and target_id are required"}), 400
        
        target_type = data['target_type']
        target_id = data['target_id']
        
        result, error = UserService.toggle_favorite(local_user.id, target_type, target_id)
        if error:
            return jsonify({"status": "error", "message": error}), 400
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_api.route('/badges', methods=['GET'])
@token_required
def get_badges(local_user):
    try:
        result, error = UserService.get_user_badges(local_user.id)
        if error:
            return jsonify({"status": "error", "message": error}), 400
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_api.route('/leaderboard', methods=['GET'])
@token_required
def get_leaderboard(local_user):
    try:
        result, error = UserService.get_leaderboard()
        if error:
            return jsonify({"status": "error", "message": error}), 400
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_api.route('/stats', methods=['GET'])
@token_required
def get_stats(local_user):
    try:
        result, error = UserService.get_user_stats(local_user.id)
        if error:
            return jsonify({"status": "error", "message": error}), 400
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_api.route('/scan-history', methods=['GET'])
@token_required
def get_scan_history(local_user):
    try:
        result, error = UserService.get_user_scan_history(local_user.id)
        if error:
            return jsonify({"status": "error", "message": error}), 400
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_api.route('/onesignal', methods=['POST'])
@token_required
def register_device(local_user):
    try:
        data = request.get_json()
        if not data or 'onesignal_id' not in data:
            return jsonify({"status": "error", "message": "onesignal_id is required"}), 400
        
        onesignal_id = data['onesignal_id']
        
        from app.models import UserDevice
        existing_device = UserDevice.query.filter_by(onesignal_id=onesignal_id).first()
        if existing_device:
            existing_device.user_id = local_user.id
        else:
            new_device = UserDevice()
            new_device.id = uuid.uuid4()
            new_device.user_id = local_user.id
            new_device.onesignal_id = onesignal_id
            db.session.add(new_device)
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Device registered successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_api.route('/onesignal/logout', methods=['POST'])
@token_required
def unregister_device(local_user):
    try:
        data = request.get_json()
        if not data or 'onesignal_id' not in data:
            return jsonify({"status": "error", "message": "onesignal_id is required"}), 400
        
        onesignal_id = data['onesignal_id']
        from app.models import UserDevice
        device = UserDevice.query.filter_by(user_id=local_user.id, onesignal_id=onesignal_id).first()
        if device:
            db.session.delete(device)
            db.session.commit()
        
        return jsonify({"status": "success", "message": "Device unregistered successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_api.route('/reset-progress', methods=['POST'])
@token_required
def reset_progress(local_user):
    try:
        db.session.query(ScanHistory).filter_by(user_id=local_user.id).delete()
        db.session.query(UserQuizHistory).filter_by(user_id=local_user.id).delete()
        db.session.query(UserFavorite).filter_by(user_id=local_user.id).delete()
        
        local_user.poin = 0
        local_user.total_xp = 0
        local_user.level = 1
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Progres akun berhasil di-reset seutuhnya!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500