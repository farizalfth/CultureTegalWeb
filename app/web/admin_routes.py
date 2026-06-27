import os
import uuid
from datetime import datetime, date, timedelta
from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, flash
from app.models import db, CultureSite, Event, UMKM, User, Facility
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.upload_service import delete_file, save_image
from app.services.auth_service import supabase

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
    data = {
        'budaya': CultureSite.query.order_by(CultureSite.id.desc()).all(),
        'events': Event.query.order_by(Event.id.desc()).all(),
        'umkm': UMKM.query.order_by(UMKM.id.desc()).all(),
        'users': User.query.order_by(User.id.desc()).all(),
        'facilities': Facility.query.order_by(Facility.nama_fasilitas.asc()).all(),
        'count_budaya': CultureSite.query.count(),
        'count_event': Event.query.count(),
        'count_umkm': UMKM.query.count(),
        'count_users': User.query.count()
    }
    return render_template('admin/dashboard.html', **data)

@admin_bp.route('/add_budaya', methods=['POST'])
def add_budaya():
    if not session.get('logged_in'):
        return redirect(url_for('admin_bp.admin_login'))

    gallery_files = request.files.getlist('gallery_images')
    gallery_list = [save_image(f) for f in gallery_files if f.filename != '']

    try:
        new_site = CultureSite(
            id=uuid.uuid4(),# type: ignore
            nama_tempat=request.form.get('nama_tempat'),# type: ignore
            subtitle=request.form.get('subtitle'),# type: ignore
            kategori=request.form.get('kategori'),# type: ignore
            tahun_dibangun=request.form.get('tahun_dibangun'),# type: ignore
            lokasi_singkat=request.form.get('lokasi_singkat'),# type: ignore
            durasi_kunjungan=request.form.get('durasi_kunjungan'),# type: ignore
            jarak_estimasi=request.form.get('jarak_estimasi'),# type: ignore
            deskripsi=request.form.get('deskripsi'),# type: ignore
            fun_fact=request.form.get('fun_fact'),# type: ignore
            latitude=float(request.form.get('latitude') or 0),# type: ignore
            longitude=float(request.form.get('longitude') or 0),# type: ignore
            image_url=save_image(request.files.get('gambar_utama')),# type: ignore
            gallery=gallery_list,# type: ignore
            video_url=request.form.get('video_url'),# type: ignore
            is_slider=True if request.form.get('is_slider') == 'on' else False,# type: ignore
            admin_id=session.get('user_id')# type: ignore
        )
        
        facility_ids = request.form.getlist('facilities')
        for f_id in facility_ids:
            fac = Facility.query.get(f_id)
            if fac:
                new_site.facilities.append(fac)

        db.session.add(new_site)
        db.session.commit()
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
        site.latitude = float(request.form.get('latitude') or site.latitude)
        site.longitude = float(request.form.get('longitude') or site.longitude)
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
        new_event = Event(
            judul_event=request.form.get('judul_event'),# type: ignore
            kategori=request.form.get('kategori'),# type: ignore
            status=request.form.get('status'),# type: ignore
            tanggal_lengkap=format_indo_date(start_date, end_date),# type: ignore
            raw_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,# type: ignore
            raw_end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,# type: ignore
            waktu_pelaksanaan=f"{start_t} - {end_t} WIB",# type: ignore
            lokasi_singkat=request.form.get('lokasi_singkat'),# type: ignore
            alamat_lengkap=request.form.get('alamat_lengkap'),# type: ignore
            audience=request.form.get('audience'),# type: ignore
            harga_tiket=request.form.get('harga_tiket'),# type: ignore
            deskripsi=request.form.get('deskripsi'),# type: ignore
            highlights=highlights_data,# type: ignore
            latitude=float(request.form.get('latitude') or 0),# type: ignore
            longitude=float(request.form.get('longitude') or 0),# type: ignore
            image_url=save_image(request.files.get('gambar_event')),# type: ignore
            is_recurring=True if request.form.get('is_recurring') == 'on' else False,# type: ignore
            badge_top=request.form.get('badge_top'),# type: ignore
            badge_bottom=request.form.get('badge_bottom'),# type: ignore
            admin_id=session.get('user_id')# type: ignore
        )
        db.session.add(new_event)
        db.session.commit()
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
        event.latitude = float(request.form.get('latitude') or event.latitude)
        event.longitude = float(request.form.get('longitude') or event.longitude)
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
        # DITAMBAHKAN: Mengambil nilai koordinat dari form input
        lat_val = request.form.get('latitude')
        lng_val = request.form.get('longitude')

        new_umkm = UMKM(
            nama_produk=request.form.get('nama_produk'), # type: ignore
            harga=request.form.get('harga'),# type: ignore
            nama_toko=request.form.get('nama_toko'),# type: ignore
            kategori=request.form.get('kategori'),# type: ignore
            rating=float(request.form.get('rating', 0)),# type: ignore
            deskripsi=request.form.get('deskripsi'),# type: ignore
            alamat_toko=request.form.get('alamat_toko'),# type: ignore
            no_whatsapp=request.form.get('no_whatsapp'),# type: ignore
            link_eksternal=request.form.get('link_eksternal'),# type: ignore
            latitude=float(lat_val) if lat_val else None, # type: ignore
            longitude=float(lng_val) if lng_val else None, # type: ignore
            image_url=save_image(request.files.get('gambar_umkm')),# type: ignore
            admin_id=session.get('user_id')# type: ignore
        )
        db.session.add(new_umkm)
        db.session.commit()
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
        umkm.rating = float(request.form.get('rating') or umkm.rating)
        umkm.deskripsi = request.form.get('deskripsi') or umkm.deskripsi
        umkm.alamat_toko = request.form.get('alamat_toko') or umkm.alamat_toko
        umkm.no_whatsapp = request.form.get('no_whatsapp') or umkm.no_whatsapp
        umkm.link_eksternal = request.form.get('link_eksternal') or umkm.link_eksternal
        
        # DITAMBAHKAN: Melakukan pembaruan koordinat toko
        lat_val = request.form.get('latitude')
        lng_val = request.form.get('longitude')
        umkm.latitude = float(lat_val) if lat_val else None
        umkm.longitude = float(lng_val) if lng_val else None

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
        new_user = User(
            nama=request.form.get('nama'), # type: ignore
            email=email, # type: ignore
            password_hash=generate_password_hash(request.form.get('password', '')), # type: ignore
            role='admin', # type: ignore
            profile_picture=save_image(request.files.get('profile_picture')) # type: ignore
        )
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
            user.poin = int(request.form.get('poin', 0))
            user.total_xp = int(request.form.get('total_xp', 0))
            user.level = int(request.form.get('level', 1))
            user.is_banned = True if request.form.get('is_banned') == 'on' else False
        
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
        new_fac = Facility(
            id=uuid.uuid4(), # type: ignore
            nama_fasilitas=request.form.get('nama_fasilitas'), # type: ignore
            icon_key=request.form.get('icon_key') # type: ignore
        )
        db.session.add(new_fac)
        db.session.commit()
        flash('Fasilitas baru berhasil ditambahkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard', _anchor='budaya'))