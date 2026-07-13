import os
import yaml
from flask import Blueprint, jsonify, request
from flasgger import swag_from
from app.models import Review
from app.services.culture_service import CultureService
from app.services.auth_service import token_required

culture_v1_bp = Blueprint('culture_v1', __name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
yml_path = os.path.abspath(os.path.join(base_dir, '..', 'docs', 'explore.yml'))

with open(yml_path, 'r', encoding='utf-8') as f:
    explore_specs = yaml.safe_load(f)

@culture_v1_bp.route('', methods=['GET'])
@token_required
@swag_from(explore_specs['get_cultures'])
def get_cultures(current_user):
    try:
        kategori = request.args.get('kategori', None)
        search = request.args.get('search', None)
        is_slider_raw = request.args.get('is_slider', None)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        is_slider = None
        if is_slider_raw is not None:
            is_slider = is_slider_raw.lower() == 'true'

        data = CultureService.get_paginated_cultures(
            kategori=kategori, 
            is_slider=is_slider, 
            search=search,
            page=page,
            per_page=per_page
        )
        
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
@swag_from(explore_specs['get_culture_detail'])
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
    
@culture_v1_bp.route('/<string:site_id>/reviews', methods=['POST'])
@token_required
@swag_from(explore_specs['add_review'])
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
@swag_from(explore_specs['update_review'])
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
@swag_from(explore_specs['delete_review'])
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
    
@culture_v1_bp.route('/<string:site_id>/reviews/list', methods=['GET'])
@token_required
@swag_from(explore_specs['get_site_reviews'])
def get_site_reviews(current_user, site_id):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        data = CultureService.get_paginated_reviews(site_id, page=page, per_page=per_page)
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

@culture_v1_bp.route('/wordcloud/<string:name>', methods=['GET'])
@token_required
@swag_from(explore_specs['get_culture_wordcloud'])
def get_culture_wordcloud(current_user, name):
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