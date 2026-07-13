import os
import yaml
from flask import Blueprint, jsonify, request
from flasgger import swag_from
from app.services.news_service import NewsService
from app.services.auth_service import token_required

news_v1_bp = Blueprint('news_v1', __name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
yml_path = os.path.abspath(os.path.join(base_dir, '..', 'docs', 'news.yml'))

with open(yml_path, 'r', encoding='utf-8') as f:
    news_specs = yaml.safe_load(f)

@news_v1_bp.route('', methods=['GET'])
@token_required
@swag_from(news_specs['get_news'])
def get_news(current_user):
    try:
        kategori = request.args.get('kategori', None)
        search = request.args.get('search', None)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        data = NewsService.get_paginated_news(kategori=kategori, search=search, page=page, per_page=per_page)
        
        return jsonify({
            "status": "success",
            "message": "Data berita berhasil dimuat",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Terjadi kesalahan internal pada server",
            "error": str(e)
        }), 500