import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime
from . import db


class DeviceGroup(db.Model):
    __tablename__ = "device_group"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(
        db.String,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    explanation = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("id", name="uq_device_group_id"),
    )
