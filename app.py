from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'tegal_culture_secret'

# --- CONFIGURASI UPLOAD GAMBAR ---
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
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return 'default.jpg'

# --- 1. KONFIGURASI DATABASE ---
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

# --- 2. ROUTES: HALAMAN PUBLIK ---

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

# --- 3. ROUTES: AUTHENTICATION ---

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
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

# --- 4. ROUTES: ADMIN DASHBOARD ---

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    data = {'budaya': [], 'events': [], 'umkm': [], 'users': []} # Default kosong
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # AMBIL DATA BUDAYA
            cursor.execute("SELECT * FROM budaya ORDER BY id DESC")
            data['budaya'] = cursor.fetchall()
            
            # AMBIL DATA EVENT, UMKM, DLL
            cursor.execute("SELECT * FROM events ORDER BY id DESC")
            data['events'] = cursor.fetchall()
            cursor.execute("SELECT * FROM umkm ORDER BY id DESC")
            data['umkm'] = cursor.fetchall()
            cursor.execute("SELECT * FROM users ORDER BY id DESC")
            data['users'] = cursor.fetchall()

            # HITUNG TOTAL (Untuk Kartu Statistik)
            data['count_budaya'] = len(data['budaya'])
            data['count_event'] = len(data['events'])
            data['count_umkm'] = len(data['umkm'])
            data['count_users'] = len(data['users'])
            
            cursor.close()
        except Exception as e:
            print(f"Error Database: {e}")
        finally:
            conn.close() # WAJIB ditutup agar server tidak hang
            
    return render_template('admin.html', **data)

# --- CRUD: TAMBAH DATA ---

@app.route('/admin/add_budaya', methods=['POST'])
def add_budaya():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    file = request.files.get('gambar')
    filename = save_image(file) # Pastikan fungsi save_image sudah ada di app.py Anda
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO budaya (nama, kategori, wilayah, gambar) VALUES (%s, %s, %s, %s)", 
                       (request.form['nama'], request.form['kategori'], request.form['wilayah'], filename))
        conn.commit()
        flash('Data Budaya Berhasil Disimpan!', 'success')
    except Exception as e:
        flash(f'Gagal: {str(e)}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='budaya'))

@app.route('/admin/add_event', methods=['POST'])
def add_event():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    file = request.files.get('gambar')
    filename = save_image(file)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "INSERT INTO events (nama_event, tanggal, lokasi, status, gambar) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (request.form['nama_event'], request.form['tanggal'], request.form['lokasi'], request.form['status'], filename))
        conn.commit()
        flash('Event baru telah diterbitkan!', 'success')
    except Exception as e:
        flash(f'Gagal: {str(e)}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='event'))

@app.route('/admin/add_umkm', methods=['POST'])
def add_umkm():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    file = request.files.get('gambar')
    filename = save_image(file)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "INSERT INTO umkm (produk, pemilik, harga, rating, gambar) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (request.form['produk'], request.form['pemilik'], request.form['harga'], request.form['rating'], filename))
        conn.commit()
        flash('Produk UMKM berhasil didaftarkan!', 'success')
    except Exception as e:
        flash(f'Gagal: {str(e)}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='umkm'))

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    file = request.files.get('gambar')
    filename = save_image(file)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "INSERT INTO users (username, email, password, gambar) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (request.form['username'], request.form['email'], request.form['password'], filename))
        conn.commit()
        flash('Admin baru berhasil dibuat!', 'success')
    except Exception as e:
        flash(f'Gagal: {str(e)}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='users'))


# --- CRUD: HAPUS DATA ---

@app.route('/admin/delete_budaya/<int:id>')
def delete_budaya(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budaya WHERE id = %s", (id,))
        conn.commit()
        flash('Data Budaya dihapus.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='budaya'))

@app.route('/admin/delete_event/<int:id>')
def delete_event(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = %s", (id,))
        conn.commit()
        flash('Event dihapus.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='event'))

@app.route('/admin/delete_umkm/<int:id>')
def delete_umkm(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM umkm WHERE id = %s", (id,))
        conn.commit()
        flash('Produk UMKM dihapus.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='umkm'))

@app.route('/admin/delete_user/<int:id>')
def delete_user(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (id,))
        conn.commit()
        flash('User dihapus.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard', _anchor='users'))

# ==========================================
# 1. UPDATE BUDAYA
# ==========================================
@app.route('/admin/update_budaya/<int:id>', methods=['POST'])
def update_budaya(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    nama = request.form['nama']
    kategori = request.form['kategori']
    wilayah = request.form['wilayah']
    file = request.files.get('gambar')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if file and file.filename != '':
        filename = save_image(file) # Simpan gambar baru
        query = "UPDATE budaya SET nama=%s, kategori=%s, wilayah=%s, gambar=%s WHERE id=%s"
        cursor.execute(query, (nama, kategori, wilayah, filename, id))
    else:
        query = "UPDATE budaya SET nama=%s, kategori=%s, wilayah=%s WHERE id=%s"
        cursor.execute(query, (nama, kategori, wilayah, id))
        
    conn.commit()
    conn.close()
    flash('Data Budaya berhasil diperbarui!', 'success')
    return redirect(url_for('admin_dashboard', _anchor='budaya'))

# ==========================================
# 2. UPDATE EVENT
# ==========================================
@app.route('/admin/update_event/<int:id>', methods=['POST'])
def update_event(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    nama = request.form['nama_event']
    tgl = request.form['tanggal']
    lokasi = request.form['lokasi']
    status = request.form['status']
    file = request.files.get('gambar')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if file and file.filename != '':
        filename = save_image(file)
        query = "UPDATE events SET nama_event=%s, tanggal=%s, lokasi=%s, status=%s, gambar=%s WHERE id=%s"
        cursor.execute(query, (nama, tgl, lokasi, status, filename, id))
    else:
        query = "UPDATE events SET nama_event=%s, tanggal=%s, lokasi=%s, status=%s WHERE id=%s"
        cursor.execute(query, (nama, tgl, lokasi, status, id))
        
    conn.commit()
    conn.close()
    flash('Event berhasil diperbarui!', 'success')
    return redirect(url_for('admin_dashboard', _anchor='event'))

# ==========================================
# 3. UPDATE UMKM
# ==========================================
@app.route('/admin/update_umkm/<int:id>', methods=['POST'])
def update_umkm(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    produk = request.form['produk']
    pemilik = request.form['pemilik']
    harga = request.form['harga']
    rating = request.form['rating']
    file = request.files.get('gambar')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if file and file.filename != '':
        filename = save_image(file)
        query = "UPDATE umkm SET produk=%s, pemilik=%s, harga=%s, rating=%s, gambar=%s WHERE id=%s"
        cursor.execute(query, (produk, pemilik, harga, rating, filename, id))
    else:
        query = "UPDATE umkm SET produk=%s, pemilik=%s, harga=%s, rating=%s WHERE id=%s"
        cursor.execute(query, (produk, pemilik, harga, rating, id))
        
    conn.commit()
    conn.close()
    flash('Produk UMKM berhasil diperbarui!', 'success')
    return redirect(url_for('admin_dashboard', _anchor='umkm'))

# ==========================================
# 4. UPDATE USER (ADMIN)
# ==========================================
@app.route('/admin/update_user/<int:id>', methods=['POST'])
def update_user(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    file = request.files.get('gambar')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if file and file.filename != '':
        filename = save_image(file)
        query = "UPDATE users SET username=%s, email=%s, password=%s, gambar=%s WHERE id=%s"
        cursor.execute(query, (username, email, password, filename, id))
    else:
        query = "UPDATE users SET username=%s, email=%s, password=%s WHERE id=%s"
        cursor.execute(query, (username, email, password, id))
        
    conn.commit()
    conn.close()
    flash('Profil User berhasil diperbarui!', 'success')
    return redirect(url_for('admin_dashboard', _anchor='users'))

if __name__ == '__main__':
    app.run(debug=True)