import uuid
from app import db, create_app
from app.models import CultureSite, Facility, Review, User

app = create_app()

def seed_database():
    with app.app_context():
        db.create_all()

        test_user = User.query.first()
        if not test_user:
            test_user = User(
                id=uuid.uuid4(), # type: ignore
                username="laksmana", # type: ignore
                email="laksmana@example.com" # type: ignore
            )
            db.session.add(test_user)
            db.session.commit()

        facilities_data = {
            "ibadah": "Tempat Ibadah (Umum)",
            "mosque": "Masjid / Mushola",
            "church": "Gereja",
            "temple": "Candi / Pura / Vihara",
            "parking": "Area Parkir",
            "toilet": "Toilet / Kamar Mandi",
            "restaurant": "Kuliner / Warung / Resto",
            "camera": "Spot Foto / Selfie",
            "store": "Toko / Souvenir / UMKM",
            "wifi": "Akses WiFi / Internet",
            "atm": "Mesin ATM / Bank",
            "wheelchair": "Akses Kursi Roda",
            "info": "Pusat Informasi / Panduan",
            "medical": "Klinik / Pos P3K",
            "security": "Keamanan / Pos Jaga",
            "ticket": "Loket Tiket",
            "charging": "Stasiun Cas HP",
            "recreation": "Area Bermain Anak",
            "nature": "Wisata Alam / Pegunungan",
            "rest_area": "Saung / Gazebo / Pendopo",
            "museum": "Museum / Monumen / Sejarah",
            "cleanliness": "Tempat Sampah / Kebersihan",
            "no_entry": "Larangan / Area Terbatas",
            "guide": "Pemandu Wisata",
            "locker": "Loker / Penitipan Barang",
            "hotel": "Hotel / Penginapan / Homestay",
            "pool": "Kolam Renang / Pemandian",
            "shower": "Kamar Bilas / Ruang Ganti",
            "shuttle": "Shuttle / Mobil Wisata",
            "camping": "Camping Ground / Kemah",
            "garden": "Taman Bunga / Kebun",
            "fauna": "Area Satwa / Fauna",
            "library": "Perpustakaan / Ruang Baca",
            "viewpoint": "Gardu Pandang / Puncak",
            "stage": "Panggung Musik / Hiburan",
            "boat": "Sewa Perahu / Dermaga",
            "bridge": "Jembatan Gantung",
            "adventure": "Outbound / Petualangan"
        }

        db_facilities = {}
        for key, name in facilities_data.items():
            fac = Facility.query.filter_by(icon_key=key).first()
            if not fac:
                fac = Facility(id=uuid.uuid4(), nama_fasilitas=name, icon_key=key) # type: ignore
                db.session.add(fac)
            db_facilities[key] = fac
        db.session.commit()

        print("Penyedia data 38 master fasilitas sukses dijalankan!")

if __name__ == "__main__":
    seed_database()