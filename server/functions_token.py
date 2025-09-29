from .common import *
from .functions_times import get_now_str

def add_token(user_id, device_id=None, token_type="login"):
    check_token = Token.query.filter_by(
        user_id=user_id,
        device_id=device_id,
        token_type=token_type
    ).first()

    if check_token:
        if token_type == "login" or "device_update":
            cleanup_expired_login_tokens()
            check_token.token = uuid.uuid4()
            check_token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            db.session.commit()
            db.session.refresh(check_token)
            return check_token
        return check_token  # device, device_update

    # 新規作成
    gene_token = uuid.uuid4()
    token = Token(
        user_id=user_id,
        device_id=device_id,  # None でも DB が許容する場合
        token_type=token_type,
        token=gene_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db.session.add(token)
    db.session.commit()
    db.session.refresh(token)
    return token


# def check_token(token, token_type):
#     check_token = Token.query.filter_by(token_type=token_type, token=token).first()

#     if check_token is None:
#         abort(404, description="Token is None")

#     if check_token.expires_at < datetime.now(timezone.utc) and check_token.token_type != "device":
#         print(check_token.expires_at, datetime.now(timezone.utc))
#         if token_type == "device_update":
#             return False
#         abort(404, description="Tokenが切れています")

#     return check_token

def check_token(token, token_type):
    check_token = Token.query.filter_by(token_type=token_type, token=token).first()

    if check_token is None:
        abort(404, description="Token is None")

    if check_token.expires_at < datetime.now(timezone.utc) and check_token.token_type != "device":
        print(check_token.expires_at, datetime.now(timezone.utc))
        if token_type == "device_update":
            return jsonify({
                "status": "error",
                "responded_at": get_now_str(),
                "message": "device_update token expired"
            }), 403
        abort(404, description="Tokenが切れています")

    return check_token


def generate_onetime_token_id():
    return uuid.uuid4()

def cleanup_expired_login_tokens():
    # login トークンで期限切れのものを取得
    expired_tokens = Token.query.filter(
        Token.token_type == "login",
        Token.expires_at < get_now_str()
    ).all()

    # 削除
    for token in expired_tokens:
        db.session.delete(token)

    db.session.commit()
    return len(expired_tokens)  
