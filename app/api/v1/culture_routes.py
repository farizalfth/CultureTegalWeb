from flask import Blueprint, jsonify, request
from app.models import Review
from app.services.culture_service import CultureService
from app.services.auth_service import token_required

culture_v1_bp = Blueprint('culture_v1', __name__)

@culture_v1_bp.route('', methods=['GET'])
@token_required
def get_cultures(current_user):
    try:
        kategori = request.args.get('kategori', None)
        is_slider_raw = request.args.get('is_slider', None)
        
        is_slider = None
        if is_slider_raw is not None:
            is_slider = is_slider_raw.lower() == 'true'

        data = CultureService.get_all_cultures(kategori=kategori, is_slider=is_slider)
        
        return jsonify({
            "status": "success",
            "message": "Data tempat budaya berhasil dimuat",
            "data": data
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Terjadi kesalahan internal pada server",
            "error": str(e)
        }), 500

@culture_v1_bp.route('/<string:site_id>', methods=['GET'])
@token_required
def get_culture_detail(current_user, site_id):
    try:
        data = CultureService.get_culture_by_id(site_id)
        if not data:
            return jsonify({
                "status": "fail",
                "message": "Tempat budaya tidak ditemukan"
            }), 404
            
        return jsonify({
            "status": "success",
            "data": data
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Terjadi kesalahan internal pada server",
            "error": str(e)
        }), 500
    
# app/api/v1/culture_routes.py

# ... sesuaikan bagian metode add_review dan update_review sebagai berikut:

@culture_v1_bp.route('/<string:site_id>/reviews', methods=['POST'])
@token_required
def add_review(current_user, site_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Data tidak boleh kosong"}), 400
            
        rating = data.get('rating')
        komentar = data.get('komentar')
        images_base64 = data.get('review_images_base64', [])
        
        if rating is None or not komentar:
            return jsonify({"status": "error", "message": "Rating dan komentar wajib diisi"}), 400

        existing_review = Review.query.filter_by(
            user_id=current_user.id,
            target_type="culture_site",
            target_id=site_id
        ).first()
        
        if existing_review:
            return jsonify({
                "status": "error",
                "message": "Anda sudah memberikan ulasan untuk tempat ini. Silakan gunakan fitur edit."
            }), 400
            
        success, message = CultureService.add_culture_review(
            user_id=current_user.id,
            site_id=site_id,
            rating=float(rating),
            komentar=komentar,
            images_base64=images_base64
        )
        
        if not success:
            return jsonify({"status": "error", "message": message}), 400
            
        return jsonify({
            "status": "success",
            "message": "Ulasan berhasil dikirim"
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@culture_v1_bp.route('/<string:site_id>/reviews', methods=['PUT'])
@token_required
def update_review(current_user, site_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Data tidak boleh kosong"}), 400
            
        rating = data.get('rating')
        komentar = data.get('komentar')
        images_base64 = data.get('review_images_base64', [])
        
        if rating is None or not komentar:
            return jsonify({"status": "error", "message": "Rating dan komentar wajib diisi"}), 400
            
        success, message = CultureService.update_culture_review(
            user_id=current_user.id,
            site_id=site_id,
            rating=float(rating),
            komentar=komentar,
            images_base64=images_base64
        )
        
        if not success:
            return jsonify({"status": "error", "message": message}), 400
            
        return jsonify({
            "status": "success",
            "message": "Ulasan berhasil diperbarui"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@culture_v1_bp.route('/<string:site_id>/reviews', methods=['DELETE'])
@token_required
def delete_review(current_user, site_id):
    try:
        success, message = CultureService.delete_culture_review(
            user_id=current_user.id,
            site_id=site_id
        )
        
        if not success:
            return jsonify({"status": "error", "message": message}), 400
            
        return jsonify({
            "status": "success",
            "message": "Ulasan berhasil dihapus"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500