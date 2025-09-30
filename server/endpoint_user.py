from .common import *
from .functions_times import get_now_str

bp = Blueprint("user", __name__)

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
@bp.route('', methods=['POST'])
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

            with bp.app_context():
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