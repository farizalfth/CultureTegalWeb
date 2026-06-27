import logging
import uuid
import os
import base64
import time
import json
from flask import request, current_app
from app import db
from app.models import UMKM
from app.models import Review
from app.models import User
from app.services.upload_service import delete_file

def get_full_url(path):
    if not path:
        return ""
    if path.startswith('http://') or path.startswith('https://'):
        return path
    clean_path = path.lstrip('/')
    return f"{request.host_url}static/uploads/{clean_path}"

def save_base64_image(base64_str):
    if not base64_str:
        return None
    try:
        if ',' in base64_str:
            base64_str = base64_str.split(',', 1)[1]
        img_data = base64.b64decode(base64_str)
        filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_review.png"
        
        upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'review')
        os.makedirs(upload_path, exist_ok=True)
        
        with open(os.path.join(upload_path, filename), 'wb') as f:
            f.write(img_data)
            
        return f"review/{filename}"
    except Exception as e:
        logging.error(f"Error saving base64 image: {str(e)}")
        return None

def parse_review_images(review_image_str):
    if not review_image_str:
        return []
    try:
        parsed = json.loads(review_image_str)
        if isinstance(parsed, list):
            return parsed
        return [review_image_str]
    except Exception:
        return [review_image_str]

class UMKMService:
    @staticmethod
    def get_all_umkm_paginated(category=None, search=None, sort=None, page=1, per_page=10):
        try:
            query = UMKM.query
            if category and category != 'Semua':
                query = query.filter_by(kategori=category)
            
            if search:
                query = query.filter(UMKM.nama_produk.ilike(f"%{search}%"))
                
            if sort == 'Termurah':
                query = query.order_by(db.func.cast(db.func.replace(UMKM.harga, '.', ''), db.Integer).asc())
            elif sort == 'Termahal':
                query = query.order_by(db.func.cast(db.func.replace(UMKM.harga, '.', ''), db.Integer).desc())
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'items': [item.to_dict() for item in pagination.items],
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        except Exception as e:
            logging.error(f"Error fetching paginated umkms: {str(e)}")
            raise e

    @staticmethod
    def get_umkm_by_id(umkm_id):
        try:
            item = UMKM.query.get(umkm_id)
            if not item:
                return None
            return item.to_dict()
        except Exception as e:
            logging.error(f"Error fetching umkm by id {umkm_id}: {str(e)}")
            raise e

    @staticmethod
    def add_umkm_review(user_id, umkm_id, rating, komentar, images_base64=None):
        try:
            umkm = UMKM.query.get(umkm_id)
            if not umkm:
                return False, "Produk UMKM tidak ditemukan"
            
            saved_filenames = []
            if isinstance(images_base64, list):
                for img_b64 in images_base64[:3]:
                    filename = save_base64_image(img_b64)
                    if filename:
                        saved_filenames.append(filename)
            
            review_image_data = json.dumps(saved_filenames) if saved_filenames else None

            new_review = Review(
                id=uuid.uuid4(), # type: ignore
                user_id=user_id,# type: ignore
                target_type="umkm",# type: ignore
                target_id=umkm.id,# type: ignore
                rating=rating,# type: ignore
                komentar=komentar,# type: ignore
                review_image=review_image_data# type: ignore
            )
            
            db.session.add(new_review)
            db.session.commit()
            return True, "Ulasan berhasil ditambahkan"
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding UMKM review: {str(e)}")
            return False, str(e)

    @staticmethod
    def update_umkm_review(user_id, umkm_id, rating, komentar, images_base64=None):
        try:
            review = Review.query.filter_by(
                user_id=user_id,
                target_type="umkm",
                target_id=umkm_id
            ).first()
            
            if not review:
                return False, "Ulasan tidak ditemukan"
                
            review.rating = rating
            review.komentar = komentar
            
            old_files = parse_review_images(review.review_image)
            new_files = []

            if isinstance(images_base64, list):
                for img in images_base64[:3]:
                    if img.startswith('http://') or img.startswith('https://'):
                        filename = img.split('/static/uploads/')[-1]
                        new_files.append(filename)
                    else:
                        filename = save_base64_image(img)
                        if filename:
                            new_files.append(filename)

                for old_f in old_files:
                    if old_f not in new_files:
                        delete_file(old_f)

                review.review_image = json.dumps(new_files) if new_files else None
            elif images_base64 is None:
                for old_f in old_files:
                    delete_file(old_f)
                review.review_image = None
                
            db.session.commit()
            return True, "Ulasan berhasil diperbarui"
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating UMKM review: {str(e)}")
            return False, str(e)

    @staticmethod
    def delete_umkm_review(user_id, umkm_id):
        try:
            review = Review.query.filter_by(
                user_id=user_id,
                target_type="umkm",
                target_id=umkm_id
            ).first()
            
            if not review:
                return False, "Ulasan tidak ditemukan"
                
            old_files = parse_review_images(review.review_image)
            for old_f in old_files:
                delete_file(old_f)

            db.session.delete(review)
            db.session.commit()
            return True, "Ulasan berhasil dihapus"
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting UMKM review: {str(e)}")
            return False, str(e)

    @staticmethod
    def get_umkm_reviews_paginated(umkm_id, page=1, per_page=5):
        statement = db.select(Review, User.nama, User.profile_picture)\
            .join(User, Review.user_id == User.id)\
            .filter(Review.target_type == 'umkm', Review.target_id == umkm_id)\
            .order_by(Review.created_at.desc())
        
        return db.paginate(statement, page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_paginated_reviews(umkm_id, page=1, per_page=10):
        try:
            query = Review.query.filter_by(
                target_type="umkm",
                target_id=umkm_id
            ).order_by(Review.created_at.desc())

            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            result = []
            for rev in pagination.items:
                user = User.query.get(rev.user_id)
                user_name = user.nama if (user and hasattr(user, 'nama')) else "Anonim"
                user_avatar = user.profile_picture if (user and hasattr(user, 'profile_picture') and user.profile_picture) else "https://i.pravatar.cc/150"

                img_paths = parse_review_images(rev.review_image)
                img_urls = [get_full_url(img) for img in img_paths]

                result.append({
                    "id": str(rev.id),
                    "user_id": str(rev.user_id),
                    "user_name": user_name,
                    "user_avatar": user_avatar,
                    "created_at": rev.created_at.isoformat() if rev.created_at else None,
                    "rating": float(rev.rating),
                    "komentar": rev.komentar,
                    "review_images": img_urls
                })

            return {
                "items": result,
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": pagination.page,
                "has_next": pagination.has_next
            }
        except Exception as e:
            logging.error(f"Error fetching paginated reviews: {str(e)}")
            raise e