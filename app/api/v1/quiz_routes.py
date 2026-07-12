import uuid
from flask import Blueprint, request, jsonify
from app.models import Quiz, CultureSite, UserQuizHistory
from app.services.quiz_service import QuizService
from app.services.auth_service import token_required
from app.models import db

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('', methods=['GET'])
@token_required
def get_all_quizzes(current_user):
    solved_quizzes = db.session.query(UserQuizHistory.quiz_id).filter(
        UserQuizHistory.user_id == current_user.id,
        UserQuizHistory.is_correct == True
    ).all()
    solved_ids = {str(item[0]) for item in solved_quizzes}

    quizzes = Quiz.query.all()
    result = []
    for quiz in quizzes:
        culture_name = "Umum"
        culture_image = ""
        if quiz.culture_id:
            site = CultureSite.query.get(quiz.culture_id)
            if site:
                culture_name = site.nama_tempat
                culture_image = site.image_url
        result.append({
            "id": str(quiz.id),
            "culture_id": str(quiz.culture_id) if quiz.culture_id else None,
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
def submit_quiz(current_user, quiz_id):
    data = request.get_json()
    if not data or 'jawaban' not in data:
        return jsonify({"message": "Jawaban is required"}), 400
    
    answer = data['jawaban']
    result, error = QuizService.submit_answer(current_user.id, quiz_id, answer)
    if error:
        return jsonify({"message": error}), 404
    
    return jsonify(result), 200