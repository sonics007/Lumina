from ..models import db, History
from flask import request, has_request_context
import logging

def log_history(action, content="", playlist=""):
    try:
        ip = "127.0.0.1"
        ua = "System"
        
        if has_request_context():
            ip = request.remote_addr
            ua = request.headers.get('User-Agent', '')

        h = History(
            action=action, 
            content=content[:255], 
            playlist=playlist,
            ip=ip,
            user_agent=ua
        )
        db.session.add(h)
        db.session.commit()
    except Exception as e:
        logging.error(f"Failed to log history: {e}")
        db.session.rollback()
