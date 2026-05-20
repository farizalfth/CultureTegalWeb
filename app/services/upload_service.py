import os
import time
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = f"{int(time.time())}_{filename}"
        upload_path = os.path.join(current_app.root_path, 'static', 'uploads')
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        file.save(os.path.join(upload_path, filename))
        return filename
    return None

def delete_file(filename):
    if filename:
        path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
        if os.path.exists(path):
            os.remove(path)