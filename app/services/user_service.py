import uuid
from app.models import db, User, UserFavorite, CultureSite, UMKM, Event, Badge, UserBadge, ScanHistory, UserQuizHistory

class UserService:

    @staticmethod
    def toggle_favorite(user_id, target_type, target_id):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(target_id, str):
            target_id = uuid.UUID(target_id)

        if target_type not in ['culture', 'umkm', 'event']:
            return None, "Invalid target type"

        exists = None

        if target_type == 'culture':
            exists = CultureSite.query.get(target_id)
        elif target_type == 'umkm':
            exists = UMKM.query.get(target_id)
        elif target_type == 'event':
            exists = Event.query.get(target_id)

        if not exists:
            return None, "Target item not found"

        fav = UserFavorite.query.filter_by(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id
        ).first()

        if fav:
            db.session.delete(fav)
            db.session.commit()
            return {"favorited": False}, None
        else:
            new_fav = UserFavorite(
                user_id=user_id, # type: ignore
                target_type=target_type, # type: ignore
                target_id=target_id # type: ignore
            )
            db.session.add(new_fav)
            db.session.commit()
            return {"favorited": True}, None

    @staticmethod
    def get_user_favorites(user_id):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        favorites = UserFavorite.query.filter_by(user_id=user_id).all()
        
        cultures_list = []
        umkms_list = []
        events_list = []

        for fav in favorites:
            if fav.target_type == 'culture':
                site = CultureSite.query.get(fav.target_id)
                if site:
                    cultures_list.append({
                        "id": str(site.id),
                        "nama_tempat": site.nama_tempat,
                        "subtitle": site.subtitle,
                        "kategori": site.kategori,
                        "image_url": site.image_url,
                        "lokasi_singkat": site.lokasi_singkat
                    })
            elif fav.target_type == 'umkm':
                umkm = UMKM.query.get(fav.target_id)
                if umkm:
                    umkms_list.append(umkm.to_dict())
            elif fav.target_type == 'event':
                from app.services.event_service import EventService
                event = Event.query.get(fav.target_id)
                if event:
                    events_list.append(EventService._serialize_event(event))

        return {
            "cultures": cultures_list,
            "umkms": umkms_list,
            "events": events_list
        }, None

    @staticmethod
    def get_user_badges(user_id):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        all_badges = Badge.query.all()
        user_badge_ids = {str(ub.badge_id) for ub in UserBadge.query.filter_by(user_id=user_id).all()}

        badges_data = []
        for badge in all_badges:
            is_unlocked = str(badge.id) in user_badge_ids
            badges_data.append({
                "id": str(badge.id),
                "nama_badge": badge.nama_badge,
                "deskripsi": badge.deskripsi,
                "image_url": badge.image_url,
                "syarat_poin": badge.syarat_poin,
                "is_unlocked": is_unlocked
            })

        return badges_data, None

    @staticmethod
    def get_leaderboard():
        top_users = User.query.filter_by(is_banned=False).order_by(User.poin.desc()).limit(10).all()
        leaderboard_data = []
        for index, user in enumerate(top_users):
            dyn_level = (user.poin // 1000) + 1
            leaderboard_data.append({
                "rank": index + 1,
                "id": str(user.id),
                "nama": user.nama,
                "profile_picture": user.profile_picture,
                "total_xp": user.poin,
                "level": dyn_level
            })
        return leaderboard_data, None

    @staticmethod
    def update_profile(user_id, nama, no_telp):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        user = User.query.get(user_id)
        if not user:
            return None, "User not found"

        user.nama = nama
        user.no_telp = no_telp
        db.session.commit()
        return {
            "id": str(user.id),
            "nama": user.nama,
            "no_telp": user.no_telp
        }, None

    @staticmethod
    def update_profile_picture(user_id, file_name):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        user = User.query.get(user_id)
        if not user:
            return None, "User not found"

        user.profile_picture = file_name
        db.session.commit()
        return {"profile_picture": file_name}, None

    @staticmethod
    def get_user_stats(user_id):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        user = User.query.get(user_id)
        if not user:
            return None, "User not found"

        scanned_count = db.session.query(ScanHistory.site_id).filter(ScanHistory.user_id == user_id).distinct().count()
        correct_quiz_count = db.session.query(UserQuizHistory.quiz_id).filter(UserQuizHistory.user_id == user_id, UserQuizHistory.is_correct == True).distinct().count()
        badges_collected = UserBadge.query.filter_by(user_id=user_id).count()

        dyn_level = (user.poin // 1000) + 1

        return {
            "scanned_sites_count": scanned_count,
            "correct_quizzes_count": correct_quiz_count,
            "badges_collected_count": badges_collected,
            "total_points": user.poin,
            "total_xp": user.poin,
            "current_level": dyn_level
        }, None

    @staticmethod
    def get_user_scan_history(user_id):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        scans = ScanHistory.query.filter_by(user_id=user_id).order_by(ScanHistory.created_at.desc()).all()
        
        history_data = []
        for scan in scans:
            site = CultureSite.query.get(scan.site_id)
            if site:
                history_data.append({
                    "id": str(scan.id),
                    "site_id": str(site.id),
                    "nama_tempat": site.nama_tempat,
                    "image_url": site.image_url,
                    "scan_method": scan.scan_method,
                    "poin_didapat": scan.poin_didapat,
                    "created_at": scan.created_at.isoformat() if scan.created_at else None
                })

        return history_data, None

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