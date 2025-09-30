from .common import *
from .functions_times import get_now_str

bp = Blueprint("signup", __name__)


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
@bp.route('', methods=['POST'])
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

            with bp.app_context():
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