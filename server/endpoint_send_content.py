from .common import *
from .functions_times import get_jst_time, get_now_str
from .functions_token import check_token
from .functions_data_management import get_content_path  

bp = Blueprint("send_content", __name__)


@bp.route('', methods=["GET"])
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
            print("content_id: ", content_id)
            print("filename: ", filename)
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


@bp.route('/device', methods=["GET"])
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
