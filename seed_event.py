import uuid
from datetime import date
from app import db, create_app
from app.models import Event

app = create_app()

def seed_events():
    with app.app_context():
        Event.query.delete()
        db.session.commit()

        events_data = [
            {
                "judul_event": "Festival Bahari Tegal",
                "kategori": "Budaya",
                "status": "Sedang Berjalan",
                "tanggal_lengkap": "17 - 19 Juni 2026",
                "raw_date": date(2026, 6, 17),
                "raw_end_date": date(2026, 6, 19),
                "waktu_pelaksanaan": "09.00 - 22.00 WIB",
                "lokasi_singkat": "Alun-Alun Kota Tegal",
                "alamat_lengkap": "Jl. Pancasila No.1, Tegal, Jawa Tengah",
                "audience": "Terbuka untuk umum",
                "harga_tiket": "Gratis",
                "deskripsi": "Festival tahunan yang merayakan kekayaan budaya pesisir Kota Tegal dengan pertunjukan seni rakyat.",
                "latitude": -6.8672,
                "longitude": 109.1380,
                "image_url": "177196762_1.png",
                "is_recurring": False,
                "badge_top": "17",
                "badge_bottom": "Jun",
                "highlights": [{"name": "Pentas Seni", "icon": "theater_comedy_rounded"}]
            },
            {
                "judul_event": "Pameran Inovasi UMKM",
                "kategori": "UMKM",
                "status": "Akan Datang",
                "tanggal_lengkap": "28 Juni - 02 Juli 2026",
                "raw_date": date(2026, 6, 28),
                "raw_end_date": date(2026, 7, 2),
                "waktu_pelaksanaan": "09.00 - 18.00 WIB",
                "lokasi_singkat": "Gedung Birao (SCS)",
                "alamat_lengkap": "Jl. Pancasila, Tegal Timur",
                "audience": "Terbuka untuk umum",
                "harga_tiket": "Gratis",
                "deskripsi": "Pameran produk unggulan UMKM lokal Kota Tegal yang menampilkan kreativitas pengusaha muda.",
                "latitude": -6.8617,
                "longitude": 109.1384,
                "image_url": "177196762_1.png",
                "is_recurring": False,
                "badge_top": "28",
                "badge_bottom": "Jun",
                "highlights": [{"name": "Bazar UMKM", "icon": "storefront_rounded"}]
            },
            {
                "judul_event": "Event Makan Ikan",
                "kategori": "Budaya",
                "status": "Selesai",
                "tanggal_lengkap": "23 Mei 2026",
                "raw_date": date(2026, 5, 23),
                "raw_end_date": date(2026, 5, 23),
                "waktu_pelaksanaan": "08.00 - 12.00 WIB",
                "lokasi_singkat": "Pantai Alam Indah",
                "alamat_lengkap": "Kawasan Pantai Alam Indah, Mintaragen",
                "audience": "Terbuka untuk umum",
                "harga_tiket": "Gratis",
                "deskripsi": "Acara gerakan memasyarakatkan makan ikan untuk meningkatkan kesehatan gizi anak-anak Kota Tegal.",
                "latitude": -6.8500,
                "longitude": 109.1400,
                "image_url": "177196762_1.png",
                "is_recurring": False,
                "badge_top": "23",
                "badge_bottom": "Mei",
                "highlights": []
            },
            {
                "judul_event": "Senam Pagi Massal",
                "kategori": "Edukasi",
                "status": "Rutin",
                "tanggal_lengkap": "Setiap Hari Minggu",
                "raw_date": date(2026, 6, 1),
                "raw_end_date": None,
                "waktu_pelaksanaan": "06.00 - 09.00 WIB",
                "lokasi_singkat": "Alun-Alun Tegal",
                "alamat_lengkap": "Kawasan Alun-Alun, Mangkukusuman",
                "audience": "Terbuka untuk umum",
                "harga_tiket": "Gratis",
                "deskripsi": "Kegiatan senam massal rutin gratis untuk menjaga kesehatan jasmani warga kota.",
                "latitude": -6.8672,
                "longitude": 109.1380,
                "image_url": "177196762_1.png",
                "is_recurring": True,
                "badge_top": "Tiap",
                "badge_bottom": "Mggu",
                "highlights": []
            }
        ]

        for item in events_data:
            new_event = Event(
                id=uuid.uuid4(), # type: ignore
                judul_event=item["judul_event"], # type: ignore
                kategori=item["kategori"], # type: ignore
                status=item["status"], # type: ignore
                tanggal_lengkap=item["tanggal_lengkap"], # type: ignore
                raw_date=item["raw_date"], # type: ignore
                raw_end_date=item["raw_end_date"], # type: ignore
                waktu_pelaksanaan=item["waktu_pelaksanaan"], # type: ignore
                lokasi_singkat=item["lokasi_singkat"], # type: ignore
                alamat_lengkap=item["alamat_lengkap"], # type: ignore
                audience=item["audience"], # type: ignore
                harga_tiket=item["harga_tiket"], # type: ignore
                deskripsi=item["deskripsi"], # type: ignore
                latitude=item["latitude"], # type: ignore
                longitude=item["longitude"], # type: ignore
                image_url=item["image_url"], # type: ignore
                is_recurring=item["is_recurring"], # type: ignore
                badge_top=item["badge_top"], # type: ignore
                badge_bottom=item["badge_bottom"], # type: ignore
                highlights=item["highlights"] # type: ignore
            )
            db.session.add(new_event)
        
        db.session.commit()
        print("Data uji event dinamis sukses disimpan!")

if __name__ == "__main__":
    seed_events()