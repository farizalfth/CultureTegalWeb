import os
from flask import Blueprint, jsonify
from flasgger import swag_from
from app.models import CultureSite, Event, UMKM, User
from app.services.auth_service import token_required

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
base_dir = os.path.dirname(os.path.abspath(__file__))

@api_v1.route('/ping', methods=['GET'])
@swag_from(os.path.join(base_dir, 'docs/ping.yml'))
def ping():
    return jsonify({"status": "success", "message": "API v1 is active."}), 200

@api_v1.route('/cultures', methods=['GET'])
@swag_from(os.path.join(base_dir, 'docs/cultures.yml'))
@token_required
def get_cultures(current_user):
    try:
        cultures = CultureSite.query.all()
        data = []
        for c in cultures:
            data.append({
                "id": str(c.id),
                "title": c.nama_tempat,
                "subtitle": c.subtitle,
                "category": c.kategori,
                "image": c.image_url,
                "latitude": c.latitude,
                "longitude": c.longitude
            })
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_v1.route('/events', methods=['GET'])
@swag_from(os.path.join(base_dir, 'docs/events.yml'))
@token_required
def get_events(current_user):
    try:
        events = Event.query.all()
        data = []
        for e in events:
            data.append({
                "id": str(e.id),
                "title": e.judul_event,
                "category": e.kategori,
                "status": e.status,
                "date": e.tanggal_lengkap,
                "time": e.waktu_pelaksanaan,
                "location": e.lokasi_singkat,
                "address": e.alamat_lengkap,
                "image": e.image_url,
                "is_recurring": e.is_recurring
            })
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_v1.route('/umkms', methods=['GET'])
@swag_from(os.path.join(base_dir, 'docs/umkms.yml'))
@token_required
def get_umkms(current_user):
    try:
        umkms = UMKM.query.all()
        data = []
        for u in umkms:
            data.append({
                "id": str(u.id),
                "name": u.nama_produk,
                "price": u.harga,
                "store_name": u.nama_toko,
                "category": u.kategori,
                "rating": u.rating,
                "image": u.image_url,
                "no_whatsapp": u.no_whatsapp,
                "link_eksternal": u.link_eksternal
            })
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_v1.route('/profile', methods=['GET'])
@swag_from(os.path.join(base_dir, 'docs/profile.yml'))
@token_required
def get_profile(current_user):
    try:
        user_data = User.query.get(current_user.id)
        if not user_data:
            return jsonify({"status": "error", "message": "User profile not found in database"}), 404
            
        return jsonify({
            "status": "success",
            "data": {
                "id": str(user_data.id),
                "nama": user_data.nama,
                "email": user_data.email,
                "profile_picture": user_data.profile_picture,
                "points": user_data.poin,
                "total_xp": user_data.total_xp,
                "level": user_data.level
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

