from datetime import datetime, timedelta
import uuid
from . import db

class Token(db.Model):
    __tablename__ = 'tokens'

    # 新しい主キー
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # UUIDトークンはユニークだけど主キーではない
    token = db.Column(db.UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    device_id = db.Column(db.String, db.ForeignKey('devices.id'), nullable=True)

    added_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow() + timedelta(hours=1))
    
    token_type = db.Column(db.String, nullable=False)

    # リレーション
    user = db.relationship('User', backref=db.backref('tokens', lazy=True))
    device = db.relationship('Device', backref=db.backref('tokens', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'device_id', 'token_type', name='unique_user_device_type'),
    )

