import uuid
from app.models import db, CultureSite, UMKM, Event
from app.services.scan_service import ScanService

class SearchService:

    @staticmethod
    def search_map(query, user_lat=None, user_lon=None):
        results = []
        q = f"%{query}%"

        cultures = CultureSite.query.filter(CultureSite.nama_tempat.ilike(q) | CultureSite.deskripsi.ilike(q)).all()
        for item in cultures:
            distance = None
            if user_lat is not None and user_lon is not None:
                distance = ScanService.calculate_distance(user_lat, user_lon, item.latitude, item.longitude)
            
            results.append({
                "id": str(item.id),
                "type": "culture",
                "name": item.nama_tempat,
                "subtitle": item.subtitle,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "image_url": item.image_url,
                "distance_meters": round(distance, 2) if distance is not None else None
            })

        umkms = UMKM.query.filter(UMKM.nama_produk.ilike(q) | UMKM.nama_toko.ilike(q) | (UMKM.deskripsi != None) & UMKM.deskripsi.ilike(q)).all()
        for item in umkms:
            distance = None
            if user_lat is not None and user_lon is not None and item.latitude is not None and item.longitude is not None:
                distance = ScanService.calculate_distance(user_lat, user_lon, item.latitude, item.longitude)

            results.append({
                "id": str(item.id),
                "type": "umkm",
                "name": item.nama_produk,
                "subtitle": item.nama_toko,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "image_url": item.image_url,
                "distance_meters": round(distance, 2) if distance is not None else None
            })

        events = Event.query.filter(Event.judul_event.ilike(q) | Event.deskripsi.ilike(q)).all()
        for item in events:
            distance = None
            if user_lat is not None and user_lon is not None:
                distance = ScanService.calculate_distance(user_lat, user_lon, item.latitude, item.longitude)

            results.append({
                "id": str(item.id),
                "type": "event",
                "name": item.judul_event,
                "subtitle": item.kategori,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "image_url": item.image_url,
                "distance_meters": round(distance, 2) if distance is not None else None
            })

        if user_lat is not None and user_lon is not None:
            results.sort(key=lambda x: x["distance_meters"] if x["distance_meters"] is not None else float('inf'))

        return results