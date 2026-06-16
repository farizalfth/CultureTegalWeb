import os
import traceback
from functools import wraps
from flask import request, jsonify
from supabase import create_client, Client
from config import Config

supabase_url = Config.SUPABASE_URL.strip().rstrip('/') # type: ignore
supabase: Client = create_client(supabase_url, Config.SUPABASE_SECRET_KEY) # type: ignore

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
        
        if not token:
            return jsonify({"status": "error", "message": "Token is missing"}), 401

        try:
            user_response = supabase.auth.get_user(token)
            supabase_user = user_response.user # type: ignore
            
            from app.models import User, db
            local_user = User.query.get(supabase_user.id)
            
            supabase_avatar = supabase_user.user_metadata.get('avatar_url')
            
            if not local_user:
                local_user = User(
                    id=supabase_user.id, # type: ignore
                    nama=supabase_user.user_metadata.get('full_name', 'User Baru'),# type: ignore
                    email=supabase_user.email,# type: ignore
                    profile_picture=supabase_avatar,# type: ignore
                    poin=0# type: ignore
                )
                db.session.add(local_user)
                db.session.commit()
            else:
                if not local_user.profile_picture and supabase_avatar:
                    local_user.profile_picture = supabase_avatar
                    db.session.commit()
                
            if local_user.is_banned:
                return jsonify({"status": "error", "message": "Your account has been suspended"}), 403
                
        except Exception as e:
            return jsonify({"status": "error", "message": "Invalid or expired token"}), 401

        return f(local_user, *args, **kwargs)
    return decorated