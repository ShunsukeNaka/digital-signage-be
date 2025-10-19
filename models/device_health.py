from datetime import datetime
from . import db

class DeviceHealth(db.Model):
    __tablename__ = "device_healths"

    device_id = db.Column(db.String, db.ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)
    latest_connectedAt = db.Column("latest_connectedat", db.DateTime(timezone=True), nullable=False)  # ←ここ！
    status = db.Column(db.String(50))
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
