import os
import uuid
from flask import current_app
from app.models import db, User, AIScanHistory, FoodMetadata
from app.services.upload_service import save_image
from app.services.ai_model_service import AIModelService
from app.services.scan_service import ScanService

class AIScanService:

    @staticmethod
    def process_food_scan(user_id, image_file):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        file_name = save_image(image_file)
        if not file_name:
            return None, "Failed to process image"

        local_image_path = os.path.join(current_app.root_path, 'static', 'uploads', file_name)
        model_directory = os.path.join(current_app.root_path, 'model_ai')
        if not os.path.exists(model_directory):
            os.makedirs(model_directory)

        model_path = os.path.join(model_directory, 'food_detector.onnx')
        model_type = "yolo"
        use_letterbox = True
        input_size = (640, 640)

        if not os.path.exists(model_path):
            model_path = os.path.join(model_directory, 'food_classifier.onnx')
            if os.path.exists(model_path):
                model_type = "classification"
                input_size = (224, 224)

        predicted_key, confidence = AIModelService.run_inference(
            local_image_path,
            model_path,
            model_type=model_type,
            use_letterbox=use_letterbox,
            input_size=input_size
        )

        food = FoodMetadata.query.filter_by(label_key=predicted_key).first()
        food_id = food.id if food else None

        existing_scan = AIScanHistory.query.filter_by(user_id=user_id, food_id=food_id).first()

        points_earned = 0
        user = User.query.get(user_id)
        if not existing_scan and food_id and user:
            points_earned = 50
            user.poin += points_earned
            user.total_xp += points_earned
            calculated_level = (user.poin // 1000) + 1
            if calculated_level > user.level:
                user.level = calculated_level
            ScanService._evaluate_and_unlock_badges(user)

        scan_record = AIScanHistory(
            user_id=user_id, # type: ignore
            image_url=file_name, # type: ignore
            predicted_label=predicted_key, # type: ignore
            food_id=food_id # type: ignore
        )
        db.session.add(scan_record)
        db.session.commit()

        return {
            "id": str(scan_record.id),
            "predicted_label": predicted_key,
            "confidence": confidence,
            "points_earned": points_earned,
            "current_points": user.poin if user else 0,
            "current_level": user.level if user else 1,
            "food_details": {
                "id": str(food.id) if food else None,
                "nama_makanan": food.nama_makanan if food else predicted_key,
                "deskripsi": food.deskripsi if food else "No description available",
                "video_url": AIScanService.resolve_video_url(food.video_url) if food and food.video_url else None
            } if food else None,
            "image_url": f"/static/uploads/{scan_record.image_url}"
        }, None

    @staticmethod
    def resolve_video_url(video_url):
        if not video_url:
            return None
        if video_url.startswith(('http://', 'https://')):
            return video_url
        try:
            from flask import request
            base_host = request.host_url.rstrip('/')
            return f"{base_host}/static/uploads/videos/{video_url}"
        except RuntimeError:
            return f"/static/uploads/videos/{video_url}"

    @staticmethod
    def get_user_ai_history(user_id):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        history = AIScanHistory.query.filter_by(user_id=user_id).order_by(AIScanHistory.created_at.desc()).all()
        result = []
        for item in history:
            food = FoodMetadata.query.get(item.food_id) if item.food_id else None
            result.append({
                "id": str(item.id),
                "predicted_label": item.predicted_label,
                "food_details": {
                    "nama_makanan": food.nama_makanan if food else item.predicted_label,
                    "deskripsi": food.deskripsi if food else "No description available",
                    "video_url": AIScanService.resolve_video_url(food.video_url) if food else None
                },
                "image_url": f"/static/uploads/{item.image_url}" if item.image_url else None,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })
        return result, None