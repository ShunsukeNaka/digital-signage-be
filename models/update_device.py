from datetime import datetime
from . import db

class UpdateDevice(db.Model):
    __tablename__ = 'update_device'

    user_id = db.Column(
        db.String,
        db.ForeignKey('users.id', ondelete="CASCADE"),  # ユーザー削除時に連動削除
        primary_key=True
    )
    device_id = db.Column(
        db.String,
        db.ForeignKey('devices.id', ondelete="CASCADE"),  # デバイス削除時に連動削除
        primary_key=True
    )

    update = db.Column(db.Boolean, nullable=False, default=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    update_index = db.Column(db.String, nullable=False, default="0", server_default="0")  # ★追加


    # リレーション
    user = db.relationship('User', backref=db.backref('update_devices', lazy=True, passive_deletes=True))
    device = db.relationship('Device', backref=db.backref('update_devices', lazy=True, passive_deletes=True))
