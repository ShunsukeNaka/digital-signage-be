from datetime import datetime
from werkzeug.security import generate_password_hash

# 現在 UTC 時間
created_at = datetime.utcnow()
print("UTC datetime:", created_at)

# パスワードのハッシュ化
password = "XUREHP0GiuZk"
hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
print("Hashed password:", hashed_password)
