from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'tegal_culture_secret'

# --- 1. KONFIGURASI DATABASE ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'tegalcultureweb'
}

def get_db_connection():
    """Fungsi untuk membuat koneksi ke database MySQL."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Error koneksi ke MySQL: {e}")
        return None

# --- 2. ROUTES: AUTHENTICATION (ADMIN) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn is None:
            flash('Gagal terhubung ke database. Pastikan XAMPP jalan.', 'danger')
            return render_template('login.html')

        cursor = conn.cursor(dictionary=True)
        # Ambil user berdasarkan username & password
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            flash(f'Selamat datang kembali, {user["username"]}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau Password salah!', 'danger')
            
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM budaya")
        data_budaya = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        data_budaya = [] # Jika DB mati, tampilkan list kosong

    return render_template('admin.html', budaya=data_budaya)

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

# --- 3. ROUTES: PUBLIC PAGES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/jelajah')
def jelajah():
    # Tips: Kedepannya, data ini bisa diambil dari tabel 'budaya' di database
    items = [
        {'id': 1, 'nama': 'Gereja Blenduk', 'kat': 'Sejarah', 'desc': 'Ikon bersejarah peninggalan kolonial Belanda.', 'img': 'gereja.jpg', 'color': 'warning'},
        {'id': 2, 'nama': 'Masjid Agung Tegal', 'kat': 'Sejarah', 'desc': 'Masjid megah dengan arsitektur khas Timur Tengah.', 'img': 'masjid.jpg', 'color': 'warning'},
        {'id': 3, 'nama': 'Klenteng Tek Hay Kiong', 'kat': 'Budaya', 'desc': 'Klenteng tertua di Tegal yang penuh nilai sejarah.', 'img': 'klenteng.jpg', 'color': 'success'},
        {'id': 4, 'nama': 'Batik Tegal', 'kat': 'Budaya', 'desc': 'Batik khas Tegal dengan motif Mega Mendung.', 'img': 'batik.jpg', 'color': 'success'},
        {'id': 5, 'nama': 'Pantai Alam Indah', 'kat': 'Alam', 'desc': 'Destinasi wisata bahari favorit di Tegal.', 'img': 'pai.jpg', 'color': 'info'},
        {'id': 6, 'nama': 'Soto Tauco', 'kat': 'Kuliner', 'desc': 'Kuliner khas Tegal dengan cita rasa tauco yang unik.', 'img': 'soto.jpg', 'color': 'danger'},
    ]
    return render_template('jelajah.html', items=items)

@app.route('/event')
def event():
    events = [
        {
            'nama': 'Festival Bahari Tegal',
            'tgl': '20 - 24 Mei 2024',
            'lokasi': 'Pantai Alam Indah, Tegal',
            'desc': 'Festival tahunan yang menampilkan berbagai atraksi budaya dan bahari.',
            'img': 'https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?auto=format&fit=crop&q=80&w=600'
        },
        {
            'nama': 'Kirab Budaya',
            'tgl': '15 Juni 2024',
            'lokasi': 'Jl. Pancasila, Tegal',
            'desc': 'Kirab budaya dengan berbagai pertunjukan seni tradisional.',
            'img': 'https://images.unsplash.com/photo-1514525253344-7624feaf68d5?auto=format&fit=crop&q=80&w=600'
        },
        {
            'nama': 'Pameran UMKM',
            'tgl': '5 - 7 Juli 2024',
            'lokasi': 'GOR Wisanggeni, Tegal',
            'desc': 'Pameran produk unggulan UMKM Kota Tegal.',
            'img': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&q=80&w=600'
        }
    ]
    return render_template('event.html', events=events)

@app.route('/umkm')
def umkm():
    produks = [
        {'nama': 'Batik Mega Mendung', 'rating': '4.8 (132)', 'harga': 'Rp 150.000', 'img': 'https://images.unsplash.com/photo-1610116303244-6239fdb23c05?auto=format&fit=crop&q=80&w=300'},
        {'nama': 'Keripik Tempe', 'rating': '4.6 (98)', 'harga': 'Rp 25.000', 'img': 'https://images.unsplash.com/photo-1603048588665-791ca8aea617?auto=format&fit=crop&q=80&w=300'},
        {'nama': 'Teh Poci', 'rating': '4.7 (110)', 'harga': 'Rp 20.000', 'img': 'https://images.unsplash.com/photo-1594631252845-29fc458695d6?auto=format&fit=crop&q=80&w=300'},
        {'nama': 'Tas Batik Tegal', 'rating': '4.9 (80)', 'harga': 'Rp 120.000', 'img': 'https://images.unsplash.com/photo-1591561954557-26941169b79e?auto=format&fit=crop&q=80&w=300'},
        {'nama': 'Kaos Tegal Culture', 'rating': '4.4 (75)', 'harga': 'Rp 75.000', 'img': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&q=80&w=300'},
        {'nama': 'Krupuk Rambak', 'rating': '4.5 (90)', 'harga': 'Rp 30.000', 'img': 'https://images.unsplash.com/photo-1600271886399-dc04a60f3396?auto=format&fit=crop&q=80&w=300'},
    ]
    return render_template('umkm.html', produks=produks)

@app.route('/tentang')
def tentang():
    return render_template('tentang.html')

# --- Kelola Budaya ---
@app.route('/admin/budaya')
def manage_budaya():
    if not session.get('logged_in'): return redirect(url_for('login'))
    # Query ambil data budaya saja
    return render_template('admin/manage_items.html', type="Budaya")

# --- Kelola Event ---
@app.route('/admin/event')
def manage_event():
    # Query ambil data event
    return render_template('admin/manage_items.html', type="Event")

# --- Pengaturan ---
@app.route('/admin/settings')
def admin_settings():
    return render_template('admin/settings.html')

# --- 4. MAIN RUNNER ---
if __name__ == '__main__':
    app.run(debug=True)