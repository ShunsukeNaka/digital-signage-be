from .common import *
from .functions_times import get_now_str, get_jst_time
from .functions_token import check_token, add_token
from .functions_check_update import check_update_device, update_device_false

bp = Blueprint("check_update", __name__)

@bp.route('/', methods=['POST'])
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

            existing = DeviceHealth.query.filter_by(device_id=device_id).first()
            now = get_jst_time()
            if existing:
                existing.latest_connectedAt = now
                existing.status = "online"
                existing.updated_at = now
            else:
                new_health = DeviceHealth(
                    device_id=device_id,
                    latest_connectedAt=now,
                    status="online",
                    updated_at=now
                )
                db.session.add(new_health)
            db.session.commit()

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
        print(e)
        return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500
    
@bp.route('/return', methods=['POST'])
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
