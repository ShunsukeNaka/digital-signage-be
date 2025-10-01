from .common import *
from .functions_times import get_now_str
from .functions_token import check_token
from .functions_data_management import get_content_path, check_content_type_forPath_ext
from .functions_check_update import update_device_true
from .static import UPDATE_INDEX_CONTENT_SET

bp = Blueprint("device", __name__)

@bp.route('/', methods=['POST', 'DELETE'])
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
            
            # with bp.app_context():
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
    
@bp.route('/get', methods=['POST'])
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
    

@bp.route('/content/set', methods=['POST'])
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
            
            # with bp.app_context():
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

@bp.route('/content/get', methods=['POST'])
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


@bp.route('/content/get/device', methods=['POST'])
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
