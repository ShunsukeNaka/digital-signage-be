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
from server import *   # Blueprintをインポート

# Flaskアプリ作成
flask_app = Flask(__name__)
flask_app.url_map.strict_slashes=False
flask_app.config.from_object('config')  # config.pyを読み込み
# flask_app.config['CONTENTS_DIR'] = '/datas/contents'
# flask_app.config['THUMBNAILS_DIR'] = './datas/thumbnails'
db.init_app(flask_app)
# CORS有効化
CORS(flask_app)

# WSGI互換用
application = flask_app


# Blueprintを登録
application.register_blueprint(user_bp, url_prefix="/users")
application.register_blueprint(signup_bp, url_prefix="/signup")
application.register_blueprint(login_bp, url_prefix="/login")
application.register_blueprint(content_bp, url_prefix="/content")
application.register_blueprint(contents_get_bp, url_prefix="/contents")
application.register_blueprint(device_bp, url_prefix="/device")
application.register_blueprint(health_bp, url_prefix="/health")
application.register_blueprint(send_content_bp, url_prefix="/send_content")
application.register_blueprint(send_thumbnail_bp, url_prefix="/send_thumbnail")
application.register_blueprint(check_update_bp, url_prefix="/check_update")
application.register_blueprint(rotate, url_prefix="/rotate")


@flask_app.route("/", methods=["GET"])
def hello_world():
    return jsonify({"message": "Hello World"}), 200

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple("0.0.0.0", 59989, application, use_debugger=True, use_reloader=True)
