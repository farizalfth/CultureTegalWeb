from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tegal_culture_secret'

# --- 1. KONFIGURASI UPLOAD GAMBAR ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.root_path, 'static/uploads', filename))
        return filename
    return 'default.jpg'

# --- 2. KONFIGURASI DATABASE ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'tegalcultureweb'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Error Database: {e}")
        return None

# --- 3. HELPER: LOG AKTIVITAS ---
def add_log(pesan):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO logs (pesan) VALUES (%s)", (pesan,))
            conn.commit()
        finally:
            conn.close()

# --- 4. ROUTES: HALAMAN PUBLIK ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/jelajah')
def jelajah():
    conn = get_db_connection()
    items = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM budaya ORDER BY id DESC")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('jelajah.html', items=items)

@app.route('/event')
def event():
    conn = get_db_connection()
    events = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM events ORDER BY id DESC")
        events = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('event.html', events=events)

@app.route('/umkm')
def umkm_public():
    conn = get_db_connection()
    produks = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM umkm ORDER BY id DESC")
        produks = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('umkm.html', produks=produks)

# --- 5. ROUTES: AUTHENTICATION ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        if not conn:
            flash('Database mati! Periksa XAMPP.', 'danger')
            return render_template('login.html')
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            if user:
                session['logged_in'] = True
                session['username'] = user['username']
                add_log(f"Admin {user['username']} berhasil login.")
                flash(f'Selamat datang kembali, {user["username"]}!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Username atau Password salah!', 'danger')
        finally:
            cursor.close()
            conn.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    user = session.get('username')
    add_log(f"Admin {user} melakukan logout.")
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

# --- 6. ROUTES: ADMIN DASHBOARD (REAL-TIME DATA) ---

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    data = {
        'budaya': [], 'events': [], 'umkm': [], 'users': [], 'logs': [],
        'cat_data': [], 'dist_data': [],
        'count_budaya': 0, 'count_event': 0, 'count_umkm': 0, 'count_users': 0,
        'count_cowo': 0, 'count_cewe': 0
    }
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Ambil List Data Utama
            cursor.execute("SELECT * FROM budaya ORDER BY id DESC")
            data['budaya'] = cursor.fetchall()
            cursor.execute("SELECT * FROM events ORDER BY id DESC")
            data['events'] = cursor.fetchall()
            cursor.execute("SELECT * FROM umkm ORDER BY id DESC")
            data['umkm'] = cursor.fetchall()
            cursor.execute("SELECT * FROM users ORDER BY id DESC")
            data['users'] = cursor.fetchall()

            # Ambil Log Aktivitas (Terbaru 5)
            cursor.execute("SELECT * FROM logs ORDER BY waktu DESC LIMIT 5")
            data['logs'] = cursor.fetchall()

            # Statistik Kategori (Untuk Donut Chart)
            cursor.execute("SELECT kategori, COUNT(*) as total FROM budaya GROUP BY kategori")
            data['cat_data'] = cursor.fetchall()

            # Statistik Sebaran Wilayah (Untuk List/Map)
            cursor.execute("SELECT deskripsi as wilayah, COUNT(*) as total FROM budaya GROUP BY deskripsi")
            data['dist_data'] = cursor.fetchall()

            # Statistik Gender (Asumsi ada kolom gender di tabel users)
            cursor.execute("SELECT gender, COUNT(*) as total FROM users GROUP BY gender")
            genders = cursor.fetchall()
            for g in genders:
                if g['gender'] == 'Cowo': data['count_cowo'] = g['total']
                if g['gender'] == 'Cewe': data['count_cewe'] = g['total']

            # Total Counts
            data['count_budaya'] = len(data['budaya'])
            data['count_event'] = len(data['events'])
            data['count_umkm'] = len(data['umkm'])
            data['count_users'] = len(data['users'])
            
            cursor.close()
        except Exception as e:
            print(f"Error Dashboard: {e}")
        finally:
            conn.close()
            
    return render_template('admin.html', **data)

# --- 7. CRUD: TAMBAH DATA (WITH LOGS) ---

@app.route('/admin/add_budaya', methods=['POST'])
def add_budaya():
    if not session.get('logged_in'): return redirect(url_for('login'))
    nama = request.form.get('nama')
    file = request.files.get('gambar')
    filename = save_image(file)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "INSERT INTO budaya (nama, kategori, deskripsi, gambar, lat, lng) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (nama, request.form.get('kategori'), request.form.get('deskripsi'), filename, request.form.get('lat'), request.form.get('lng')))
        conn.commit()
        add_log(f"Menambahkan data budaya baru: {nama}")
        flash('Budaya berhasil ditambahkan!', 'success')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard') + '#budaya')

@app.route('/admin/add_event', methods=['POST'])
def add_event():
    if not session.get('logged_in'): return redirect(url_for('login'))
    nama = request.form.get('nama_event')
    filename = save_image(request.files.get('gambar'))
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "INSERT INTO events (nama_event, tanggal, lokasi, status, gambar) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (nama, request.form.get('tanggal'), request.form.get('lokasi'), request.form.get('status'), filename))
        conn.commit()
        add_log(f"Menerbitkan event baru: {nama}")
        flash('Event baru diterbitkan!', 'success')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='event'))

@app.route('/admin/add_umkm', methods=['POST'])
def add_umkm():
    if not session.get('logged_in'): return redirect(url_for('login'))
    nama = request.form.get('produk')
    filename = save_image(request.files.get('gambar'))
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "INSERT INTO umkm (produk, pemilik, harga, rating, gambar) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (nama, request.form.get('pemilik'), request.form.get('harga'), request.form.get('rating'), filename))
        conn.commit()
        add_log(f"Mendaftarkan produk UMKM: {nama}")
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='umkm'))

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if not session.get('logged_in'): return redirect(url_for('login'))
    user = request.form.get('username')
    filename = save_image(request.files.get('gambar'))
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "INSERT INTO users (username, email, password, gender, gambar) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (user, request.form.get('email'), request.form.get('password'), request.form.get('gender'), filename))
        conn.commit()
        add_log(f"Mendaftarkan admin baru: {user}")
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='users'))

# --- 8. CRUD: HAPUS DATA (WITH LOGS) ---

@app.route('/admin/delete_budaya/<int:id>')
def delete_budaya(id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budaya WHERE id = %s", (id,))
        conn.commit()
        add_log(f"Menghapus data budaya ID: {id}")
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='budaya'))

# (Serta rute delete_event, delete_umkm, delete_user serupa dengan penambahan add_log)

# --- 9. CRUD: UPDATE DATA ---

@app.route('/admin/update_budaya/<int:id>', methods=['POST'])
def update_budaya(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    nama = request.form.get('nama')
    file = request.files.get('gambar')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if file and file.filename != '':
            filename = save_image(file)
            query = "UPDATE budaya SET nama=%s, kategori=%s, deskripsi=%s, gambar=%s, lat=%s, lng=%s WHERE id=%s"
            cursor.execute(query, (nama, request.form.get('kategori'), request.form.get('deskripsi'), filename, request.form.get('lat'), request.form.get('lng'), id))
        else:
            query = "UPDATE budaya SET nama=%s, kategori=%s, deskripsi=%s, lat=%s, lng=%s WHERE id=%s"
            cursor.execute(query, (nama, request.form.get('kategori'), request.form.get('deskripsi'), request.form.get('lat'), request.form.get('lng'), id))
        conn.commit()
        add_log(f"Memperbarui data budaya: {nama}")
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard') + '#budaya')

# API KOORDINAT
@app.route('/get_coords/<kecamatan>')
def get_coords(kecamatan):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT latitude, longitude FROM ref_wilayah_tegal WHERE kecamatan = %s", (kecamatan,))
        result = cursor.fetchone()
        conn.close()
        return result if result else {"latitude": "0", "longitude": "0"}
    return {"latitude": "0", "longitude": "0"}

if __name__ == '__main__':
    app.run(debug=True)