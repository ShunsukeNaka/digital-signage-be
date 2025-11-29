from datetime import datetime, timedelta
import uuid
from . import db

class OneTimeToken(db.Model):
    __tablename__ = 'onetimetokens'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    expires_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.utcnow() + timedelta(hours=1))
