from .common import *
from .functions_times import get_now_str
from .functions_data_management import check_content_type, change_filename, allowed_file, create_square_thumbnail, get_content_path, check_content_type_forPath
from .functions_token import check_token, generate_onetime_token_id

bp = Blueprint("content", __name__)


@bp.route('/', methods=['POST', 'DELETE'])
def content():
    try:
        if request.method == 'POST':

            if 'file' not in request.files:
                return jsonify({"status": "error", "message": "ファイルがありません"}), 400

            if not request.form or "file" not in request.files or "content_id" not in request.form or "content_name" not in request.form or "content_explanation" not in request.form:
                return jsonify({"error": "Invalid multipart form", "responded_at": get_now_str()}), 400

            get_token = request.form.get("token")

            check_token(get_token, "login")

            token = Token.query.filter_by(token=get_token, token_type="login").first()

            file = request.files['file']
            user_id = token.user_id
            # user_pass = request.form.get("user_pass")
            content_id = request.form.get("content_id")
            content_name = request.form.get("content_name")
            content_explanation = request.form.get("content_explanation")
            content_type = request.form.get("content_type")

            if file.filename == '':
                return jsonify({"status": "error", "message": "ファイル名が空です"}), 400
            
            if content_id == '':
                content_id = f'{user_id}-{uuid.uuid4()}'
            
            if content_name == '':
                content_name = content_id

            content_type = check_content_type(file)
            if content_type == 'NOTALLOWEDTYPE':
                return jsonify({"status": "error", "message": "許可されていないファイル形式です"}), 400
            

            # DataBaseからデータを取得して照合
            # user = User.query.filter_by(id=user_id).first()
            # if user is None:
            #     return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404
            # if not check_password_hash(user.password, user_pass):
            #     return jsonify({"status": "error", "responded_at": get_now_str(), "message": "パスワードが一致しません"}), 401
            
            content = Content.query.filter_by(id=content_id).first()
            if content is not None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "同じコンテンツIDが存在しています"}), 409
            
            if file and allowed_file(file.filename):
                filename = secure_filename(change_filename(file, content_id))
                save_path = os.path.join(bp.config['CONTENTS_DIR'], filename)
                thumbnail_path = os.path.join(bp.config['THUMBNAILS_DIR'], secure_filename(f"{content_id}.png"))
                file.save(save_path)

                print(save_path)
                print(thumbnail_path)

                create_square_thumbnail(input_path=save_path, output_path=thumbnail_path)
                # return jsonify({"status": "success", "filename": filename}), 200
            else:
                return jsonify({"status": "error", "message": "許可されていないファイル形式です"}), 400
            
            add_content = Content(
                id=content_id, 
                name=content_name, 
                type=content_type,
                explanation=content_explanation, 
                user_id=user_id
            )
            db.session.add(add_content)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "user": {
                    "id": user_id,
                },
                "content": {
                    "id": content_id,
                    "name": content_name,
                    "explanation": content_explanation,
                    "type": content_type,
                    "url": f"http://fukutech.kinulab.org/dsbe/send_content?id={content_id}"
                }
            }), 200
        if request.method == 'DELETE':

            data = request.get_json()
            if not data or "token" not in data or "content_id" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400

            token_value = data.get("token")
            result = check_token(token_value, "login")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result

            content_id = data.get("content_id")
            content = Content.query.filter_by(id=content_id, user_id=token.user_id).first()
            if not content:
                return jsonify({"status": "error", "message": "コンテンツが存在しません"}), 404

            # ファイル削除
            file_path = get_content_path(content_id)
            if not file_path:
                return jsonify({"status": "error", "message": "ファイルが存在しません"}), 404

            if os.path.exists(file_path):
                os.remove(file_path)

            db.session.delete(content)
            db.session.commit()

            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "deleted_content_id": content_id
            }), 200
    except Exception as e:
        db.session.rollback()

        if 'save_path' in locals() and os.path.exists(save_path):
            os.remove(save_path)

        return jsonify({
            "status": "error", "responded_at": get_now_str(),
            "message": f'message: {e}'
        }), 500
    

@bp.route('/get', methods=['GET','POST'])
def get_content():
    try:
        if request.method == 'POST':
        
            data = request.get_json()
            if "token" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            
            if not data or "content" not in data or "id" not in data["content"]:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400

            token_value = data.get("token")
            result = check_token(token_value, "login")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result

            user_id = token.user_id
            content_id = data["content"].get('id')

            # DataBaseからuserのデータを取得して照合
            user = User.query.filter_by(id=user_id).first()
            if user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404

            file_path = get_content_path(content_id) 
            # _, ext = os.path.splitext(file_path)
            token = generate_onetime_token_id()

            with bp.app_context():
                one_time_token = OneTimeToken(id=token, user_id=user_id, created_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc) + timedelta(hours=1))

                db.session.add(one_time_token)
                db.session.commit()


            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "user": {
                    "id": user_id,
                },
                "content": {
                    "id": content_id,
                    "type": check_content_type_forPath(file_path),
                    "url": f"http://fukutech.kinulab.org/dsbe/send_content?id={content_id}",
                    "token": token
                }
            })
    except Exception as e:
            return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500
    return jsonify({"status": "error", "responded_at": get_now_str()}), 405

@bp.route('/get/device', methods=['POST'])
def get_content_device():
    try:
        if request.method == 'POST':
        
            data = request.get_json()
            if "token" not in data:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400
            
            if not data or "content" not in data or "id" not in data["content"]:
                return jsonify({"error": "Invalid JSON", "responded_at": get_now_str()}), 400

            token_value = data.get("token")
            result = check_token(token_value, "device")
            if not isinstance(result, Token):
                return result  # エラー時はそのまま返す
            token = result

            user_id = token.user_id
            content_id = data["content"].get('id')

            # DataBaseからuserのデータを取得して照合
            user = User.query.filter_by(id=user_id).first()
            if user is None:
                return jsonify({"status": "error", "responded_at": get_now_str(), "message": "ユーザーが存在しません"}), 404

            file_path = get_content_path(content_id) 
            # _, ext = os.path.splitext(file_path)
            token = generate_onetime_token_id()

            with bp.app_context():
                one_time_token = OneTimeToken(id=token, user_id=user_id, created_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc) + timedelta(hours=1))

                db.session.add(one_time_token)
                db.session.commit()


            return jsonify({
                "status": "success",
                "responded_at": get_now_str(),
                "user": {
                    "id": user_id,
                },
                "content": {
                    "id": content_id,
                    "type": check_content_type_forPath(file_path),
                    "url": f"http://fukutech.kinulab.org/dsbe/send_content/device?id={content_id}",
                    "token": token
                }
            })
    except Exception as e:
            return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500
    return jsonify({"status": "error", "responded_at": get_now_str()}), 405

