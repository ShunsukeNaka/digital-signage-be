from datetime import datetime
from . import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    explanation = db.Column(db.String(255), nullable=False)
    registrated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Device 側の product relationship を自動生成する backref
    devices = db.relationship('Device', backref='product', lazy=True)
