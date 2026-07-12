import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, JSONB
from flask import request, current_app
from sqlalchemy import func

db = SQLAlchemy()

culture_facilities = db.Table('culture_facilities',
    db.Column('culture_id', UUID(as_uuid=True), db.ForeignKey('culture_sites.id', ondelete='CASCADE'), primary_key=True),
    db.Column('facility_id', UUID(as_uuid=True), db.ForeignKey('facilities.id', ondelete='CASCADE'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    no_telp = db.Column(db.String(20), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    auth_provider = db.Column(db.String(50), default='email')
    poin = db.Column(db.Integer, default=0)
    total_xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    role = db.Column(db.String(20), default='user')
    onesignal_id = db.Column(db.String(255), nullable=True)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    reviews = db.relationship('Review', backref='user', cascade='all, delete-orphan', passive_deletes=True)
    favorites = db.relationship('UserFavorite', backref='user', cascade='all, delete-orphan', passive_deletes=True)
    scan_histories = db.relationship('ScanHistory', backref='user', cascade='all, delete-orphan', passive_deletes=True)
    badges = db.relationship('UserBadge', backref='user', cascade='all, delete-orphan', passive_deletes=True)
    quiz_histories = db.relationship('UserQuizHistory', backref='user', cascade='all, delete-orphan', passive_deletes=True)
    ai_scans = db.relationship('AIScanHistory', backref='user', cascade='all, delete-orphan', passive_deletes=True)
    devices = db.relationship('UserDevice', backref='user', cascade='all, delete-orphan', passive_deletes=True)

class CultureSite(db.Model):
    __tablename__ = 'culture_sites'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama_tempat = db.Column(db.String(150), nullable=False)
    subtitle = db.Column(db.String(150), nullable=True)
    kategori = db.Column(db.String(50), nullable=False)
    tahun_dibangun = db.Column(db.String(50), nullable=True)
    lokasi_singkat = db.Column(db.String(100), nullable=True)
    durasi_kunjungan = db.Column(db.String(50), nullable=True)
    jarak_estimasi = db.Column(db.String(50), nullable=True)
    deskripsi = db.Column(db.Text, nullable=False)
    fun_fact = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    gallery = db.Column(JSONB, nullable=True)
    video_url = db.Column(db.String(255), nullable=True)
    is_slider = db.Column(db.Boolean, default=False)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    facilities = db.relationship('Facility', secondary=culture_facilities, backref=db.backref('cultures', lazy='dynamic'))

class Facility(db.Model):
    __tablename__ = 'facilities'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama_fasilitas = db.Column(db.String(100), nullable=False)
    icon_key = db.Column(db.String(100), nullable=False)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    judul_event = db.Column(db.String(150), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    tanggal_lengkap = db.Column(db.String(100), nullable=False)
    raw_date = db.Column(db.Date, nullable=True)
    raw_end_date = db.Column(db.Date, nullable=True)
    waktu_pelaksanaan = db.Column(db.String(100), nullable=False)
    lokasi_singkat = db.Column(db.String(100), nullable=False)
    alamat_lengkap = db.Column(db.Text, nullable=False)
    audience = db.Column(db.String(100), nullable=False)
    harga_tiket = db.Column(db.String(50), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    highlights = db.Column(JSONB, nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    badge_top = db.Column(db.String(50), nullable=True)
    badge_bottom = db.Column(db.String(50), nullable=True)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

class UMKM(db.Model):
    __tablename__ = 'umkms'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama_produk = db.Column(db.String(150), nullable=False)
    harga = db.Column(db.String(50), nullable=False)
    nama_toko = db.Column(db.String(100), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Float, default=0.0)
    image_url = db.Column(db.String(255), nullable=True)
    deskripsi = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    alamat_toko = db.Column(db.Text, nullable=True)
    no_whatsapp = db.Column(db.String(20), nullable=True)
    link_eksternal = db.Column(db.String(255), nullable=True)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    def to_dict(self):
        image_url_full = None
        if self.image_url:
            if self.image_url.startswith(('http://', 'https://')):
                image_url_full = self.image_url
            else:
                try:
                    storage_type = current_app.config.get('STORAGE_TYPE', 'local')
                except RuntimeError:
                    storage_type = 'local'

                if storage_type == 'local':
                    try:
                        image_url_full = f"{request.host_url.rstrip('/')}/static/uploads/{self.image_url}"
                    except RuntimeError:
                        fallback_url = current_app.config.get('LOCAL_STORAGE_BASE_URL', '')
                        image_url_full = f"{fallback_url.rstrip('/')}/static/uploads/{self.image_url}"
                elif storage_type in ['s3', 'supabase']:
                    base_url = current_app.config.get('STORAGE_BASE_URL', '').rstrip('/')
                    image_url_full = f"{base_url}/{self.image_url}"

        avg_rating_query = db.session.query(func.avg(Review.rating), func.count(Review.id))\
            .filter(Review.target_type == 'umkm', Review.target_id == self.id).first()
            
        db_avg = avg_rating_query[0] if avg_rating_query and avg_rating_query[0] is not None else None
        review_count = avg_rating_query[1] if avg_rating_query else 0

        final_rating = round(db_avg, 1) if db_avg is not None else self.rating

        return {
            'id': str(self.id),
            'nama_produk': self.nama_produk,
            'harga': self.harga,
            'nama_toko': self.nama_toko,
            'kategori': self.kategori,
            'rating': final_rating, 
            'review_count': review_count, 
            'image_url': image_url_full, 
            'deskripsi': self.deskripsi,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'alamat_toko': self.alamat_toko,
            'no_whatsapp': self.no_whatsapp,
            'link_eksternal': self.link_eksternal,
            'admin_id': str(self.admin_id) if self.admin_id else None
        }

class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    judul = db.Column(db.String(200), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    konten = db.Column(db.Text, nullable=False)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    culture_id = db.Column(UUID(as_uuid=True), db.ForeignKey('culture_sites.id'), nullable=True)
    food_id = db.Column(UUID(as_uuid=True), db.ForeignKey('food_metadata.id', ondelete='SET NULL'), nullable=True)
    pertanyaan = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    opsi_jawaban = db.Column(JSONB, nullable=False)
    jawaban_benar = db.Column(db.String(10), nullable=False)
    poin_reward = db.Column(db.Integer, default=50)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

class ScanHistory(db.Model):
    __tablename__ = 'scan_history'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    site_id = db.Column(UUID(as_uuid=True), db.ForeignKey('culture_sites.id'), nullable=False)
    scan_method = db.Column(db.String(50), nullable=False)
    poin_didapat = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(UUID(as_uuid=True), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    komentar = db.Column(db.Text, nullable=False)
    review_image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class UserFavorite(db.Model):
    __tablename__ = 'user_favorites'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(UUID(as_uuid=True), nullable=False)
    reminder_1h_sent = db.Column(db.Boolean, default=False)
    reminder_start_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class Badge(db.Model):
    __tablename__ = 'badges'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama_badge = db.Column(db.String(100), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    syarat_poin = db.Column(db.Integer, nullable=False)

class UserBadge(db.Model):
    __tablename__ = 'user_badges'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    badge_id = db.Column(UUID(as_uuid=True), db.ForeignKey('badges.id'), nullable=False)
    unlocked_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class UserQuizHistory(db.Model):
    __tablename__ = 'user_quiz_history'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    quiz_id = db.Column(UUID(as_uuid=True), db.ForeignKey('quizzes.id'), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class FoodMetadata(db.Model):
    __tablename__ = 'food_metadata'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label_key = db.Column(db.String(100), unique=True, nullable=False)
    nama_makanan = db.Column(db.String(150), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class AIScanHistory(db.Model):
    __tablename__ = 'ai_scan_history'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    predicted_label = db.Column(db.String(100), nullable=False)
    food_id = db.Column(UUID(as_uuid=True), db.ForeignKey('food_metadata.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class ScrapeTarget(db.Model):
    __tablename__ = 'scrape_targets'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id = db.Column(UUID(as_uuid=True), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    nama_tempat = db.Column(db.String(150), nullable=False)
    url_maps = db.Column(db.Text, nullable=False)
    max_reviews = db.Column(db.Integer, default=100, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class UserDevice(db.Model):
    __tablename__ = 'user_devices'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    onesignal_id = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())