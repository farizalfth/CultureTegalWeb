from app.models import db, User

class AuthController:
    @staticmethod
    def sync_user_data(user_id, email, nama, provider='email', profile_picture=None):
        try:
            user = User.query.get(user_id)
            if not user:
                user = User(
                    id=user_id, # type: ignore
                    email=email, # type: ignore
                    nama=nama, # type: ignore
                    auth_provider=provider, # type: ignore
                    profile_picture=profile_picture # type: ignore
                )
                db.session.add(user)
            else:
                user.nama = nama if nama else user.nama
                user.profile_picture = profile_picture if profile_picture else user.profile_picture
            
            db.session.commit()
            return {"status": "success", "data": {"id": str(user.id), "nama": user.nama, "email": user.email}}
        except Exception as e:
            db.session.rollback()
            raise Exception(str(e))