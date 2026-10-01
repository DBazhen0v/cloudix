from .models import Notification


def create_notification(db, user_id, type, title, body=None, link=None):
    db.add(Notification(user_id=user_id, type=type, title=title, body=body, link=link))
