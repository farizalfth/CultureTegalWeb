import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.quiz_service import QuizService

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/culture/<uuid:culture_id>', methods=['GET'])
@jwt_required()
def get_culture_quizzes(culture_id):
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
@jwt_required()
def submit_quiz(quiz_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data or 'jawaban' not in data:
        return jsonify({"message": "Jawaban is required"}), 400
    
    answer = data['jawaban']
    result, error = QuizService.submit_answer(user_id, quiz_id, answer)
    if error:
        return jsonify({"message": error}), 404
    
    return jsonify(result), 200