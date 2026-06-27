import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SECRET_KEY = os.getenv('SUPABASE_SECRET_KEY')
    
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

    SITE_NAME = os.getenv('SITE_NAME', 'Tegal Culture')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'helloa@tegalculture.id')
    SITE_SLOGAN = os.getenv('SITE_SLOGAN', 'Platform digital untuk mengeksplorasi identitas dan kebanggaan budaya Kota Bahari.')

    STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'local')
    LOCAL_STORAGE_BASE_URL = os.getenv('LOCAL_STORAGE_BASE_URL', '')
    STORAGE_BASE_URL = os.getenv('STORAGE_BASE_URL', '')