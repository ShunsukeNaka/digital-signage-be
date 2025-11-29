from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY
from . import db


class DeviceSetting(db.Model):
    __tablename__ = "device_settings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String, nullable=False)
    device_id = db.Column(db.String, nullable=False)
    settings = db.Column(db.JSON, nullable=False)
    group_settings = db.Column(ARRAY(db.String), nullable=False,default=list,server_default='{}')  # リスト型に変更
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("device_id"),
    )
