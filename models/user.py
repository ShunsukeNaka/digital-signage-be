from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)  # ←追加
    logined_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    # パスワード設定
    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password, method='pbkdf2:sha256', salt_length=16)

    # パスワードチェック
    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)
