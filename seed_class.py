# import uuid
# from app import db, create_app
# from app.models import Badge

# app = create_app()

# def seed_missions():
#     with app.app_context():
#         missions = [
#             {"nama": "Mata Elang", "desc": "Membaca 1 detail objek budaya untuk pertama kalinya.", "poin": 10},
#             {"nama": "Pengamat Budaya", "desc": "Membaca 5 detail objek budaya yang berbeda.", "poin": 50},
#             {"nama": "Pelestari Sejarah", "desc": "Menuntaskan bacaan pada 10 objek budaya Kota Tegal.", "poin": 150},
#             {"nama": "Langkah Pasti", "desc": "Melakukan verifikasi kunjungan fisik di 2 lokasi bersejarah.", "poin": 250},
#             {"nama": "Jejak Bersejarah", "desc": "Berhasil memverifikasi kehadiran di 3 lokasi budaya berbeda.", "poin": 400},
#             {"nama": "Suara Rakyat", "desc": "Memberikan ulasan rill pertama pada objek budaya atau UMKM.", "poin": 20},
#             {"nama": "Teknologi Bahari", "desc": "Menggunakan fitur AI Scan untuk mendeteksi makanan tradisional.", "poin": 60},
#             {"nama": "Identitas Baru", "desc": "Berhasil memperbarui foto profil untuk memperkuat identitas diri.", "poin": 15},
#             {"nama": "Kelelawar Malam", "desc": "Mengaktifkan mode gelap (Dark Mode) untuk kenyamanan mata.", "poin": 5}
#         ]

#         added = 0
#         for m in missions:
#             exists = Badge.query.filter_by(nama_badge=m["nama"]).first()
#             if not exists:
#                 new_badge = Badge(
#                     id=uuid.uuid4(),
#                     nama_badge=m["nama"],
#                     deskripsi=m["desc"],
#                     image_url="badges/default_mission.png",
#                     syarat_poin=m["poin"]
#                 )
#                 db.session.add(new_badge)
#                 added += 1
        
#         db.session.commit()
#         print(f"Sukses menambahkan {added} misi lencana baru ke database!")

# if __name__ == "__main__":
#     seed_missions()