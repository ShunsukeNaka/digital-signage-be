from flask import Flask, send_file, request, jsonify, abort
from flask_cors import CORS  # 追加
from flask_restx import Resource, Api
import os
import uuid
import mimetypes
import pytz
import json
from PIL import Image
import cv2
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
from sqlalchemy import or_
from models import db
from models.user import User
from models.device import Device
from models.content import Content
from models.product import Product
from models.update_device import UpdateDevice
from models.device_content import DeviceContent
from models.onetimetoken import OneTimeToken
from models.tokens import Token
from models.device_setting import DeviceSetting


# Flaskアプリ作成
flask_app = Flask(__name__)
flask_app.config.from_object('config')  # config.pyを読み込み
flask_app.config['CONTENTS_DIR'] = './datas/contents'
flask_app.config['THUMBNAILS_DIR'] = './datas/thumbnails'
db.init_app(flask_app)
# CORS有効化
CORS(flask_app)

# WSGI互換用
application = flask_app

def get_jst_time():
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst)

def get_now_str():
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

def UtcGmt2JST(time: str):
    jst = pytz.timezone('Asia/Tokyo')

    if isinstance(time, str):
        # 文字列を datetime に変換（UTC と仮定）
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        time = time.replace(tzinfo=pytz.utc)
        
    if time.tzinfo is None:
        # naive datetime は UTC と仮定
        time = time.replace(tzinfo=pytz.utc)
    return time.astimezone(jst).strftime("%Y-%m-%d %H:%M:%S")

UPDATE_INDEX_CONTENT_SET=1
UPDATE_INDEX_DEVICENAME_CHANGE=2
UPDATE_INDEX_DEVICETOKEN_CHANGE=3

ALLOWED_EXTENSIONS_IMG = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXTENSIONS_MOV = {'mp4', 'mov'}
# ALLOWED_EXTENSIONS_PPT = {'ppt', 'pptx'}
ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS_IMG.union(ALLOWED_EXTENSIONS_MOV)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def change_filename(file, newfilename):
    _, ext = os.path.splitext(file.filename)
    return secure_filename(f"{newfilename}{ext}")

def check_content_type(file):
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower().lstrip('.')
    ext = ext.lower()
    if ext in ALLOWED_EXTENSIONS_IMG:
        return 'image'
    if ext in ALLOWED_EXTENSIONS_MOV:
        return 'video'
    # if ext in ALLOWED_EXTENSIONS_PPT:
    #     return 'powerpoint'
    return 'NOTALLOWEDTYPE'

def check_content_type_forPath(filepath):
    _, ext = os.path.splitext(filepath)
    ext = ext.lower().lstrip('.')
    ext = ext.lower()
    if ext in ALLOWED_EXTENSIONS_IMG:
        return 'image'
    if ext in ALLOWED_EXTENSIONS_MOV:
        return 'video'
    # if ext in ALLOWED_EXTENSIONS_PPT:
    #     return 'powerpoint'
    return 'NOTALLOWEDTYPE'

def check_content_type_forPath_ext(filepath):
    _, ext = os.path.splitext(filepath)
    ext = ext.lower().lstrip('.')
    ext = ext.lower()
    if ext in ALLOWED_EXTENSIONS_IMG:
        return ext
    if ext in ALLOWED_EXTENSIONS_MOV:
        return ext
    # if ext in ALLOWED_EXTENSIONS_PPT:
    #     return 'powerpoint'
    return 'NOTALLOWEDTYPE'

# def get_content_path(content_id):
#     content_dir = './datas/contents/'
#     # ファイルパスを探索（拡張子は任意）
#     possible_files = [f for f in os.listdir(content_dir) if f.startswith(content_id + ".")]
#     if not possible_files:
#         return None
    
#     file_path = os.path.join(content_dir, possible_files[0])
#     return file_path

def get_content_path(content_id):
    content_dir = './datas/contents/'
    # ファイルパスを探索（拡張子は任意）
    possible_files = [f for f in os.listdir(content_dir) if f.startswith(content_id + ".")]
    if not possible_files:
        return None
    
    file_path = os.path.join(content_dir, possible_files[0])
    return file_path

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


def create_square_thumbnail(input_path, output_path,size: int = 300, video_frame_sec: float = 1.0):
    """
    画像 or 動画ファイルから中央正方形サムネイルを作成する。

    Parameters
    ----------
    input_path : str
        入力ファイルパス（画像 or 動画）
    output_path : str
        出力するサムネイル画像ファイルパス
    size : int
        出力サムネイルの一辺のピクセル数
    video_frame_sec : float
        動画の場合に切り出す秒位置
    """

    # 判定用の拡張子セット
    img_exts = {'.png', '.jpg', '.jpeg', '.gif'}
    vid_exts = {'.mp4', '.mov'}

    ext = os.path.splitext(input_path)[1].lower()

    if ext in img_exts:
        # ----- 画像 -----
        with Image.open(input_path) as img:
            w, h = img.size
            min_side = min(w, h)
            left   = (w - min_side) // 2
            top    = (h - min_side) // 2
            right  = left + min_side
            bottom = top + min_side
            img_cropped = img.crop((left, top, right, bottom))
            img_cropped = img_cropped.resize((size, size), Image.LANCZOS)
            img_cropped.save(output_path)

    elif ext in vid_exts:
        # ----- 動画 -----
        cap = cv2.VideoCapture(input_path)
        cap.set(cv2.CAP_PROP_POS_MSEC, video_frame_sec * 1000)
        success, frame = cap.read()
        cap.release()
        if not success:
            raise RuntimeError("動画フレームを取得できませんでした。")

        h, w, _ = frame.shape
        min_side = min(w, h)
        left   = (w - min_side) // 2
        top    = (h - min_side) // 2
        square = frame[top:top+min_side, left:left+min_side]
        square = cv2.resize(square, (size, size))
        cv2.imwrite(output_path, square)

    else:
        raise ValueError(f"対応していない拡張子です: {ext}")



# def add_token(user_id, device_id, token_type):
#     check_token = Token.query.filter_by(
#         user_id=user_id,
#         device_id=device_id,
#         token_type=token_type
#     ).first()

#     if check_token:
#         if token_type == "login":
#             cleanup_expired_login_tokens()
#             # 既存トークンを更新する
#             gene_token = uuid.uuid4()
#             check_token.token = gene_token
#             db.session.commit()
#             db.session.refresh(check_token)
#             return check_token
#         elif token_type == "device":
#             # 既存なら何もしない
#             return check_token
#         elif token_type == "device_update":
#             # 既存なら何もしない
#             return check_token

#     # 新しいトークンを作成する場合
#     gene_token = uuid.uuid4()
#     token = Token(user_id=user_id, device_id=device_id, token_type=token_type, token=gene_token)
#     db.session.add(token)
#     db.session.commit()
#     db.session.refresh(token)
#     return token

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


def update_device_true(user_id, device_id, UPDATE_INDEX):
    try:
        check_device = UpdateDevice.query.filter_by(user_id=user_id, device_id=device_id).first()
        user = User.query.filter_by(id=user_id).first()
        device = Device.query.filter_by(id=device_id).first()

        if user is None or device is None:
            return False

        if check_device is None:
            update_index = list("00000000")
            update_index[UPDATE_INDEX] = "1"
            update_index = "".join(update_index)

            updatedevice = UpdateDevice(
                user_id=user_id,
                device_id=device_id,
                update=True,
                update_index=update_index
            )
            db.session.add(updatedevice)
            db.session.commit()
            db.session.refresh(updatedevice)
        else:
            update_index = list(check_device.update_index)
            update_index[UPDATE_INDEX] = "1"
            check_device.update_index = "".join(update_index)
            check_device.update = True
            db.session.commit()
        return True
    except Exception as e:
        print(f"update_device_true error: {e}")
        return False


# def update_device_true(user_id, device_id, UPDATE_INDEX):
#     try:
#         check_device = UpdateDevice.query.filter_by(user_id=user_id, device_id=device_id).first()
#         user = User.query.filter_by(id=user_id).first()
#         device = Device.query.filter_by(id=device_id).first()

        

#         if check_device is None:
#             if user is not None and device is not None:
#                 with flask_app.app_context():
#                     update_index = "00000000"
#                     update_index[UPDATE_INDEX] = "1"

#                     updatedevice = UpdateDevice(user_id=user_id, device_id=device_id, update=True, update_index=update_index)
#                     db.session.add(updatedevice)
#                     db.session.commit()
#                     db.session.refresh(updatedevice)
#         else:
#             if user is not None and device is not None:
#                 with flask_app.app_context():
#                     check_device.update = True
#                     update_index = check_device.update_index
#                     update_index[UPDATE_INDEX] = "1"

#                     check_device.update_index = update_index
#                     db.session.commit()
#         return True
#     except Exception as e:
#         return jsonify({
#             "status": "error", "responded_at": get_now_str(),
#             "message": f'message: {e}'
#         }), 500

def update_device_false(user_id, device_id) -> bool:
    try:
        check_device = UpdateDevice.query.filter_by(user_id=user_id, device_id=device_id).first()
        user = User.query.filter_by(id=user_id).first()
        device = Device.query.filter_by(id=device_id).first()

        if check_device is None:
            print("IS NONE")
            return False
        else:
            if user is not None and device is not None:
                print("ELSE")
                # with flask_app.app_context():
                check_device.update = False
                check_device.update_index = "00000000"
                db.session.commit()
                db.session.refresh(check_device)
                return True   # ← 成功を表すブール値に統一
            else:
                return False
    except Exception as e:
        print(f"update_device_false error: {e}")
        return False
    
def check_update_device(user_id, device_id):
    try:
        check_device = UpdateDevice.query.filter_by(user_id=user_id, device_id=device_id).first()
        user = User.query.filter_by(id=user_id).first()
        device = Device.query.filter_by(id=device_id).first()
        if check_device is None:
            if user is not None and device is not None:
                with flask_app.app_context():
                    updatedevice = UpdateDevice(user_id=user_id, device_id=device_id, update=True, update_index="11111111")
                    db.session.add(updatedevice)
                    db.session.commit()
                    db.session.refresh(updatedevice)
                return updatedevice
        else:
            if user is not None and device is not None:
                return check_device
    except Exception as e:
        return jsonify({
            "status": "error", "responded_at": get_now_str(),
            "message": f'message: {e}'
        }), 500
        

# ルートのサンプル
@flask_app.route('/', methods=['GET'])
def index():
    return jsonify({
            "message": "Hello from Flask!",
            "responded_at": get_now_str()
        })


"""
ENDPOINT: login
POST /login:
    ・ログインを行う。
    ・全ユーザーが使用可能。

    -----RequestBody-----
    {
    	user: {
    		id: “”,
			pass: “”,
    	}
    }
    -----------------------

    user: 追加したいユーザーの情報

    -----ResponseBody-----
    {
        "status": string,
        "responded_at": get_now_str(),
        "user": {
            "id": string,
            "name": string,
            "token": string,
            "token_expires_at": string
        }
    }
    ----------------------

"""
@flask_app.route('/login', methods=['POST'])
def login():
    try:
        if request.method == 'POST':
            data = request.get_json()

            if not data or "user" not in data or "id" not in data["user"] or  "pass" not in data["user"]:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400           

            user_id = data["user"].get("id")
            user_password = data["user"].get("pass")

            # DataBaseからuserのデータを取得して照合
            user = User.query.filter_by(id=user_id).first()
            if user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404
            if not check_password_hash(user.password, user_password):
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "パスワードが一致しません"}), 401

            token=add_token(user_id=user_id, device_id=None, token_type="login")

            # jst = token.expires_at.astimezone(pytz.timezone("Asia/Tokyo"))
            jst = pytz.timezone("Asia/Tokyo")
            print(token.expires_at)
            print(jst)

            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "user": {
                    "id": user_id,
                    "name": user.name,
                    "token": token.token,
                    "token_expires_at": UtcGmt2JST(token.expires_at)
                }
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error", "responded_at": get_now_str(),
            "message": f'message: {e}'
        }), 500
    
"""
ENDPOINT: login/device
POST /login/device:
    ・デバイスからログインを行う。
    ・tokenを取得するために利用する
    ・全ユーザーが使用可能。

    -----RequestBody-----
    {
    	user: {
    		id: “”,
			pass: “”,
    	},
        device: {
            id: ""
        }
    }
    -----------------------

    user: ログインするユーザーの情報
    device: ログイン先のデバイスの情報

    -----ResponseBody-----
    {
        "status": string,
        "responded_at": get_now_str(),
        "user": {
            "id": string,
            "name": string
        },
        "device": {
            "id": string,
            "name": string
        },
        "token": uuid
    }
    ----------------------
"""
@flask_app.route('/login/device', methods=['POST'])
def login_device():
    try:
        if request.method == 'POST':
            data = request.get_json()

            if not data or "user" not in data or "id" not in data["user"] or "pass" not in data["user"] or "id" not in data["device"]:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400           

            user_id = data["user"].get("id")
            user_password = data["user"].get("pass")
            device_id = data["device"].get("id")

            # DataBaseからuserのデータを取得して照合
            user = User.query.filter_by(id=user_id).first()
            if user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404
            if not check_password_hash(user.password, user_password):
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "パスワードが一致しません"}), 401

            # DataBaseからDeviceのデータを取得して照合
            device = Device.query.filter_by(id=device_id, user_id=user_id).first()
            if device is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "デバイスが存在しません"}), 404
            
            token = add_token(user_id, device_id, "device")
            send_token = token.token
            if token == None:
                send_token = "NO_GENERATE_TOKEN"

            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "user": {
                    "id": user_id,
                    "name": user.name
                },
                "device": {
                    "id": device_id,
                    "name": device.name
                },
                "token": send_token
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error", "responded_at": get_now_str(),
            "message": f'message: {e}'
        }), 500

"""
ENDPOINT: user
POST /user:
    ・ユーザー情報の追加を行う。
    ・開発者用の管理者ユーザーのみが使用可能。
    -----RequestBody-----
    {
    	admin: {
			id: “”,
        	pass: “”
		}, 
    	user: {
    		id: “”,
			name: “”,
			pass: “” 
    	}
    }
    -----------------------

    admin: 管理者ユーザーの情報
    user: 追加したいユーザーの情報

    -----ResponseBody-----
    {
        "status": string,
        "responded_at": get_now_str(),
        "created_user": {
            "id": string,
            "name": string,
            "logined_at": datetime.utc,
            "created_at": datetime.utc
        }
    }
    ----------------------

"""
@flask_app.route('/user', methods=['POST'])
def user():
    try:
        if request.method == 'POST':
            data = request.get_json()

            if not data or "admin" not in data or "id" not in data["admin"] or "pass" not in data["admin"]:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            
            if not data or "user" not in data or "id" not in data["user"] or "name" not in data["user"] or  "pass" not in data["user"]:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400           

            admin_id = data["admin"].get("id")
            admin_password = data["admin"].get("pass")

            # DataBaseからadminのデータを取得して照合
            admin_user = User.query.filter_by(id=admin_id).first()
            if admin_user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404
            if not check_password_hash(admin_user.password, admin_password):
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "パスワードが一致しません"}), 401
            
            created_id = data["user"].get("id")
            created_name = data["user"].get("name")
            created_password = data["user"].get("pass")
            created_email = data["user"].get("email")
            created_at = get_now_str()

            hashed_password = generate_password_hash(created_password, method="pbkdf2:sha256", salt_length=16)

            with flask_app.app_context():
                existing_user = User.query.filter_by(email=created_email).first()
                if existing_user:
                    return jsonify({
                        "status": "error",
                        "message": "このメールアドレスは既に使われています。",
                        "responded_at": get_now_str()
                    }), 400
                existing_user = User.query.filter_by(id=created_id).first()
                if existing_user:
                    return jsonify({
                        "status": "error",
                        "message": "このユーザーIDは既に使われています。",
                        "responded_at": get_now_str()
                    }), 400
                
                user = User(id=created_id, name=created_name, password=hashed_password, email=created_email, logined_at=created_at, created_at=created_at)


                db.session.add(user)
                db.session.commit()

            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "created_user": {
                    "id": created_id,
                    "name": created_name,
                    "email": created_email,
                    "logined_at": created_at,
                    "created_at": created_at
                }
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error", "responded_at": get_now_str(),
            "message": f'message: {e}'
        }), 500
    

"""
ENDPOINT: signup
POST /signup:
    ・ユーザー情報の追加を行う。
    ・全員が使用可能。
    -----RequestBody-----
    { 
    	user: {
    		id: “”,
			name: “”,
			pass: “” 
    	}
    }
    -----------------------

    user: 追加したいユーザーの情報

    -----ResponseBody-----
    {
        "status": string,
        "responded_at": get_now_str(),
        "created_user": {
            "id": string,
            "name": string,
            "logined_at": datetime.utc,
            "created_at": datetime.utc
        }
    }
    ----------------------

"""
@flask_app.route('/signup', methods=['POST'])
def signup():
    try:
        if request.method == 'POST':
            data = request.get_json()

            if not data or "user" not in data or "id" not in data["user"] or "name" not in data["user"] or "pass" not in data["user"] or "email" not in data["user"]:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400           

            created_id = data["user"].get("id")
            created_name = data["user"].get("name")
            created_password = data["user"].get("pass")
            created_email = data["user"].get("email")
            created_at = get_now_str()

            hashed_password = generate_password_hash(created_password, method="pbkdf2:sha256", salt_length=16)

            with flask_app.app_context():
                existing_user = User.query.filter_by(email=created_email).first()
                if existing_user:
                    return jsonify({
                        "status": "error",
                        "message": "このメールアドレスは既に使われています。",
                        "responded_at": get_now_str()
                    }), 409
                existing_user = User.query.filter_by(id=created_id).first()
                if existing_user:
                    return jsonify({
                        "status": "error",
                        "message": "このユーザーIDは既に使われています。",
                        "responded_at": get_now_str()
                    }), 409
                
                user = User(id=created_id, name=created_name, password=hashed_password, email=created_email, logined_at=created_at, created_at=created_at)

                db.session.add(user)
                db.session.commit()

            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "created_user": {
                    "id": created_id,
                    "name": created_name,
                    "email": created_email,
                    "logined_at": created_at,
                    "created_at": created_at
                }
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error", "responded_at": get_now_str(),
            "message": f'message: {e}'
        }), 500

@flask_app.route('/content', methods=['POST', 'DELETE'])
def content():
    try:
        if request.method == 'POST':

            if 'file' not in request.files:
                return jsonify({"status": "error", "message": "ファイルがありません"}), 400

            if not request.form or "file" not in request.files or "content_id" not in request.form or "content_name" not in request.form or "content_explanation" not in request.form:
                return jsonify({"error": "Invalid multipart form", "responded_at": get_now_str()}), 400

            get_token = request.form.get("token")

            check_token(get_token, "login")

            token = Token.query.filter_by(token=get_token, token_type="login").first()

            file = request.files['file']
            user_id = token.user_id
            # user_pass = request.form.get("user_pass")
            content_id = request.form.get("content_id")
            content_name = request.form.get("content_name")
            content_explanation = request.form.get("content_explanation")
            content_type = request.form.get("content_type")

            if file.filename == '':
                return jsonify({"status": "error", "message": "ファイル名が空です"}), 400
            
            if content_id == '':
                content_id = f'{user_id}-{uuid.uuid4()}'
            
            if content_name == '':
                content_name = content_id

            content_type = check_content_type(file)
            if content_type == 'NOTALLOWEDTYPE':
                return jsonify({"status": "error", "message": "許可されていないファイル形式です"}), 400
            

            # DataBaseからデータを取得して照合
            # user = User.query.filter_by(id=user_id).first()
            # if user is None:
            #     return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404
            # if not check_password_hash(user.password, user_pass):
            #     return jsonify({"status": "error", "responded_at": get_now_str(), "message": "パスワードが一致しません"}), 401
            
            content = Content.query.filter_by(id=content_id).first()
            if content is not None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "同じコンテンツIDが存在しています"}), 409
            
            if file and allowed_file(file.filename):
                filename = secure_filename(change_filename(file, content_id))
                save_path = os.path.join(flask_app.config['CONTENTS_DIR'], filename)
                thumbnail_path = os.path.join(flask_app.config['THUMBNAILS_DIR'], secure_filename(f"{content_id}.png"))
                file.save(save_path)

                print(save_path)
                print(thumbnail_path)

                create_square_thumbnail(input_path=save_path, output_path=thumbnail_path)
                # return jsonify({"status": "success", "filename": filename}), 200
            else:
                return jsonify({"status": "error", "message": "許可されていないファイル形式です"}), 400
            
            add_content = Content(
                id=content_id, 
                name=content_name, 
                type=content_type,
                explanation=content_explanation, 
                user_id=user_id
            )
            db.session.add(add_content)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "user": {
                    "id": user_id,
                },
                "content": {
                    "id": content_id,
                    "name": content_name,
                    "explanation": content_explanation,
                    "type": content_type,
                    "url": f"http://fukutech.kinulab.org/dsbe/send_content?id={content_id}"
                }
            }), 200
        if request.method == 'DELETE':

            data = request.get_json()
            if not data or "token" not in data or "content_id" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400

            token_value = data.get("token")
            result = check_token(token_value, "login")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result

            content_id = data.get("content_id")
            content = Content.query.filter_by(id=content_id, user_id=token.user_id).first()
            if not content:
                return jsonify({"status": "error", "message": "コンテンツが存在しません"}), 404

            # ファイル削除
            file_path = get_content_path(content_id)
            if not file_path:
                return jsonify({"status": "error", "message": "ファイルが存在しません"}), 404

            if os.path.exists(file_path):
                os.remove(file_path)

            db.session.delete(content)
            db.session.commit()

            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "deleted_content_id": content_id
            }), 200
    except Exception as e:
        db.session.rollback()

        if 'save_path' in locals() and os.path.exists(save_path):
            os.remove(save_path)

        return jsonify({
            "status": "error", "responded_at": get_now_str(),
            "message": f'message: {e}'
        }), 500

@flask_app.route('/content/get', methods=['GET','POST'])
def get_content():
    try:
        if request.method == 'POST':
        
            data = request.get_json()
            if "token" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            
            if not data or "content" not in data or "id" not in data["content"]:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400

            token_value = data.get("token")
            result = check_token(token_value, "login")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result

            user_id = token.user_id
            content_id = data["content"].get('id')

            # DataBaseからuserのデータを取得して照合
            user = User.query.filter_by(id=user_id).first()
            if user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404

            file_path = get_content_path(content_id) 
            # _, ext = os.path.splitext(file_path)
            token = generate_onetime_token_id()

            with flask_app.app_context():
                one_time_token = OneTimeToken(id=token, user_id=user_id, created_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc) + timedelta(hours=1))

                db.session.add(one_time_token)
                db.session.commit()


            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "user": {
                    "id": user_id,
                },
                "content": {
                    "id": content_id,
                    "type": check_content_type_forPath(file_path),
                    "url": f"http://fukutech.kinulab.org/dsbe/send_content?id={content_id}",
                    "token": token
                }
            })
    except Exception as e:
            return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500
    return jsonify({"status": "error", "responded_at": get_now_str()}), 405

@flask_app.route('/content/get/device', methods=['POST'])
def get_content_device():
    try:
        if request.method == 'POST':
        
            data = request.get_json()
            if "token" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            
            if not data or "content" not in data or "id" not in data["content"]:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400

            token_value = data.get("token")
            result = check_token(token_value, "device")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result

            user_id = token.user_id
            content_id = data["content"].get('id')

            # DataBaseからuserのデータを取得して照合
            user = User.query.filter_by(id=user_id).first()
            if user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404

            file_path = get_content_path(content_id) 
            # _, ext = os.path.splitext(file_path)
            token = generate_onetime_token_id()

            with flask_app.app_context():
                one_time_token = OneTimeToken(id=token, user_id=user_id, created_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc) + timedelta(hours=1))

                db.session.add(one_time_token)
                db.session.commit()


            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "user": {
                    "id": user_id,
                },
                "content": {
                    "id": content_id,
                    "type": check_content_type_forPath(file_path),
                    "url": f"http://fukutech.kinulab.org/dsbe/send_content/device?id={content_id}",
                    "token": token
                }
            })
    except Exception as e:
            return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500
    return jsonify({"status": "error", "responded_at": get_now_str()}), 405

@flask_app.route('/contents/get', methods=['POST'])
def get_contents():
    try:
        if request.method == 'POST':
            data = request.get_json()
            if "token" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            
            token_value = data.get("token")
            result = check_token(token_value, "login")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result
            
            user_id = token.user_id

            # DataBaseからuserのデータを取得して照合
            user = User.query.filter_by(id=user_id).first()
            if user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404
          
            # DataBaseからcontentのデータを取得して照合
            contents = Content.query.filter_by(user_id=user_id).all()


            # contents = [
            #     {
            #         "id": "sampleimage",
            #         "thumbnail_url": "http://fukutech.kinulab.org/dsbe/send_thumbnail?id=sampleimage",
            #         "title": "テストデータ１",
            #         "created_at": "2025-08-13T01:01:10.393510+09:00"
            #     },
            #     {
            #         "id": "sampleimage2",
            #         "thumbnail_url": "http://fukutech.kinulab.org/dsbe/send_thumbnail?id=sampleimage2",
            #         "title": "テストデータ２",
            #         "created_at": "2025-08-10T04:01:10.393510+09:00"
            #     },
            #     {
            #         "id": "sampleimage3",
            #         "thumbnail_url": "http://fukutech.kinulab.org/dsbe/send_thumbnail?id=sampleimage3",
            #         "title": "テストデータ３",
            #         "created_at": "2025-08-11T06:23:10.393510+09:00"
            #     },
            # ]

            contents_list = [
            {
                "id": c.id,
                "thumbnail_url": f"http://fukutech.kinulab.org/dsbe/send_thumbnail?id={c.id}",
                "name": c.name,
                "explanation": c.explanation,
                "created_at": c.created_at
            }
            for c in contents
        ]

            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "user": {
                    "id": user_id,
                },
                "contents": contents_list
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error", "responded_at": get_now_str(),
            "message": f'message: {e}'
        }), 500

@flask_app.route('/send_content', methods=["GET"])
def send_content():
    if request.method == 'GET':
        try:
            if request.args.get('id') is None:
                return jsonify({"error": "it has no query"}), 400
            
            content_id = request.args.get('id')
            user_id = request.args.get('user_id')
            token = request.args.get('token')

            user = User.query.filter_by(id=user_id).first()
            if user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404

            now = get_jst_time()
            now_utc = datetime.now(pytz.utc)
            used_token = OneTimeToken.query.filter(
                OneTimeToken.id==token,
                OneTimeToken.user_id==user_id,
                OneTimeToken.expires_at >= datetime.now(pytz.timezone("Asia/Tokyo"))
            ).first()

            if not used_token:
                return jsonify({"status": "error", "message": "無効なトークンです"}), 401

            file_path = get_content_path(content_id)
            mimetype, _ = mimetypes.guess_type(file_path)
            
            
            db.session.delete(used_token)
            db.session.commit()
            
            return send_file(file_path, mimetype=mimetype)
        except Exception as e:
            return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500
    return jsonify({"status": "error", "responded_at": get_now_str()}), 405

@flask_app.route('/send_content/device', methods=["GET"])
def send_content_device():
    if request.method == 'GET':
        try:
            if request.args.get('id') is None:
                return jsonify({"error": "it has no query"}), 400
            
            content_id = request.args.get('id')
            device_token = request.args.get('device_token')
            token = request.args.get('token')

            token_value = request.args.get('device_token')
            result = check_token(token_value, "device")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            device_token = result
            
            user_id = device_token.user_id
            
            user = User.query.filter_by(id=user_id).first()
            if user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404

            now = get_jst_time()
            now_utc = datetime.now(pytz.utc)
            used_token = OneTimeToken.query.filter(
                OneTimeToken.id==token,
                OneTimeToken.user_id==user_id,
                OneTimeToken.expires_at >= datetime.now(pytz.timezone("Asia/Tokyo"))
            ).first()

            if not used_token:
                return jsonify({"status": "error", "message": "無効なトークンです"}), 401

            file_path = get_content_path(content_id)
            mimetype, _ = mimetypes.guess_type(file_path)
            
            
            db.session.delete(used_token)
            db.session.commit()
            
            return send_file(file_path, mimetype=mimetype)
        except Exception as e:
            return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500
    return jsonify({"status": "error", "responded_at": get_now_str()}), 405

@flask_app.route('/send_thumbnail', methods=["GET"])
def send_thumbnail():
    if request.method == 'GET':
        try:
            if request.args.get('id') is None:
                return jsonify({"error": "it has no query"}), 400
            
            content_id = request.args.get('id')
            file_path = f'./datas/thumbnails/{content_id}.png'

            # ファイルの存在チェック
            if not os.path.exists(file_path):
                file_path = './datas/thumbnails/no_thunmbnail.png'
                # return jsonify({"error": "file not found"}), 404
            
            return send_file(
                file_path,
                mimetype="image/png"
            )
        except Exception as e:
            return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500
    return jsonify({"status": "error", "responded_at": get_now_str()}), 405

@flask_app.route('/device/get', methods=['POST'])
def get_device():
    try:
        if request.method == 'POST':
            data = request.get_json()

            if not data or "token" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            if not data or "search" not in data or "device_id" not in data["search"] or "and" not in data["search"] or "device_name" not in data["search"] or "product_id" not in data["search"] or "product_name" not in data["search"]:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400

            token_value = data.get("token")
            result = check_token(token_value, "login")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result
            
            user_id = token.user_id
            and_flg = data["search"].get("and")
            device_id = data["search"].get("device_id")
            device_name = data["search"].get("device_name")
            product_id = data["search"].get("product_id")
            product_name = data["search"].get("product_name")

            # DataBaseからデータを取得して照合
            user = User.query.filter_by(id=user_id).first()
            if user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404
            
            # product = Product.query.filter_by(id=product_id).first()
            # if product is None:
            #     return jsonify({"status": "error", "responded_at": get_now_str(), "message": "製品が存在しません"}), 404
            
            # DataBaseからDeviceのデータを取得して照合
            search_device_products = Product.query.filter(Product.name.like(f"%{product_name}%")).all()
            product_ids = [p.id for p in search_device_products]
            product_ids.append(product_id)

            if and_flg:
                filters = [Device.user_id == user_id]

                if device_id:
                    filters.append(Device.id.like(f"%{device_id}%"))
                if device_name:
                    filters.append(Device.name.like(f"%{device_name}%"))
                if product_id:
                    filters.append(Device.product_id.like(f"%{product_id}%"))
                if product_ids:  # product_name から取得したIDリスト
                    filters.append(Device.product_id.in_(product_ids))

                devices = Device.query.filter(*filters).all()
            else:
                # query = Device.query.filter(Device.user_id == user_id)

                user_filter = Device.user_id == user_id
                or_filters = []
                if device_id:
                    or_filters.append(Device.id.like(f"%{device_id}%"))
                if device_name:
                    or_filters.append(Device.name.like(f"%{device_name}%"))
                if product_id:
                    or_filters.append(Device.product_id.like(f"%{product_id}%"))
                if product_ids:
                    or_filters.append(Device.product_id.in_(product_ids))

                devices = Device.query.filter(user_filter).filter(or_(*or_filters)).all()
                # devices = query.all()
            
            device_list = []
            product_ids_set = set()
            product_list = []
            for d in devices:
                device_list.append({
                    "id": d.id,
                    "name": d.name,
                    "explanation": d.explanation,
                    "user_id": d.user_id,
                    "product_id": d.product_id,
                    "updated_at": d.updated_at.isoformat() if d.updated_at else None,
                    "created_at": d.created_at.isoformat() if d.created_at else None
                })
                product_ids_set.add(d.product_id)  # ユニークな product_id を集める

                # product_id に対応する Product を取得
                products = Product.query.filter(Product.id.in_(list(product_ids_set))).all()

                # Product を辞書に変換
                for p in products:
                    product_list.append({
                        "id": p.id,
                        "name": p.name
                    })


            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "user": {
                    "id": user_id,
                },
                "device": device_list,
                "search": {
                    "and": and_flg,
                    "device_id": device_id,
                    "device_name": device_name,
                    "product_id": product_id,
                    "product_name": product_name
                },
                "product": product_list
            }), 200
    except Exception as e:
        return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500

@flask_app.route('/device', methods=['POST', 'DELETE'])
def device():
    try:
        if request.method == 'POST':
            data = request.get_json()

            if not data or "token" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            
            if not data or "device" not in data or "id" not in data["device"] or "name" not in data["device"] or "explanation" not in data["device"] or "product_id" not in data["device"]:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            
            token_value = data.get("token")
            result = check_token(token_value, "login")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result

            user_id = token.user_id
            device_id = data["device"].get("id")
            device_name = data["device"].get("name")
            device_explanation = data["device"].get("explanation")
            product_id = data["device"].get("product_id")

            # DataBaseからデータを取得して照合
            user = User.query.filter_by(id=user_id).first()
            if user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404

            product = Product.query.filter_by(id=product_id).first()
            if product is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "製品が存在しません"}), 404
            
            # DataBaseからDeviceのデータを取得して照合
            add_device = Device.query.filter_by(id=device_id).first()
            if add_device is not None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "同じIDのデバイスが存在しています"}), 406
            
            with flask_app.app_context():
                device = Device(id=device_id, name=device_name, explanation=device_explanation, user_id=user.id, product_id=product.id)

                db.session.add(device)
                db.session.commit()
            
            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "user": {
                    "id": user_id,
                },
                "device": {
                    "id": device_id,
                    "name": device_name,
                    "explanation": device_explanation,
                    "type": product_id
                }
            }), 200
        if request.method == 'DELETE':
            data = request.get_json()
            if not data or "token" not in data or "device_id" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400

            token_value = data.get("token")
            result = check_token(token_value, "login")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result

            device_id = data.get("device_id")
            device = Device.query.filter_by(id=device_id, user_id=token.user_id).first()
            if not device:
                return jsonify({"status": "error","responded_at": get_now_str(), "message": "デバイスが存在しません"}), 404
            
            db.session.delete(device)
            db.session.commit()
            

            return jsonify({
                "status": "success",
                "user": {
                    "id": token.user_id
                },
                "responded_at": get_now_str(),
                "deleted_content_id": device_id
            }), 200
    except Exception as e:
        return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500


@flask_app.route('/device/content/set', methods=['POST'])
def device_content_set():
    try:
        if request.method == 'POST':
            data = request.get_json()

            # if not data or "token" not in data or "device_id" not in data or "content_id" not in data:
            

            token = data.get("token")
            device_id = data.get("device_id")
            settings = data.get("settings")

            if not token or not device_id or not settings:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            # content_id = data.get("content_id")
            # device_id = data.get("device_id")

            token_value = data.get("token")
            result = check_token(token_value, "login")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result

            searched_token = Token.query.filter_by(user_id=token.user_id).first()
            device = Device.query.filter_by(id=device_id).first()
            
            with flask_app.app_context():
                # まず既存のレコードを取得
                device_setting = DeviceSetting.query.filter_by(device_id=device_id).first()

                if device_setting:
                    # 既存レコードがあれば更新
                    device_setting.token = token.token
                    device_setting.settings = settings  # JSONBなら dict のままでOK
                else:
                    # なければ新規作成
                    device_setting = DeviceSetting(
                        token=token.token,
                        device_id=device_id,
                        settings=settings
                    )
                    db.session.add(device_setting)

                db.session.commit()

          
            update_device_true(searched_token.user_id, device_id, UPDATE_INDEX_CONTENT_SET)
            
            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "device": device.id,
                "settings": settings
            }), 200

    except Exception as e:
        return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500

@flask_app.route('/device/content/get', methods=['POST'])
def device_content_get():
    try:
        data = request.get_json()
        token = data.get("token")
        device_id = data.get("device_id")

        if not token or not device_id:
            return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400

        # トークンチェック
        result = check_token(token, "login")
        if not isinstance(result, Token):
            return result
        checked_token = result

        # デバイス取得
        device = Device.query.filter_by(id=device_id).first()
        if not device:
            return jsonify({"error": "Device not found", "responded_at": get_now_str()}), 404

        # 設定取得（ORM）
        device_setting = DeviceSetting.query.filter_by(device_id=device_id).first()

        if not device_setting:
            return jsonify({
                "status": "no_settings",
                "responded_at": get_now_str(),
                "device": device.id,
                "settings": None
            }), 200

        return jsonify({
            "status": "success",
            "responded_at": get_now_str(),
            "device": device.id,
            "settings": device_setting.settings  # JSONBはdictとして返る
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "responded_at": get_now_str(),
            "message": f'message: {e}'
        }), 500

@flask_app.route('/device/content/get/device', methods=['POST'])
def device_content_get_device():
    try:
        data = request.get_json()
        token = data.get("token")

        if not token:
            return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400

        # トークンチェック
        result = check_token(token, "device")
        if not isinstance(result, Token):
            return result
        checked_token = result

        device_id = checked_token.device_id

        # デバイス取得
        device = Device.query.filter_by(id=device_id).first()
        if not device:
            return jsonify({"error": "Device not found", "responded_at": get_now_str()}), 404

        # 設定取得（ORM）
        device_setting = DeviceSetting.query.filter_by(device_id=device_id).first()


        if device_setting and device_setting.settings:
            settings = device_setting.settings  # dict
            contents = settings.get("contents", [])

        # contents の各要素に ext を追加
        for content in contents:
            content_id = content.get("id")
            if content_id:
                path = get_content_path(content_id)
                if path is None:
                    return jsonify({"error": "File not found", "responded_at": get_now_str()}), 404
                ext = check_content_type_forPath_ext(path)
                content["ext"] = ext

        if not device_setting:
            return jsonify({
                "status": "no_settings",
                "responded_at": get_now_str(),
                "device": device.id,
                "settings": None
            }), 200

        return jsonify({
            "status": "success",
            "responded_at": get_now_str(),
            "device": device.id,
            "settings": {
                "type": device_setting.settings.get("type"),
                "created_at": device_setting.created_at,
                "contents":contents # device_setting.settings  # JSONBはdictとして返る
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "responded_at": get_now_str(),
            "message": f'message: {e}'
        }), 500    

@flask_app.route('/check_update', methods=['POST'])
def checkupdate():
    try:
        if request.method == 'POST':
            data = request.get_json()

            if not data or "token" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            
            token_value = data.get("token")
            result = check_token(token_value, "device")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result

            # DataBaseからデータを取得して照合
            # token = Token.query.filter_by(token=token).first()
            checked_token = token

            user_id = checked_token.user_id
            device_id = checked_token.device_id

            update_device = check_update_device(user_id=user_id, device_id=device_id)
            
            device_update_token = add_token(user_id=user_id, device_id=device_id, token_type="device_update")

            return jsonify({
                "status": "success", 
                "responded_at": get_now_str(), 
                "update_device":{
                    "update": update_device.update,
                    "update_index": update_device.update_index,
                    "updated_at": update_device.updated_at,
                    "device_update_token": device_update_token.token
                }
            }), 200
    except Exception as e:
        return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500
    
@flask_app.route('/check_update/return', methods=['POST'])
def checkupdate_return():
    try:
        if request.method == 'POST':
            data = request.get_json()

            if not data or "device_update_token" not in data or "token" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            
            token_value = data.get("token")
            result = check_token(token_value, "device")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result

            token_value = data.get("device_update_token")
            result = check_token(token_value, "device_update")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            update_token = result

            user_id = update_token.user_id
            device_id = update_token.device_id
            check_device = update_device_false(user_id=user_id, device_id=device_id)

            # update_device = check_update_device(user_id=user_id, device_id=device_id)
            
            # device_update_token = add_token(user_id=user_id, device_id=device_id, token_type="device_update")

            if check_device is True:
                return jsonify({
                    "status": "success", 
                    "responded_at": get_now_str(), 
                }), 200
            else:
                return jsonify({
                    "status": "error", 
                    "responded_at": get_now_str(), 
                    "up": update_token.user_id,
                    "up2": update_token.device_id,
                    "message": 'token is Failed'
                }), 403
    except Exception as e:
        return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple("0.0.0.0", 59888, application, use_debugger=True, use_reloader=True)
