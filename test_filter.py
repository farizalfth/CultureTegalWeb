import os
from pymongo import MongoClient

def load_env_manually():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().strip('"').strip("'")
                    os.environ[key] = val

def test_database_queries():
    print("[1/3] Memulai inisialisasi lingkungan...")
    load_env_manually()
    
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("[Error] MONGO_URI tidak ditemukan di file .env!")
        return

    print("[2/3] Menghubungkan ke MongoDB Atlas...")
    try:
        client = MongoClient(mongo_uri)
        db = client['review_tempat_bersejarah_tegal']
        collection = db['reviews_data']
        print(f"[Sukses] Terhubung ke MongoDB Atlas.")

        print("\n=== [TEST 1] PEMETAAN DATA NYATA DI MONGODB CLOUD ===")
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "target_id": "$target_id",
                        "Lokasi": "$Lokasi"
                    },
                    "total_ulasan": {"$sum": 1}
                }
            }
        ]
        
        groups = list(collection.aggregate(pipeline))
        if not groups:
            print("[Warning] Database ulasan kosong! Jalankan scraper terlebih dahulu.")
            return

        for g in groups:
            t_id = g["_id"].get("target_id")
            loc = g["_id"].get("Lokasi")
            count = g.get("total_ulasan")
            print(f"UUID di MongoDB: {t_id} | Lokasi: {loc} | Jumlah: {count} Ulasan")
            
        print("\n=== [TEST 2] SIMULASI FILTER LOKASI DAN SORTIR TERBARU ===")
        
        sample_target_id = groups[0]["_id"].get("target_id")
        sample_location = groups[0]["_id"].get("Lokasi")
        
        print(f"Menguji kueri filter untuk target_id: {sample_target_id} ({sample_location})")
        
        query_filter = {
            "target_id": sample_target_id,
            "Ulasan": {"$ne": ""}
        }
        
        results = list(collection.find(query_filter).sort([("Tanggal_Review", -1), ("_id", -1)]).limit(5))
        
        print(f"[Sukses] Berhasil mengambil {len(results)} ulasan terurut terbaru:")
        for r in results:
            print(f" - Lokasi Doc: {r.get('Lokasi')} | Rating: {r.get('Rating')} | Tanggal Review: {r.get('Tanggal_Review')} | Ulasan: {r.get('Ulasan', '')[:60]}...")

    except Exception as e:
        print(f"[Error] Terjadi kegagalan selama pemrosesan: {str(e)}")

if __name__ == '__main__':
    test_database_queries()