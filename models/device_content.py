from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint
from . import db


class DeviceContent(db.Model):
    __tablename__ = "device_content"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(
        db.String,
        db.ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False
    )
    content_id = db.Column(
        db.String,
        db.ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False
    )
    seted_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("device_id", name="uq_device"),
    )
