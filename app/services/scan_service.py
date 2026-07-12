import uuid
import math
from app.models import db, User, CultureSite, ScanHistory, Badge, UserBadge

class ScanService:

    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        r = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @staticmethod
    def scan_via_qr(user_id, site_id):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(site_id, str):
            site_id = uuid.UUID(site_id)

        user = User.query.get(user_id)
        site = CultureSite.query.get(site_id)

        if not user or not site:
            return None, "User or Culture Site not found"

        existing_scan = ScanHistory.query.filter_by(
            user_id=user_id,
            site_id=site_id
        ).first()

        points_earned = 0
        if not existing_scan:
            points_earned = 100
            user.poin += points_earned
            user.total_xp += points_earned

            calculated_level = (user.poin // 1000) + 1
            if calculated_level > user.level:
                user.level = calculated_level

            ScanService._evaluate_and_unlock_badges(user)

        history = ScanHistory(
            user_id=user_id,# type: ignore
            site_id=site_id,# type: ignore
            scan_method="qr",# type: ignore
            poin_didapat=points_earned# type: ignore
        )
        db.session.add(history)
        db.session.commit()

        return {
            "success": True,
            "method": "qr",
            "points_earned": points_earned,
            "current_points": user.poin,
            "current_level": user.level
        }, None

    @staticmethod
    def scan_via_geofence(user_id, site_id, user_lat, user_lon):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(site_id, str):
            site_id = uuid.UUID(site_id)

        user = User.query.get(user_id)
        site = CultureSite.query.get(site_id)

        if not user or not site:
            return None, "User or Culture Site not found"

        distance = ScanService.calculate_distance(user_lat, user_lon, site.latitude, site.longitude)
        
        if distance > 100.0:
            return None, f"You are too far from the location. Distance: {round(distance, 2)} meters. Required: within 100 meters."

        existing_scan = ScanHistory.query.filter_by(
            user_id=user_id,
            site_id=site_id
        ).first()

        points_earned = 0
        if not existing_scan:
            points_earned = 100
            user.poin += points_earned
            user.total_xp += points_earned

            calculated_level = (user.poin // 1000) + 1
            if calculated_level > user.level:
                user.level = calculated_level

            ScanService._evaluate_and_unlock_badges(user)

        history = ScanHistory(
            user_id=user_id,# type: ignore
            site_id=site_id,# type: ignore
            scan_method="geofence",# type: ignore
            poin_didapat=points_earned# type: ignore
        )
        db.session.add(history)
        db.session.commit()

        return {
            "success": True,
            "method": "geofence",
            "distance_meters": round(distance, 2),
            "points_earned": points_earned,
            "current_points": user.poin,
            "current_level": user.level
        }, None

    @staticmethod
    def explore_via_read(user_id, site_id):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(site_id, str):
            site_id = uuid.UUID(site_id)

        user = User.query.get(user_id)
        site = CultureSite.query.get(site_id)

        if not user or not site:
            return None, "User or Culture Site not found"

        existing_scan = db.session.query(ScanHistory).filter(
            ScanHistory.user_id == user_id,
            ScanHistory.site_id == site_id
        ).first()

        points_earned = 0
        if not existing_scan:
            points_earned = 10
            user.poin += points_earned
            user.total_xp += points_earned

            calculated_level = (user.poin // 1000) + 1
            if calculated_level > user.level:
                user.level = calculated_level

            ScanService._evaluate_and_unlock_badges(user)

            history = ScanHistory(
                user_id=user_id,# type: ignore
                site_id=site_id,# type: ignore
                scan_method="read",# type: ignore
                poin_didapat=points_earned# type: ignore
            )
            db.session.add(history)
            db.session.commit()

        return {
            "success": True,
            "points_earned": points_earned,
            "current_points": user.poin,
            "current_level": user.level
        }, None

    @staticmethod
    def _evaluate_and_unlock_badges(user):
        eligible_badges = Badge.query.filter(Badge.syarat_poin <= user.poin).all()
        for badge in eligible_badges:
            already_unlocked = UserBadge.query.filter_by(
                user_id=user.id,
                badge_id=badge.id
            ).first()
            if not already_unlocked:
                unlocked_badge = UserBadge(
                    user_id=user.id, # type: ignore
                    badge_id=badge.id # type: ignore
                )
                db.session.add(unlocked_badge)