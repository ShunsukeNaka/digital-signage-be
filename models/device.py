from datetime import datetime
from . import db

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    explanation = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.String, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id'), db.UniqueConstraint('product_id'))

    user = db.relationship('User', backref=db.backref('devices', lazy=True))
