# import uuid
# from app import create_app, db
# from app.models import CultureSite, Facility, Review, User

# app = create_app()

# def seed_database():
#     with app.app_context():
#         db.create_all()

#         test_user = User.query.first()
#         if not test_user:
#             test_user = User(
#                 id=uuid.uuid4(),
#                 username="laksmana",
#                 email="laksmana@example.com"
#             )
#             db.session.add(test_user)
#             db.session.commit()

#         facilities_data = {
#             "camera": "Spot Foto",
#             "parking": "Area Parkir",
#             "restaurant": "Area Makan",
#             "toilet": "Toilet Umum",
#             "store": "Toko Souvenir",
#             "mosque": "Tempat Ibadah"
#         }

#         db_facilities = {}
#         for key, name in facilities_data.items():
#             fac = Facility.query.filter_by(icon_key=key).first()
#             if not fac:
#                 fac = Facility(id=uuid.uuid4(), nama_fasilitas=name, icon_key=key)
#                 db.session.add(fac)
#             db_facilities[key] = fac
#         db.session.commit()

#         culture_sites_data = [
#             {
#                 "nama_tempat": "Klenteng Tek Hay Kiong",
#                 "subtitle": "Simbol Toleransi & Akulturasi",
#                 "kategori": "Tradisi",
#                 "tahun_dibangun": "Abad 17",
#                 "lokasi_singkat": "Tegal Barat",
#                 "durasi_kunjungan": "45-60 mnt",
#                 "jarak_estimasi": "1.2 km",
#                 "deskripsi": "Klenteng Tek Hay Kiong merupakan klenteng tertua di Kota Tegal yang didirikan pada abad ke-17. Bangunan ini tidak hanya menjadi tempat ibadah bagi umat Tri Dharma, tetapi juga menjadi simbol keharmonisan budaya dan toleransi yang sangat kuat di Kota Tegal. Arsitekturnya yang megah dipenuhi dengan ukiran-ukiran artistik khas Tionghoa kuno, dengan dominasi warna merah dan emas yang melambangkan keberuntungan serta kebahagiaan.",
#                 "fun_fact": "Nama 'Tek Hay Kiong' memiliki arti harfiah 'Istana Penenang Samudra'.",
#                 "latitude": -6.8642,
#                 "longitude": 109.1384,
#                 "is_slider": True,
#                 "image_url": "177196762_1.png",
#                 "gallery": ["177196762_4.png", "177196762_3.png"],
#                 "facility_keys": ["camera", "parking"],
#                 "review": "Tempat yang sangat tenang dan penuh nilai sejarah tinggi."
#             },
#             {
#                 "nama_tempat": "Gedung Birao (SCS)",
#                 "subtitle": "Lawang Sewunya Tegal",
#                 "kategori": "Sejarah",
#                 "tahun_dibangun": "1913",
#                 "lokasi_singkat": "Tegal Timur",
#                 "durasi_kunjungan": "30-45 mnt",
#                 "jarak_estimasi": "1.5 km",
#                 "deskripsi": "Gedung bersejarah peninggalan Belanda yang megah dengan arsitektur klasik yang masih terawat sangat baik hingga saat ini.",
#                 "fun_fact": "Gedung ini dirancang oleh arsitek terkemuka Belanda, Henri Maclaine Pont.",
#                 "latitude": -6.8617,
#                 "longitude": 109.1384,
#                 "is_slider": True,
#                 "image_url": "177196762_1.png",
#                 "gallery": ["177196762_4.png", "177196762_3.png"],
#                 "facility_keys": ["parking"],
#                 "review": "Tempat bersejarah yang sangat bagus."
#             },
#             {
#                 "nama_tempat": "Tahu Aci Tegal",
#                 "subtitle": "Kuliner Khas Paling Populer",
#                 "kategori": "Kuliner",
#                 "tahun_dibangun": "Legendaris",
#                 "lokasi_singkat": "Jl. AR. Hakim",
#                 "durasi_kunjungan": "15-20 mnt",
#                 "jarak_estimasi": "0.8 km",
#                 "deskripsi": "Tahu goreng dengan isian aci gurih yang renyah di luar dan kenyal di dalam. Sangat nikmat dimakan bersama teh poci.",
#                 "fun_fact": "Tahu aci asli Tegal menggunakan tahu kuning yang padat.",
#                 "latitude": -6.8700,
#                 "longitude": 109.1300,
#                 "is_slider": True,
#                 "image_url": "177196762_1.png",
#                 "gallery": ["177196762_4.png", "177196762_3.png"],
#                 "facility_keys": ["restaurant"],
#                 "review": "Rasanya juara, wajib beli kalau ke Tegal."
#             },
#             {
#                 "nama_tempat": "Pantai Alam Indah",
#                 "subtitle": "Wisata Bahari Ikonik",
#                 "kategori": "Wisata",
#                 "tahun_dibangun": "Alami",
#                 "lokasi_singkat": "Mintaragen",
#                 "durasi_kunjungan": "1-2 jam",
#                 "jarak_estimasi": "3.2 km",
#                 "deskripsi": "Pantai yang menawarkan keindahan sunset dan berbagai fasilitas rekreasi air untuk keluarga.",
#                 "fun_fact": "Di sini terdapat Monumen Bahari yang menyimpan alat tempur asli.",
#                 "latitude": -6.8500,
#                 "longitude": 109.1400,
#                 "is_slider": True,
#                 "image_url": "177196762_1.png",
#                 "gallery": ["177196762_4.png", "177196762_3.png"],
#                 "facility_keys": ["toilet"],
#                 "review": "Pasirnya bersih dan ombaknya tenang."
#             },
#             {
#                 "nama_tempat": "Batik Tegalan",
#                 "subtitle": "Warisan Budaya Mendunia",
#                 "kategori": "Tradisi",
#                 "tahun_dibangun": "Abad 19",
#                 "lokasi_singkat": "Kampung Batik",
#                 "durasi_kunjungan": "1 jam",
#                 "jarak_estimasi": "4.5 km",
#                 "deskripsi": "Batik Tegalan memiliki ciri khas warna-warna gelap dan motif yang tegas menggambarkan karakter masyarakat pesisir.",
#                 "fun_fact": "Motif 'Beras Tumpah' adalah salah satu motif paling terkenal.",
#                 "latitude": -6.8800,
#                 "longitude": 109.1200,
#                 "is_slider": True,
#                 "image_url": "177196762_1.png",
#                 "gallery": ["177196762_4.png", "177196762_3.png"],
#                 "facility_keys": ["store"],
#                 "review": "Kualitas kainnya luar biasa bagus."
#             },
#             {
#                 "nama_tempat": "Warteg Bahari",
#                 "subtitle": "Sentra UMKM Kuliner",
#                 "kategori": "UMKM",
#                 "tahun_dibangun": "Modern",
#                 "lokasi_singkat": "Seluruh Kota",
#                 "durasi_kunjungan": "30 mnt",
#                 "jarak_estimasi": "2.1 km",
#                 "deskripsi": "Warung Tegal yang menjadi representasi kemandirian ekonomi masyarakat Tegal di seluruh Indonesia.",
#                 "fun_fact": "Warteg awalnya muncul dari kebutuhan makan pekerja proyek di Jakarta.",
#                 "latitude": -6.8900,
#                 "longitude": 109.1500,
#                 "is_slider": True,
#                 "image_url": "177196762_1.png",
#                 "gallery": ["177196762_4.png", "177196762_3.png"],
#                 "facility_keys": ["restaurant"],
#                 "review": "Menu pilihannya banyak dan murah meriah."
#             },
#             {
#                 "nama_tempat": "Masjid Agung Tegal",
#                 "subtitle": "Ikon Religi & Sejarah",
#                 "kategori": "Sejarah",
#                 "tahun_dibangun": "1825",
#                 "lokasi_singkat": "Alun-Alun",
#                 "durasi_kunjungan": "30 mnt",
#                 "jarak_estimasi": "0.5 km",
#                 "deskripsi": "Masjid utama kota dengan desain yang menggabungkan unsur modern dan tradisional.",
#                 "fun_fact": "Menara masjid ini dapat terlihat dari kejauhan di jalur pantura.",
#                 "latitude": -6.8672,
#                 "longitude": 109.1380,
#                 "is_slider": True,
#                 "image_url": "177196762_1.png",
#                 "gallery": ["177196762_4.png", "177196762_3.png"],
#                 "facility_keys": ["mosque"],
#                 "review": "Sangat tenang untuk beribadah."
#             }
#         ]

#         for item in culture_sites_data:
#             site = CultureSite.query.filter_by(nama_tempat=item["nama_tempat"]).first()
#             if not site:
#                 site = CultureSite(
#                     id=uuid.uuid4(),
#                     nama_tempat=item["nama_tempat"],
#                     subtitle=item["subtitle"],
#                     kategori=item["kategori"],
#                     tahun_dibangun=item["tahun_dibangun"],
#                     lokasi_singkat=item["lokasi_singkat"],
#                     durasi_kunjungan=item["durasi_kunjungan"],
#                     jarak_estimasi=item["jarak_estimasi"],
#                     deskripsi=item["deskripsi"],
#                     fun_fact=item["fun_fact"],
#                     latitude=item["latitude"],
#                     longitude=item["longitude"],
#                     is_slider=item["is_slider"],
#                     image_url=item["image_url"],
#                     gallery=item["gallery"]
#                 )
                
#                 for key in item["facility_keys"]:
#                     if key in db_facilities:
#                         site.facilities.append(db_facilities[key])

#                 db.session.add(site)
#                 db.session.commit()

#                 review = Review(
#                     id=uuid.uuid4(),
#                     user_id=test_user.id,
#                     target_type="culture_site",
#                     target_id=site.id,
#                     rating=4.8,
#                     komentar=item["review"]
#                 )
#                 db.session.add(review)
#                 db.session.commit()

#         print("Sinkronisasi 7 data budaya ikonik berhasil dilakukan!")

# if __name__ == "__main__":
#     seed_database()