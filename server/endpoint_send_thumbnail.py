from .common import *
from .functions_times import get_now_str

bp = Blueprint("send_thumbnail", __name__)


@bp.route('/', methods=["GET"])
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