import uuid
from app.models import db, User, Quiz, UserQuizHistory, Badge, UserBadge

class QuizService:

    @staticmethod
    def get_quizzes_by_culture(culture_id):
        if isinstance(culture_id, str):
            culture_id = uuid.UUID(culture_id)
        return Quiz.query.filter_by(culture_id=culture_id).all()

    @staticmethod
    def get_quiz_by_id(quiz_id):
        if isinstance(quiz_id, str):
            quiz_id = uuid.UUID(quiz_id)
        return Quiz.query.get(quiz_id)

    @staticmethod
    def submit_answer(user_id, quiz_id, answer):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(quiz_id, str):
            quiz_id = uuid.UUID(quiz_id)

        user = User.query.get(user_id)
        quiz = Quiz.query.get(quiz_id)

        if not user or not quiz:
            return None, "User or Quiz not found"

        existing_correct = UserQuizHistory.query.filter_by(
            user_id=user_id,
            quiz_id=quiz_id,
            is_correct=True
        ).first()

        is_correct = quiz.jawaban_benar.strip().upper() == answer.strip().upper()

        if is_correct:
            history = UserQuizHistory(
                user_id=user_id, # type: ignore
                quiz_id=quiz_id, # type: ignore
                is_correct=True # type: ignore
            )
            db.session.add(history)

            points_earned = 0
            if not existing_correct:
                points_earned = quiz.poin_reward
                user.poin += points_earned
                user.total_xp += points_earned
                
                calculated_level = (user.total_xp // 1000) + 1
                if calculated_level > user.level:
                    user.level = calculated_level

                QuizService._evaluate_and_unlock_badges(user)

            db.session.commit()
            return {
                "correct": True,
                "points_earned": points_earned,
                "current_points": user.poin,
                "current_xp": user.total_xp,
                "current_level": user.level
            }, None
        else:
            history = UserQuizHistory(
                user_id=user_id, # type: ignore
                quiz_id=quiz_id, # type: ignore
                is_correct=False # type: ignore
            )
            db.session.add(history)
            db.session.commit()
            return {
                "correct": False,
                "points_earned": 0,
                "current_points": user.poin,
                "current_xp": user.total_xp,
                "current_level": user.level
            }, None

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