import os
import requests
import uuid
from app.models import db, User, UserDevice

class NotificationService:

    @staticmethod
    def send_to_user(user_id, title, message, data_payload=None):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        
        devices = UserDevice.query.filter_by(user_id=user_id).all()
        subscription_ids = [d.onesignal_id for d in devices]
        if not subscription_ids:
            return False, "No active devices found for this user"

        app_id = os.getenv("ONESIGNAL_APP_ID")
        api_key = os.getenv("ONESIGNAL_API_KEY")

        if not app_id or not api_key:
            return False, "OneSignal credentials not configured"

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Basic {api_key}"
        }

        payload = {
            "app_id": app_id,
            "include_subscription_ids": subscription_ids,
            "headings": {"en": title, "id": title},
            "contents": {"en": message, "id": message}
        }

        if data_payload:
            payload["data"] = data_payload

        try:
            response = requests.post(
                "https://onesignal.com/api/v1/notifications",
                headers=headers,
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                return True, None
            return False, response.text
        except Exception as e:
            return False, str(e)

    @staticmethod
    def send_to_all(title, message, data_payload=None):
        app_id = os.getenv("ONESIGNAL_APP_ID")
        api_key = os.getenv("ONESIGNAL_API_KEY")

        if not app_id or not api_key:
            return False, "OneSignal credentials not configured"

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Basic {api_key}"
        }

        payload = {
            "app_id": app_id,
            "included_segments": ["All"],
            "headings": {"en": title, "id": title},
            "contents": {"en": message, "id": message}
        }

        if data_payload:
            payload["data"] = data_payload

        try:
            response = requests.post(
                "https://onesignal.com/api/v1/notifications",
                headers=headers,
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                return True, None
            return False, response.text
        except Exception as e:
            return False, str(e)