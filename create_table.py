import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

# .env の読み込み
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ユーザーテーブル
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    logined_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

# コンテンツテーブル
class Content(db.Model):
    __tablename__ = 'contents'
    
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    explanation = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    # Userモデルとのリレーション
    user = db.relationship('User', backref=db.backref('contents', lazy=True))

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    explanation = db.Column(db.String(255), nullable=False)
    registrated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    devices = db.relationship('Device', backref='product', lazy=True)

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    explanation = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.String, db.ForeignKey('products.id'), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('devices', lazy=True))

class OneTimeToken(db.Model):
    __tablename__ = 'onetimetokens'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    expires_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.utcnow() + timedelta(hours=1))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("テーブル作成完了！")
