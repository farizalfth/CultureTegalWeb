import logging
import uuid
import os
import base64
import time
import json
from flask import request, current_app
from app import db
from app.models import CultureSite, Facility, Review, User
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

class CultureService:
    @staticmethod
    def get_all_cultures(kategori=None, is_slider=None):
        try:
            query = CultureSite.query

            if kategori and kategori != "Semua":
                query = query.filter(CultureSite.kategori.ilike(kategori))

            if is_slider is not None:
                query = query.filter_by(is_slider=is_slider)

            sites = query.all()
            result = []

            for site in sites:
                result.append(CultureService._serialize_site(site))

            return result
        except Exception as e:
            logging.error(f"Error fetching cultures: {str(e)}")
            raise e

    @staticmethod
    def get_culture_by_id(site_id):
        try:
            site = CultureSite.query.get(site_id)
            if not site:
                return None
            return CultureService._serialize_site(site)
        except Exception as e:
            logging.error(f"Error fetching culture by id {site_id}: {str(e)}")
            raise e

    @staticmethod
    def _serialize_site(site):
        serialized_facilities = []
        for fac in site.facilities:
            serialized_facilities.append({
                "id": str(fac.id),
                "nama_fasilitas": fac.nama_fasilitas,
                "icon_key": fac.icon_key
            })

        serialized_reviews = []
        try:
            reviews = Review.query.filter_by(
                target_type="culture_site",
                target_id=site.id
            ).order_by(Review.created_at.desc()).all()

            for rev in reviews:
                user = User.query.get(rev.user_id)
                user_name = user.nama if (user and hasattr(user, 'nama')) else "Anonim"
                user_avatar = user.profile_picture if (user and hasattr(user, 'profile_picture') and user.profile_picture) else "https://i.pravatar.cc/150"

                img_paths = parse_review_images(rev.review_image)
                img_urls = [get_full_url(img) for img in img_paths]

                serialized_reviews.append({
                    "id": str(rev.id),
                    "user_id": str(rev.user_id),
                    "user_name": user_name,
                    "user_avatar": user_avatar,
                    "created_at": rev.created_at.isoformat() if rev.created_at else None,
                    "rating": float(rev.rating),
                    "komentar": rev.komentar,
                    "review_images": img_urls
                })
        except Exception as rev_err:
            logging.warning(f"Gagal memuat ulasan untuk site {site.id}: {str(rev_err)}")

        gallery_urls = []
        if isinstance(site.gallery, list):
            for img in site.gallery:
                gallery_urls.append(get_full_url(img))

        try:
            for rev_data in serialized_reviews:
                if rev_data["review_images"] and isinstance(rev_data["review_images"], list):
                    for r_img in rev_data["review_images"]:
                        gallery_urls.append(r_img)
        except Exception:
            pass

        return {
            "id": str(site.id),
            "nama_tempat": site.nama_tempat or "Tempat Budaya Tegal",
            "subtitle": site.subtitle or "Warisan Sejarah & Budaya Lokal Kota Tegal",
            "kategori": site.kategori or "Sejarah",
            "tahun_dibangun": site.tahun_dibangun or "Tidak diketahui",
            "lokasi_singkat": site.lokasi_singkat or "Kota Tegal",
            "durasi_kunjungan": site.durasi_kunjungan or "30-60 mnt",
            "jarak_estimasi": site.jarak_estimasi or "0.0 km",
            "deskripsi": site.deskripsi or "Deskripsi lengkap mengenai tempat budaya ini belum tersedia saat ini.",
            "fun_fact": site.fun_fact or "Tempat ini menyimpan nilai luhur yang dijaga oleh masyarakat Kota Tegal.",
            "latitude": site.latitude if site.latitude is not None else 0.0,
            "longitude": site.longitude if site.longitude is not None else 0.0,
            "image_url": get_full_url(site.image_url),
            "gallery": gallery_urls,
            "video_url": get_full_url(site.video_url) if site.video_url else None,
            "is_slider": site.is_slider if site.is_slider is not None else False,
            "facilities": serialized_facilities,
            "reviews": serialized_reviews
        }

    @staticmethod
    def add_culture_review(user_id, site_id, rating, komentar, images_base64=None):
        try:
            site = CultureSite.query.get(site_id)
            if not site:
                return False, "Tempat budaya tidak ditemukan"
            
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
                target_type="culture_site",# type: ignore
                target_id=site.id,# type: ignore
                rating=rating,# type: ignore
                komentar=komentar,# type: ignore
                review_image=review_image_data# type: ignore
            )
            
            db.session.add(new_review)
            db.session.commit()
            return True, "Ulasan sukses ditambahkan"
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding review: {str(e)}")
            return False, str(e)

    @staticmethod
    def update_culture_review(user_id, site_id, rating, komentar, images_base64=None):
        try:
            review = Review.query.filter_by(
                user_id=user_id,
                target_type="culture_site",
                target_id=site_id
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
            logging.error(f"Error updating review: {str(e)}")
            return False, str(e)

    @staticmethod
    def delete_culture_review(user_id, site_id):
        try:
            review = Review.query.filter_by(
                user_id=user_id,
                target_type="culture_site",
                target_id=site_id
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
            logging.error(f"Error deleting review: {str(e)}")
            return False, str(e)