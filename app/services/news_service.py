import logging
from flask import request
from app import db
from app.models import News

class NewsService:
    @staticmethod
    def get_all_news(kategori=None):
        try:
            query = News.query
            if kategori and kategori != "Semua":
                query = query.filter(News.kategori.ilike(kategori))
            
            news_list = query.all()
            result = []
            for n in news_list:
                result.append(NewsService._serialize_news(n))
            return result
        except Exception as e:
            logging.error(f"Error fetching news: {str(e)}")
            raise e

    @staticmethod
    def _serialize_news(news):
        def get_full_url(path):
            if not path:
                return None
            if path.startswith('http://') or path.startswith('https://'):
                return path
            clean_path = path.lstrip('/')
            return f"{request.host_url}static/uploads/{clean_path}"

        months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        date_str = "-"
        if news.tanggal:
            date_str = f"{news.tanggal.day} {months[news.tanggal.month-1]} {news.tanggal.year}"

        return {
            "id": str(news.id),
            "title": news.judul,
            "category": news.kategori,
            "date": date_str,
            "image": get_full_url(news.image_url) if news.image_url else None,
            "content": news.konten
        }

    @staticmethod
    def get_paginated_news(kategori=None, page=1, per_page=10):
        try:
            query = News.query
            if kategori and kategori != "Semua":
                query = query.filter(News.kategori.ilike(kategori))
            
            query = query.order_by(News.tanggal.desc())
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            result = []
            for n in pagination.items:
                result.append(NewsService._serialize_news(n))
                
            return {
                "items": result,
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": pagination.page,
                "has_next": pagination.has_next
            }
        except Exception as e:
            logging.error(f"Error fetching paginated news: {str(e)}")
            raise e