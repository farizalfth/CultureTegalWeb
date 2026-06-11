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
            current_user = user_response.user # type: ignore
            
            from app.models import User
            local_user = User.query.get(current_user.id)
            
            if not local_user:
                return jsonify({"status": "error", "message": "User account has been deleted"}), 403
                
            if local_user.is_banned:
                return jsonify({"status": "error", "message": "Your account has been suspended"}), 403
                
        except Exception as e:
            print(traceback.format_exc())
            return jsonify({"status": "error", "message": "Invalid or expired token"}), 401

        return f(current_user, *args, **kwargs)
    return decorated