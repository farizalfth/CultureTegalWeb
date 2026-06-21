import uuid
from datetime import date
from app import db, create_app
from app.models import News

app = create_app()

def seed_news():
    with app.app_context():
        News.query.delete()
        db.session.commit()

        news_data = [
            {
                "judul": "Gereja Blenduk Jadi Ikon Sejarah Kota Tegal",
                "kategori": "Budaya",
                "tanggal": date(2026, 6, 18),
                "image_url": "177196762_1.png",
                "konten": "Gereja Blenduk merupakan salah satu bangunan bersejarah yang sangat terawat di kawasan pesisir Jawa Tengah. Keunikan arsitektur kolonial yang khas menjadikannya destinasi favorit bagi pecinta sejarah dan budaya lokal."
            },
            {
                "judul": "Tahu Aci Khas Tegal Semakin Diminati Wisatawan",
                "kategori": "Kuliner",
                "tanggal": date(2026, 6, 17),
                "image_url": "177196762_1.png",
                "konten": "Kuliner tahu aci dengan tekstur renyah di luar dan kenyal di dalam terus mendominasi pusat oleh-oleh Tegal. Peningkatan jumlah kunjungan wisatawan berbanding lurus dengan peningkatan omset para pengrajin tahu aci lokal."
            },
            {
                "judul": "Pameran Kerajinan Batik Tegalan Resmi Dibuka",
                "kategori": "UMKM",
                "tanggal": date(2026, 6, 15),
                "image_url": "177196762_1.png",
                "konten": "Pemerintah Kota Tegal meresmikan pameran batik tegalan bermotif klasik. Acara ini ditujukan untuk mempromosikan warisan wastra pesisir ke pasar internasional guna mendukung ekonomi kreatif lokal."
            },
            {
                "judul": "Workshop Koding Pemula untuk Pelajar Tegal",
                "kategori": "Edukasi",
                "tanggal": date(2026, 6, 10),
                "image_url": "177196762_1.png",
                "konten": "Puluhan siswa SMA/SMK di Kota Tegal antusias mengikuti pelatihan logika dasar pemrograman. Kegiatan ini diinisiasi untuk membangun kesiapan digital generasi muda Tegal menghadapi era industri cerdas."
            },
            {
                "judul": "Festival Mangrove Pantai Alam Indah Dipadati Pengunjung",
                "kategori": "Wisata",
                "tanggal": date(2026, 6, 1),
                "image_url": "177196762_1.png",
                "konten": "Ribuan warga memadati kawasan hutan mangrove dalam acara kampanye pelestarian lingkungan pesisir Pantai Alam Indah. Berbagai edukasi ekologi disajikan secara menarik sepanjang acara."
            }
        ]

        for item in news_data:
            new_news = News(
                id=uuid.uuid4(), # type: ignore
                judul=item["judul"], # type: ignore
                kategori=item["kategori"], # type: ignore
                tanggal=item["tanggal"], # type: ignore
                image_url=item["image_url"], # type: ignore
                konten=item["konten"] # type: ignore
            )
            db.session.add(new_news)
        
        db.session.commit()
        print("Data uji berita sukses disimpan!")

if __name__ == "__main__":
    seed_news()