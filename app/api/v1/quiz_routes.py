import os
import yaml
import uuid
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.models import Quiz, CultureSite, UserQuizHistory, FoodMetadata
from app.services.quiz_service import QuizService
from app.services.auth_service import token_required
from app.models import db, AIScanHistory

quiz_bp = Blueprint('quiz', __name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
yml_path = os.path.abspath(os.path.join(base_dir, '..', 'docs', 'quizzes.yml'))

with open(yml_path, 'r', encoding='utf-8') as f:
    quiz_specs = yaml.safe_load(f)

@quiz_bp.route('', methods=['GET'])
@token_required
@swag_from(quiz_specs['get_all_quizzes'])
def get_all_quizzes(current_user):
    solved_quizzes = db.session.query(UserQuizHistory.quiz_id).filter(
        UserQuizHistory.user_id == current_user.id,
        UserQuizHistory.is_correct == True
    ).all()
    solved_ids = {str(item[0]) for item in solved_quizzes}

    scanned_foods = db.session.query(AIScanHistory.food_id).filter(
        AIScanHistory.user_id == current_user.id
    ).all()
    scanned_food_ids = {str(item[0]) for item in scanned_foods if item[0] is not None}

    quizzes = Quiz.query.all()
    result = []
    for quiz in quizzes:
        if quiz.food_id and str(quiz.food_id) not in scanned_food_ids:
            continue

        culture_name = "Umum"
        culture_image = ""
        if quiz.culture_id:
            site = CultureSite.query.get(quiz.culture_id)
            if site:
                culture_name = site.nama_tempat
                culture_image = site.image_url
        elif quiz.food_id:
            food = FoodMetadata.query.get(quiz.food_id)
            if food:
                culture_name = food.nama_makanan
                culture_image = "default.jpg"

        result.append({
            "id": str(quiz.id),
            "culture_id": str(quiz.culture_id) if quiz.culture_id else None,
            "food_id": str(quiz.food_id) if quiz.food_id else None,
            "culture_name": culture_name,
            "culture_image": culture_image,
            "pertanyaan": quiz.pertanyaan,
            "image_url": quiz.image_url,
            "opsi_jawaban": quiz.opsi_jawaban,
            "poin_reward": quiz.poin_reward,
            "jawaban_benar": quiz.jawaban_benar,
            "is_solved": str(quiz.id) in solved_ids
        })
    return jsonify(result), 200

@quiz_bp.route('/culture/<uuid:culture_id>', methods=['GET'])
@token_required
@swag_from(quiz_specs['get_culture_quizzes'])
def get_culture_quizzes(current_user, culture_id):
    quizzes = QuizService.get_quizzes_by_culture(culture_id)
    result = []
    for quiz in quizzes:
        result.append({
            "id": str(quiz.id),
            "pertanyaan": quiz.pertanyaan,
            "image_url": quiz.image_url,
            "opsi_jawaban": quiz.opsi_jawaban,
            "poin_reward": quiz.poin_reward
        })
    return jsonify(result), 200

@quiz_bp.route('/<uuid:quiz_id>/submit', methods=['POST'])
@token_required
@swag_from(quiz_specs['submit_quiz'])
def submit_quiz(current_user, quiz_id):
    data = request.get_json()
    if not data or 'jawaban' not in data:
        return jsonify({"message": "Jawaban is required"}), 400
    
    answer = data['jawaban']
    result, error = QuizService.submit_answer(current_user.id, quiz_id, answer)
    if error:
        return jsonify({"message": error}), 404
    
    return jsonify(result), 200