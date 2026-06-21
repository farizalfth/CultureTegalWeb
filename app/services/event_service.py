import logging
from datetime import date
from flask import request
from app import db
from app.models import Event

def calculate_event_status(event):
    if event.is_recurring:
        return "Rutin"
        
    if not event.raw_date:
        return event.status
        
    today = date.today()
    end_date = event.raw_end_date if event.raw_end_date else event.raw_date
    
    if today < event.raw_date:
        return "Akan Datang"
    elif event.raw_date <= today <= end_date:
        return "Sedang Berjalan"
    else:
        return "Selesai"

class EventService:
    @staticmethod
    def get_paginated_events(kategori=None, status=None, page=1, per_page=10):
        try:
            query = Event.query
            if kategori and kategori != "Semua":
                query = query.filter(Event.kategori.ilike(kategori))
            
            if status == "Berjalan":
                query = query.filter_by(status="Sedang Berjalan")
            elif status == "Mendatang":
                query = query.filter(Event.status.in_(["Akan Datang", "Rutin"]))
            elif status == "Selesai":
                query = query.filter_by(status="Selesai")

            query = query.order_by(Event.raw_date.desc())
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            result = []
            for e in pagination.items:
                result.append(EventService._serialize_event(e))
                
            return {
                "items": result,
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": pagination.page,
                "has_next": pagination.has_next
            }
        except Exception as e:
            logging.error(f"Error fetching paginated events: {str(e)}")
            raise e


    @staticmethod
    def _serialize_event(event):
        def get_full_url(path):
            if not path:
                return None
            if path.startswith('http://') or path.startswith('https://'):
                return path
            clean_path = path.lstrip('/')
            return f"{request.host_url}static/uploads/{clean_path}"

        dynamic_status = calculate_event_status(event)

        return {
            "id": str(event.id),
            "name": event.judul_event,
            "category": event.kategori,
            "status": dynamic_status,
            "schedule": event.tanggal_lengkap,
            "full_date": event.tanggal_lengkap,
            "time": event.waktu_pelaksanaan,
            "location": event.lokasi_singkat,
            "detailed_address": event.alamat_lengkap,
            "audience": event.audience,
            "ticket_price": event.harga_tiket,
            "description": event.deskripsi,
            "highlights": event.highlights if isinstance(event.highlights, list) else [],
            "latitude": event.latitude,
            "longitude": event.longitude,
            "image_url": get_full_url(event.image_url) if event.image_url else None,
            "is_recurring": event.is_recurring,
            "badge_top": event.badge_top,
            "badge_bottom": event.badge_bottom
        }