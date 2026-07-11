import os
import uuid
from datetime import datetime, date, timedelta
from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, flash, jsonify
from realtime import Any
from sqlalchemy import func
from app.models import db, CultureSite, Event, UMKM, User, Facility, ScrapeTarget, ScanHistory
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.upload_service import delete_file, save_image
from app.services.auth_service import supabase
from app.services.scraper_service import ScraperService
from app.models import FoodMetadata, Badge, Quiz
from app.services.upload_service import save_video, delete_video
from app.services.notification_service import NotificationService
import re

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/appadministrator/admin')

def format_indo_date(start_str, end_str=None):
    if not start_str: return "-"
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    dt_start = datetime.strptime(start_str, '%Y-%m-%d')
    start_fmt = f"{days[dt_start.weekday()]}, {dt_start.day} {months[dt_start.month-1]}"
    
    if not end_str or start_str == end_str:
        return f"{start_fmt} {dt_start.year}"
    
    dt_end = datetime.strptime(end_str, '%Y-%m-%d')
    if dt_start.month == dt_end.month and dt_start.year == dt_end.year:
        return f"{days[dt_start.weekday()]}, {dt_start.day} - {days[dt_end.weekday()]}, {dt_end.day} {months[dt_start.month-1]} {dt_start.year}"
    else:
        return f"{start_fmt} {dt_start.year} - {days[dt_end.weekday()]}, {dt_end.day} {months[dt_end.month-1]} {dt_end.year}"

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and password and user.password_hash and check_password_hash(user.password_hash, password) and user.role == 'admin':
            session.permanent = True
            session['logged_in'] = True
            session['user_id'] = str(user.id)
            session['nama'] = user.nama
            return redirect(url_for('admin_bp.admin_dashboard'))
        else:
            flash('Kredensial tidak valid.', 'danger')
            
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_bp.admin_login'))

@admin_bp.route('/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))

    user_created_at = getattr(User, 'created_at')

    user_growth_raw = db.session.query(
        func.cast(user_created_at, db.Date),
        func.count(User.id)
    ).filter(User.role == 'user').group_by(func.cast(user_created_at, db.Date)).order_by(func.cast(user_created_at, db.Date).asc()).all()

    user_growth_labels = [str(item[0]) for item in user_growth_raw]
    user_growth_data = [item[1] for item in user_growth_raw]

    top_visited_raw = db.session.query(
        CultureSite.nama_tempat,
        func.count(ScanHistory.id)
    ).join(ScanHistory, ScanHistory.site_id == CultureSite.id).group_by(CultureSite.nama_tempat).order_by(func.count(ScanHistory.id).desc()).limit(5).all()

    top_visited_labels = [item[0] for item in top_visited_raw]
    top_visited_data = [item[1] for item in top_visited_raw]

    level_dist_raw = db.session.query(
        User.level,
        func.count(User.id)
    ).filter(User.role == 'user').group_by(User.level).order_by(User.level.asc()).all()

    level_dist_labels = [f"Level {item[0]}" for item in level_dist_raw]
    level_dist_data = [item[1] for item in level_dist_raw]

    filter_target_id = request.args.get('filter_target_id', 'semua')
    review_sort = request.args.get('sort_review', 'terbaru')

    query_filter: dict[str, Any] = {"Ulasan": {"$ne": ""}}
    if filter_target_id != 'semua':
        query_filter["target_id"] = filter_target_id

    mongo_uri = os.getenv("MONGO_URI")
    scraped_reviews = []
    if mongo_uri:
        try:
            from pymongo import MongoClient
            client = MongoClient(mongo_uri)
            mongo_db = client['review_tempat_bersejarah_tegal']
            collection = mongo_db['reviews_data']
            
            cursor = collection.find(query_filter)
            
            if review_sort == 'terbaru':
                cursor = cursor.sort([("Tanggal_Review", -1), ("_id", -1)])
            elif review_sort == 'terlama':
                cursor = cursor.sort([("Tanggal_Review", 1), ("_id", 1)])
            elif review_sort == 'rating_tinggi':
                cursor = cursor.sort([("Rating", -1), ("_id", -1)])
            elif review_sort == 'rating_rendah':
                cursor = cursor.sort([("Rating", 1), ("_id", 1)])
                
            scraped_reviews = list(cursor.limit(100))
        except:
            pass

    data = {
        'budaya': CultureSite.query.order_by(CultureSite.id.desc()).all(),
        'events': Event.query.order_by(Event.id.desc()).all(),
        'umkm': UMKM.query.order_by(UMKM.id.desc()).all(),
        'users': User.query.order_by(User.id.desc()).all(),
        'facilities': Facility.query.order_by(Facility.nama_fasilitas.asc()).all(),
        'scrape_targets': ScrapeTarget.query.order_by(ScrapeTarget.created_at.desc()).all(),
        'scraped_reviews': scraped_reviews,
        'count_budaya': CultureSite.query.count(),
        'count_event': Event.query.count(),
        'count_umkm': UMKM.query.count(),
        'count_users': User.query.count(),
        'user_growth_labels': user_growth_labels,
        'user_growth_data': user_growth_data,
        'top_visited_labels': top_visited_labels,
        'top_visited_data': top_visited_data,
        'level_dist_labels': level_dist_labels,
        'level_dist_data': level_dist_data
    }
    return render_template('admin/dashboard.html', **data)


@admin_bp.route('/add_budaya', methods=['POST'])
def add_budaya():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))

    gallery_files = request.files.getlist('gallery_images')
    gallery_list = [save_image(f) for f in gallery_files if f.filename != '']

    try:
        new_site = CultureSite()
        new_site.id = uuid.uuid4() # type: ignore
        new_site.nama_tempat = request.form.get('nama_tempat') # type: ignore
        new_site.subtitle = request.form.get('subtitle') # type: ignore
        new_site.kategori = request.form.get('kategori') # type: ignore
        new_site.tahun_dibangun = request.form.get('tahun_dibangun') # type: ignore
        new_site.lokasi_singkat = request.form.get('lokasi_singkat') # type: ignore
        new_site.durasi_kunjungan = request.form.get('durasi_kunjungan') # type: ignore
        new_site.jarak_estimasi = request.form.get('jarak_estimasi') # type: ignore
        new_site.deskripsi = request.form.get('deskripsi') # type: ignore
        new_site.fun_fact = request.form.get('fun_fact') # type: ignore
        new_site.latitude = float(request.form.get('latitude') or 0) # type: ignore
        new_site.longitude = float(request.form.get('longitude') or 0) # type: ignore
        new_site.image_url = save_image(request.files.get('gambar_utama')) # type: ignore
        new_site.gallery = gallery_list # type: ignore
        new_site.video_url = request.form.get('video_url') # type: ignore
        new_site.is_slider = True if request.form.get('is_slider') == 'on' else False # type: ignore
        new_site.admin_id = session.get('user_id') # type: ignore
        
        facility_ids = request.form.getlist('facilities')
        for f_id in facility_ids:
            fac = Facility.query.get(f_id)
            if fac:
                new_site.facilities.append(fac)

        db.session.add(new_site)
        db.session.commit()

        NotificationService.send_to_all(
            "Destinasi Budaya Baru!",
            f"Ayo jelajahi dan kunjungi tempat bersejarah baru: {new_site.nama_tempat}!"
        )

        flash('Data berhasil disimpan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin_bp.admin_dashboard', _anchor='budaya'))

@admin_bp.route('/update_budaya/<uuid:id>', methods=['POST'])
def update_budaya(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))

    site = CultureSite.query.get_or_404(id)
    try:
        site.nama_tempat = request.form.get('nama_tempat') or site.nama_tempat
        site.subtitle = request.form.get('subtitle')
        site.kategori = request.form.get('kategori') or site.kategori
        site.tahun_dibangun = request.form.get('tahun_dibangun')
        site.durasi_kunjungan = request.form.get('durasi_kunjungan')
        site.jarak_estimasi = request.form.get('jarak_estimasi')
        site.deskripsi = request.form.get('deskripsi') or site.deskripsi
        site.fun_fact = request.form.get('fun_fact')
        site.latitude = float(request.form.get('latitude') or site.latitude) # type: ignore
        site.longitude = float(request.form.get('longitude') or site.longitude) # type: ignore
        site.video_url = request.form.get('video_url')
        site.is_slider = True if request.form.get('is_slider') == 'on' else False

        file_utama = request.files.get('gambar_utama')
        if file_utama and file_utama.filename != '':
            delete_file(site.image_url)
            site.image_url = save_image(file_utama)

        gallery_files = request.files.getlist('gallery_images')
        new_gallery_pics = [save_image(f) for f in gallery_files if f.filename != '']
        if new_gallery_pics:
            current_gallery = list(site.gallery) if site.gallery else []
            site.gallery = current_gallery + new_gallery_pics

        site.facilities.clear()
        facility_ids = request.form.getlist('facilities')
        for f_id in facility_ids:
            fac = Facility.query.get(f_id)
            if fac:
                site.facilities.append(fac)

        db.session.commit()
        flash('Data berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal memperbarui: {str(e)}', 'danger')

    return redirect(url_for('admin_bp.admin_dashboard', _anchor='budaya'))

@admin_bp.route('/delete_gallery_img/<uuid:id>/<path:filename>', methods=['DELETE'])
def delete_gallery_img(id, filename):
    if not session.get('logged_in'):
        return {"status": "error", "message": "Sesi berakhir, silakan login ulang"}, 401
    
    site = CultureSite.query.get_or_404(id)
    if site.gallery and filename in site.gallery:
        updated_gallery = [img for img in site.gallery if img != filename]
        site.gallery = updated_gallery
        
        try:
            db.session.commit()
            delete_file(filename)
            return {"status": "success", "message": "Gambar berhasil dihapus"}, 200
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": str(e)}, 500
    
    return {"status": "error", "message": "Gambar tidak ditemukan dalam galeri"}, 404

@admin_bp.route('/delete_budaya/<uuid:id>')
def delete_budaya(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    site = CultureSite.query.get_or_404(id)
    try:
        delete_file(site.image_url)
        if site.gallery:
            for img in site.gallery:
                delete_file(img)
        db.session.delete(site)
        db.session.commit()
        flash('Data dan file terkait dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='budaya'))

@admin_bp.route('/add_event', methods=['POST'])
def add_event():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    
    start_date = request.form.get('tanggal_mulai')
    end_date = request.form.get('tanggal_selesai')
    start_t = request.form.get('jam_mulai')
    end_t = request.form.get('jam_selesai')
    
    h_names = request.form.getlist('h_name[]')
    h_icons = request.form.getlist('h_icon[]')
    highlights_data = [{"name": n, "icon": i} for n, i in zip(h_names, h_icons) if n]

    try:
        new_event = Event()
        new_event.id = uuid.uuid4() # type: ignore
        new_event.judul_event = request.form.get('judul_event') # type: ignore
        new_event.kategori = request.form.get('kategori') # type: ignore
        new_event.status = request.form.get('status') # type: ignore
        new_event.tanggal_lengkap = format_indo_date(start_date, end_date) # type: ignore
        new_event.raw_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None # type: ignore
        new_event.raw_end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None # type: ignore
        new_event.waktu_pelaksanaan = f"{start_t} - {end_t} WIB" # type: ignore
        new_event.lokasi_singkat = request.form.get('lokasi_singkat') # type: ignore
        new_event.alamat_lengkap = request.form.get('alamat_lengkap') # type: ignore
        new_event.audience = request.form.get('audience') # type: ignore
        new_event.harga_tiket = request.form.get('harga_tiket') # type: ignore
        new_event.deskripsi = request.form.get('deskripsi') # type: ignore
        new_event.highlights = highlights_data # type: ignore
        new_event.latitude = float(request.form.get('latitude') or 0) # type: ignore
        new_event.longitude = float(request.form.get('longitude') or 0) # type: ignore
        new_event.image_url = save_image(request.files.get('gambar_event')) # type: ignore
        new_event.is_recurring = True if request.form.get('is_recurring') == 'on' else False # type: ignore
        new_event.badge_top = request.form.get('badge_top') # type: ignore
        new_event.badge_bottom = request.form.get('badge_bottom') # type: ignore
        new_event.admin_id = session.get('user_id') # type: ignore
        
        db.session.add(new_event)
        db.session.commit()

        NotificationService.send_to_all(
        "Event Budaya Baru!",
         f"Jangan lewatkan keseruan event '{new_event.judul_event}' pada {new_event.tanggal_lengkap}!"
        )
        flash('Event berhasil diterbitkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='event'))

@admin_bp.route('/update_event/<uuid:id>', methods=['POST'])
def update_event(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    
    event = Event.query.get_or_404(id)
    start_date = request.form.get('tanggal_mulai')
    end_date = request.form.get('tanggal_selesai')
    start_t = request.form.get('jam_mulai')
    end_t = request.form.get('jam_selesai')
    
    try:
        if start_date:
            event.raw_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            event.raw_end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else event.raw_date
            event.tanggal_lengkap = format_indo_date(start_date, end_date)
        
        if start_t and end_t:
            event.waktu_pelaksanaan = f"{start_t} - {end_t} WIB"

        event.judul_event = request.form.get('judul_event') or event.judul_event
        event.kategori = request.form.get('kategori') or event.kategori
        event.status = request.form.get('status') or event.status
        event.lokasi_singkat = request.form.get('lokasi_singkat') or event.lokasi_singkat
        event.alamat_lengkap = request.form.get('alamat_lengkap') or event.alamat_lengkap
        event.audience = request.form.get('audience') or event.audience
        event.harga_tiket = request.form.get('harga_tiket') or event.harga_tiket
        event.deskripsi = request.form.get('deskripsi') or event.deskripsi
        event.latitude = float(request.form.get('latitude') or event.latitude) # type: ignore
        event.longitude = float(request.form.get('longitude') or event.longitude) # type: ignore
        event.badge_top = request.form.get('badge_top') or event.badge_top
        event.badge_bottom = request.form.get('badge_bottom') or event.badge_bottom
        event.is_recurring = True if request.form.get('is_recurring') == 'on' else False

        file = request.files.get('gambar_event')
        if file and file.filename != '':
            delete_file(event.image_url)
            event.image_url = save_image(file)

        db.session.commit()
        flash('Data event berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal: {str(e)}', 'danger')
    
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='event'))

@admin_bp.route('/delete_event/<uuid:id>')
def delete_event(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    event = Event.query.get_or_404(id)
    try:
        delete_file(event.image_url)
        db.session.delete(event)
        db.session.commit()
        flash('Event dihapus permanen.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='event'))

@admin_bp.route('/add_umkm', methods=['POST'])
def add_umkm():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))

    try:
        lat_val = request.form.get('latitude')
        lng_val = request.form.get('longitude')

        new_umkm = UMKM()
        new_umkm.id = uuid.uuid4() # type: ignore
        new_umkm.nama_produk = request.form.get('nama_produk') # type: ignore
        new_umkm.harga = request.form.get('harga') # type: ignore
        new_umkm.nama_toko = request.form.get('nama_toko') # type: ignore
        new_umkm.kategori = request.form.get('kategori') # type: ignore
        new_umkm.rating = float(request.form.get('rating', 0)) # type: ignore
        new_umkm.deskripsi = request.form.get('deskripsi') # type: ignore
        new_umkm.alamat_toko = request.form.get('alamat_toko') # type: ignore
        new_umkm.no_whatsapp = request.form.get('no_whatsapp') # type: ignore
        new_umkm.link_eksternal = request.form.get('link_eksternal') # type: ignore
        new_umkm.latitude = float(lat_val) if lat_val else None # type: ignore
        new_umkm.longitude = float(lng_val) if lng_val else None # type: ignore
        new_umkm.image_url = save_image(request.files.get('gambar_umkm')) # type: ignore
        new_umkm.admin_id = session.get('user_id') # type: ignore
        
        db.session.add(new_umkm)
        db.session.commit()

        NotificationService.send_to_all(
        "Kuliner & Toko Baru!",
        f"Telah hadir '{new_umkm.nama_produk}' di {new_umkm.nama_toko}. Yuk intip detailnya!"
        )
        flash('Produk UMKM berhasil ditambahkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin_bp.admin_dashboard', _anchor='umkm'))

@admin_bp.route('/update_umkm/<uuid:id>', methods=['POST'])
def update_umkm(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))

    umkm = UMKM.query.get_or_404(id)
    try:
        umkm.nama_produk = request.form.get('nama_produk') or umkm.nama_produk
        umkm.harga = request.form.get('harga') or umkm.harga
        umkm.nama_toko = request.form.get('nama_toko') or umkm.nama_toko
        umkm.kategori = request.form.get('kategori') or umkm.kategori
        umkm.rating = float(request.form.get('rating') or umkm.rating) # type: ignore
        umkm.deskripsi = request.form.get('deskripsi') or umkm.deskripsi
        umkm.alamat_toko = request.form.get('alamat_toko') or umkm.alamat_toko
        umkm.no_whatsapp = request.form.get('no_whatsapp') or umkm.no_whatsapp
        umkm.link_eksternal = request.form.get('link_eksternal') or umkm.link_eksternal
        
        lat_val = request.form.get('latitude')
        lng_val = request.form.get('longitude')
        umkm.latitude = float(lat_val) if lat_val else None # type: ignore
        umkm.longitude = float(lng_val) if lng_val else None # type: ignore

        file = request.files.get('gambar_umkm')
        if file and file.filename != '':
            delete_file(umkm.image_url)
            umkm.image_url = save_image(file)

        db.session.commit()
        flash('Data UMKM diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal memperbarui: {str(e)}', 'danger')

    return redirect(url_for('admin_bp.admin_dashboard', _anchor='umkm'))

@admin_bp.route('/delete_umkm/<uuid:id>')
def delete_umkm(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    umkm = UMKM.query.get_or_404(id)
    try:
        delete_file(umkm.image_url)
        db.session.delete(umkm)
        db.session.commit()
        flash('Data UMKM dihapus permanen.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='umkm'))

@admin_bp.route('/add_user', methods=['POST'])
def add_user():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))

    email = request.form.get('email')
    if User.query.filter_by(email=email).first():
        flash('Email sudah terdaftar.', 'danger')
        return redirect(url_for('admin_bp.admin_dashboard', _anchor='users'))

    try:
        new_user = User()
        new_user.id = uuid.uuid4() # type: ignore
        new_user.nama = request.form.get('nama') # type: ignore
        new_user.email = email # type: ignore
        new_user.password_hash = generate_password_hash(request.form.get('password', '')) # type: ignore
        new_user.role = 'admin' # type: ignore
        new_user.profile_picture = save_image(request.files.get('profile_picture')) # type: ignore
        
        db.session.add(new_user)
        db.session.commit()
        flash('Admin baru berhasil didaftarkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin_bp.admin_dashboard', _anchor='users'))

@admin_bp.route('/update_user/<uuid:id>', methods=['POST'])
def update_user(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))

    user = User.query.get_or_404(id)
    try:
        user.nama = request.form.get('nama') or user.nama
        user.email = request.form.get('email') or user.email
        
        if user.role == 'user':
            user.poin = int(request.form.get('poin', 0)) # type: ignore
            user.total_xp = int(request.form.get('total_xp', 0)) # type: ignore
            user.level = int(request.form.get('level', 1)) # type: ignore
            user.is_banned = True if request.form.get('is_banned') == 'on' else False # type: ignore
        
        if user.role == 'admin':
            new_pass = request.form.get('password')
            if new_pass:
                user.password_hash = generate_password_hash(new_pass)

        file = request.files.get('profile_picture')
        if file and file.filename != '':
            delete_file(user.profile_picture)
            user.profile_picture = save_image(file)

        db.session.commit()
        flash('Profil user berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal: {str(e)}', 'danger')

    return redirect(url_for('admin_bp.admin_dashboard', _anchor='users'))

@admin_bp.route('/delete_user/<uuid:id>')
def delete_user(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    
    if str(id) == session.get('user_id'):
        flash('Anda tidak dapat menghapus akun Anda sendiri.', 'warning')
        return redirect(url_for('admin_bp.admin_dashboard', _anchor='users'))

    user = User.query.get_or_404(id)
    try:
        supabase.auth.admin.delete_user(str(id))
        delete_file(user.profile_picture)
        db.session.delete(user)
        db.session.commit()
        flash('Akun berhasil dihapus sepenuhnya dari database dan autentikasi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus sepenuhnya: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='users'))

@admin_bp.route('/add_facility', methods=['POST'])
def add_facility():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    try:
        new_fac = Facility()
        new_fac.id = uuid.uuid4() # type: ignore
        new_fac.nama_fasilitas = request.form.get('nama_fasilitas') # type: ignore
        new_fac.icon_key = request.form.get('icon_key') # type: ignore
        
        db.session.add(new_fac)
        db.session.commit()
        flash('Fasilitas baru berhasil ditambahkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='budaya'))

@admin_bp.route('/add_scrape_target', methods=['POST'])
def add_scrape_target():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    
    url_maps = request.form.get('url_maps', '').strip()
    if not ScraperService.validate_url(url_maps):
        flash('Pola URL Google Maps tidak valid.', 'danger')
        return redirect(url_for('admin_bp.admin_dashboard', _anchor='scraper'))

    composite = request.form.get('target_composite', '')
    parts = composite.split('|')
    if len(parts) != 3:
        flash('Format pilihan target tidak valid.', 'danger')
        return redirect(url_for('admin_bp.admin_dashboard', _anchor='scraper'))

    target_type = parts[0]
    target_id_str = parts[1]
    nama_tempat = parts[2]
    target_id = uuid.UUID(target_id_str)

    existing = ScrapeTarget.query.filter_by(target_id=target_id).first()
    if existing:
        flash('Target ini sudah terdaftar sebelumnya.', 'warning')
        return redirect(url_for('admin_bp.admin_dashboard', _anchor='scraper'))

    max_reviews_str = request.form.get('max_reviews', '100').strip()
    max_reviews = int(max_reviews_str) if max_reviews_str.isdigit() else 100

    try:
        new_target = ScrapeTarget()
        new_target.id = uuid.uuid4() # type: ignore
        new_target.target_id = target_id # type: ignore
        new_target.target_type = target_type # type: ignore
        new_target.nama_tempat = nama_tempat # type: ignore
        new_target.url_maps = url_maps # type: ignore
        new_target.max_reviews = max_reviews # type: ignore
        
        db.session.add(new_target)
        db.session.commit()
        flash('Target scraping berhasil ditambahkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='scraper'))

@admin_bp.route('/scrape-targets/bulk-upload', methods=['POST'])
def bulk_upload_targets():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    
    if 'file' not in request.files:
        flash('File tidak ditemukan.', 'danger')
        return redirect(url_for('admin_bp.admin_dashboard', _anchor='scraper'))
        
    file = request.files['file']
    if file.filename == '':
        flash('Tidak ada file yang dipilih.', 'danger')
        return redirect(url_for('admin_bp.admin_dashboard', _anchor='scraper'))
        
    if not file.filename.endswith('.txt'): # type: ignore
        flash('Hanya mendukung file format .txt.', 'danger')
        return redirect(url_for('admin_bp.admin_dashboard', _anchor='scraper'))

    try:
        content = file.read().decode('utf-8')
        lines = content.splitlines()
        added_count = 0
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            url_index = line_str.find('http')
            if url_index == -1:
                continue
                
            url = line_str[url_index:].strip()
            name_str = line_str[:url_index].strip()
            
            name_str = re.sub(r'^\d+[\.\s\-)]*', '', name_str).strip()
            name_str = re.sub(r'[:\-,\s]*$', '', name_str).strip()
            
            if not name_str or not ScraperService.validate_url(url):
                continue

            clean_search = re.sub(r'[^a-zA-Z0-9]', '', name_str).lower()

            site = CultureSite.query.filter(
                func.lower(func.regexp_replace(CultureSite.nama_tempat, '[^a-zA-Z0-9]', '', 'g')).like(clean_search)
            ).first()
            
            if site:
                target_type = "culture"
                target_id = site.id
                nama_tempat = site.nama_tempat
            else:
                umkm = UMKM.query.filter(
                    func.lower(func.regexp_replace(UMKM.nama_produk, '[^a-zA-Z0-9]', '', 'g')).like(clean_search)
                ).first()
                
                if umkm:
                    target_type = "umkm"
                    target_id = umkm.id
                    nama_tempat = umkm.nama_produk
                else:
                    continue

            existing = ScrapeTarget.query.filter_by(target_id=target_id).first()
            if existing:
                continue

            new_target = ScrapeTarget()
            new_target.id = uuid.uuid4() # type: ignore
            new_target.target_id = target_id # type: ignore
            new_target.target_type = target_type # type: ignore
            new_target.nama_tempat = nama_tempat # type: ignore
            new_target.url_maps = url # type: ignore
            db.session.add(new_target)
            added_count += 1
            
        db.session.commit()
        flash(f'Berhasil mengimpor {added_count} target dari file.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='scraper'))

@admin_bp.route('/delete_scrape_target/<uuid:id>')
def delete_scrape_target(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    target = ScrapeTarget.query.get_or_404(id)
    try:
        db.session.delete(target)
        db.session.commit()
        flash('Target scraping berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus target: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='scraper'))

@admin_bp.route('/scrape/trigger', methods=['POST'])
def trigger_scrape():
    if not session.get('logged_in'):
        return {"status": "error", "message": "Unauthorized"}, 401
    
    mongo_uri = current_app.config.get('MONGO_URI') # type: ignore
    if ScraperService.progress["running"]:
        return {"status": "error", "message": "Scraping sedang berjalan di latar belakang"}, 400
    
    ScraperService.run_scraping_job(mongo_uri) # type: ignore
    return {"status": "success", "message": "Scraping dimulai di latar belakang"}, 200

@admin_bp.route('/scrape/status', methods=['GET'])
def get_scrape_status():
    if not session.get('logged_in'):
        return {"status": "error", "message": "Unauthorized"}, 401
    return {"status": "success", "data": ScraperService.progress}, 200


@admin_bp.route('/add_food_metadata', methods=['POST'])
def add_food_metadata():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    try:
        video_file = request.files.get('video_file')
        video_url = None
        if video_file and video_file.filename != '':
            video_url = save_video(video_file)
        else:
            video_url = request.form.get('video_url')

        new_food = FoodMetadata()
        new_food.id = uuid.uuid4() # type: ignore
        new_food.label_key = request.form.get('label_key') # type: ignore
        new_food.nama_makanan = request.form.get('nama_makanan') # type: ignore
        new_food.deskripsi = request.form.get('deskripsi') # type: ignore
        new_food.video_url = video_url # type: ignore

        db.session.add(new_food)
        db.session.commit()
        flash('Metadata makanan tradisional berhasil disimpan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='food'))

@admin_bp.route('/update_food_metadata/<uuid:id>', methods=['POST'])
def update_food_metadata(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    food = FoodMetadata.query.get_or_404(id)
    try:
        food.label_key = request.form.get('label_key') or food.label_key
        food.nama_makanan = request.form.get('nama_makanan') or food.nama_makanan
        food.deskripsi = request.form.get('deskripsi') or food.deskripsi

        video_file = request.files.get('video_file')
        if video_file and video_file.filename != '':
            if food.video_url and not food.video_url.startswith(('http://', 'https://')):
                delete_video(food.video_url)
            food.video_url = save_video(video_file)
        elif request.form.get('video_url'):
            food.video_url = request.form.get('video_url')

        db.session.commit()
        flash('Metadata makanan berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='food'))

@admin_bp.route('/delete_food_metadata/<uuid:id>')
def delete_food_metadata(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    food = FoodMetadata.query.get_or_404(id)
    try:
        if food.video_url and not food.video_url.startswith(('http://', 'https://')):
            delete_video(food.video_url)
        db.session.delete(food)
        db.session.commit()
        flash('Metadata makanan berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='food'))

@admin_bp.route('/add_badge', methods=['POST'])
def add_badge():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    try:
        new_badge = Badge()
        new_badge.id = uuid.uuid4() # type: ignore
        new_badge.nama_badge = request.form.get('nama_badge') # type: ignore
        new_badge.deskripsi = request.form.get('deskripsi') # type: ignore
        new_badge.syarat_poin = int(request.form.get('syarat_poin') or 0) # type: ignore
        new_badge.image_url = save_image(request.files.get('badge_image')) # type: ignore

        db.session.add(new_badge)
        db.session.commit()
        flash('Lencana baru berhasil didaftarkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='badges'))

@admin_bp.route('/delete_badge/<uuid:id>')
def delete_badge(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    badge = Badge.query.get_or_404(id)
    try:
        delete_file(badge.image_url)
        db.session.delete(badge)
        db.session.commit()
        flash('Lencana berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='badges'))

@admin_bp.route('/add_quiz', methods=['POST'])
def add_quiz():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    try:
        culture_id_str = request.form.get('culture_id')
        culture_id = uuid.UUID(culture_id_str) if culture_id_str else None

        opsi_a = request.form.get('opsi_a', '')
        opsi_b = request.form.get('opsi_b', '')
        opsi_c = request.form.get('opsi_c', '')
        opsi_d = request.form.get('opsi_d', '')
        opsi_jawaban = {"A": opsi_a, "B": opsi_b, "C": opsi_c, "D": opsi_d}

        new_quiz = Quiz()
        new_quiz.id = uuid.uuid4() # type: ignore
        new_quiz.culture_id = culture_id # type: ignore
        new_quiz.pertanyaan = request.form.get('pertanyaan') # type: ignore
        new_quiz.opsi_jawaban = opsi_jawaban # type: ignore
        new_quiz.jawaban_benar = request.form.get('jawaban_benar') # type: ignore
        new_quiz.poin_reward = int(request.form.get('poin_reward') or 50) # type: ignore
        new_quiz.image_url = save_image(request.files.get('quiz_image')) # type: ignore
        new_quiz.admin_id = session.get('user_id') # type: ignore

        db.session.add(new_quiz)
        db.session.commit()
        flash('Soal kuis baru berhasil ditambahkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='quiz'))

@admin_bp.route('/delete_quiz/<uuid:id>')
def delete_quiz(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))
    quiz = Quiz.query.get_or_404(id)
    try:
        if quiz.image_url:
            delete_file(quiz.image_url)
        db.session.delete(quiz)
        db.session.commit()
        flash('Soal kuis berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='quiz'))

