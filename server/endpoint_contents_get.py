from .common import *
from .functions_times import get_now_str
from .functions_token import check_token

bp = Blueprint("contents", __name__)

@bp.route('/get', methods=['POST'])
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