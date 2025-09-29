from datetime import datetime
from . import db

class DeviceSetting(db.Model):
    __tablename__ = "device_settings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String, nullable=False)
    device_id = db.Column(db.String, nullable=False)
    settings = db.Column(db.JSON, nullable=False)  # PostgreSQL なら JSONB として扱われる
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("device_id"),
    )
