from .common import *
from .functions_times import get_now_str
from .static import CONTENTS_PATH, THUMBNAIL_PATH


bp = Blueprint("send_thumbnail", __name__)


@bp.route('', methods=["GET"])
def send_thumbnail():
    if request.method == 'GET':
        try:
            if request.args.get('id') is None:
                return jsonify({"error": "it has no query"}), 400
            
            content_id = request.args.get('id')
            thumbnail_path = os.path.join(THUMBNAIL_PATH, f"{content_id}.png")
            file_path = thumbnail_path

            # ファイルの存在チェック
            if not os.path.exists(file_path):
                thumbnail_no_path = os.path.join(THUMBNAIL_PATH, "no_thumbnail.png")
                file_path = thumbnail_no_path
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
