from .common import *
from .functions_times import get_now_str
from .functions_token import check_token
from .static import CONTENTS_PATH, THUMBNAIL_PATH

bp = Blueprint("health", __name__)


"""
POST /health/
{
    token: ユーザートークン
    device_id: [] or "ALL"
}
"""
@bp.route('/', methods=['POST'])
def content():
    try:
        data = request.get_json()

        if not data or "token" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
        if not data or "device_id" not in data:
            return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
        
        token_value = data.get("token")
        result = check_token(token_value, "login")
        if not isinstance(result, Token):
            return result  # エラー時はそのまま返す
        token = result

        device_id = data.get("device_id")
        if device_id is None:
            return jsonify({
                 "status": "error",
                 "responded_at": get_now_str(),
            }), 400
        
        device_health = []
        if device_id == "ALL":
            devices = (
                db.session.query(DeviceHealth)
                .join(Device, DeviceHealth.device_id == Device.id)
                .filter(Device.user_id == token.user_id)
                .all()
            )

            print(devices)
            print(token.user_id)
            if not devices:
                return jsonify({"status": "error","responded_at": get_now_str(), "message": "デバイスが存在しません"}), 404
            

        if type(device_id) == type([]):
            pass
            

        result = []
        for health in devices:
            result.append({
                "device_id": health.device_id,
                "latest_connectedAt": health.latest_connectedAt,
                "status": health.status,
                "updated_at": health.updated_at
            })

        return jsonify({
                "status": "success",
                "user": {
                    "id": token.user_id
                },
                "responded_at": get_now_str(),
                "device_health": result
            }), 200
    except Exception as e:
        return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500