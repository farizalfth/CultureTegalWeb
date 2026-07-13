import os
import yaml
from flask import Blueprint, jsonify, request
from flasgger import swag_from
from app.models import Review
from app.services.umkm_service import UMKMService
from app.services.auth_service import token_required

umkm_v1_bp = Blueprint('umkm_v1', __name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
yml_path = os.path.abspath(os.path.join(base_dir, '..', 'docs', 'umkms.yml'))

with open(yml_path, 'r', encoding='utf-8') as f:
    umkm_specs = yaml.safe_load(f)

@umkm_v1_bp.route('', methods=['GET'])
@token_required
@swag_from(umkm_specs['get_all_umkm'])
def get_all_umkm(current_user):
    try:
        category = request.args.get('kategori', 'Semua')
        search = request.args.get('search', None)
        sort = request.args.get('sort', None)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        data = UMKMService.get_all_umkm_paginated(category, search, sort, page, per_page)
        
        return jsonify({
            "status": "success",
            "message": "Data UMKM berhasil dimuat",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Terjadi kesalahan internal pada server",
            "error": str(e)
        }), 500

@umkm_v1_bp.route('/<string:umkm_id>', methods=['GET'])
@token_required
@swag_from(umkm_specs['get_umkm_detail'])
def get_umkm_detail(current_user, umkm_id):
    try:
        data = UMKMService.get_umkm_by_id(umkm_id)
        if not data:
            return jsonify({
                "status": "fail",
                "message": "Produk UMKM tidak ditemukan"
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

@umkm_v1_bp.route('/<string:umkm_id>/reviews', methods=['POST'])
@token_required
@swag_from(umkm_specs['add_review'])
def add_review(current_user, umkm_id):
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
            target_type="umkm",
            target_id=umkm_id
        ).first()
        
        if existing_review:
            return jsonify({
                "status": "error",
                "message": "Anda sudah memberikan ulasan untuk tempat ini. Silakan gunakan fitur edit."
            }), 400
            
        success, message = UMKMService.add_umkm_review(
            user_id=current_user.id,
            umkm_id=umkm_id,
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

@umkm_v1_bp.route('/<string:umkm_id>/reviews', methods=['PUT'])
@token_required
@swag_from(umkm_specs['update_review'])
def update_review(current_user, umkm_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Data tidak boleh kosong"}), 400
            
        rating = data.get('rating')
        komentar = data.get('komentar')
        images_base64 = data.get('review_images_base64', [])
        
        if rating is None or not komentar:
            return jsonify({"status": "error", "message": "Rating dan komentar wajib diisi"}), 400
            
        success, message = UMKMService.update_umkm_review(
            user_id=current_user.id,
            umkm_id=umkm_id,
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

@umkm_v1_bp.route('/<string:umkm_id>/reviews', methods=['DELETE'])
@token_required
@swag_from(umkm_specs['delete_review'])
def delete_review(current_user, umkm_id):
    try:
        success, message = UMKMService.delete_umkm_review(
            user_id=current_user.id,
            umkm_id=umkm_id
        )
        
        if not success:
            return jsonify({"status": "error", "message": message}), 400
            
        return jsonify({
            "status": "success",
            "message": "Ulasan berhasil dihapus"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@umkm_v1_bp.route('/<string:umkm_id>/reviews/list', methods=['GET'])
@token_required
@swag_from(umkm_specs['get_umkm_reviews'])
def get_umkm_reviews(current_user, umkm_id):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        data = UMKMService.get_paginated_reviews(umkm_id, page=page, per_page=per_page)
        return jsonify({
            "status": "success",
            "message": "Data ulasan berhasil dimuat",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Terjadi kesalahan internal pada server",
            "error": str(e)
        }), 500

@umkm_v1_bp.route('/wordcloud/<string:name>', methods=['GET'])
@token_required
@swag_from(umkm_specs['get_umkm_wordcloud'])
def get_umkm_wordcloud(current_user, name):
    try:
        mongo_uri = os.getenv('MONGO_URI')
        from app.services.scraper_service import ScraperService
        
        data = ScraperService.get_word_frequencies(name, mongo_uri)
        return jsonify({
            "status": "success",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500