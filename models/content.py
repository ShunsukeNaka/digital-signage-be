from datetime import datetime
from . import db

class Content(db.Model):
    __tablename__ = 'contents'
    
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    explanation = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String, nullable=False)
    
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    # リレーション
    user = db.relationship('User', backref=db.backref('contents', lazy=True))
