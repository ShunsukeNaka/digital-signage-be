from .common import *
from .functions_times import get_now_str
from .functions_token import check_token, add_token
from .functions_check_update import check_update_device, update_device_false
from .static import TMP_PATH
import io
import tempfile


bp = Blueprint("rotate", __name__)

def rotate_img(file_name,file,direction):
    img = Image.open(file)
    if "right" in direction:
        rotate_image = img.rotate(-90,expand=True)
    elif "left" in direction:
        rotate_image = img.rotate(90,expand=True)
    else:
        print('えるす')
        raise ValueError("direction は 'left' か 'right' で指定してください")
    ext = os.path.splitext(file_name)[1]
    file_name = f"rotated_{file_name[:-4]}{ext}"
    print(file_name)
    # save_path = os.path.join(output_dir, file_name)

    # rotate_image.save(save_path)
    return rotate_image


def rotate_mp4(video_name,file,direction): 
    name, ext = os.path.splitext(video_name)
    # output_path = os.path.join("app", "static", "rotated_contents", f"{name}_rotated{ext}")

    with tempfile.NamedTemporaryFile(suffix=ext) as tmp:
        print("."+ext)
        file.save(tmp.name)
        cap = cv2.VideoCapture(tmp.name)

        if not cap.isOpened():
            print(f"動画を開けません: {tmp.name}")
            raise ValueError("動画を開けません")

        # # 動画読み込み
        # cap = cv2.VideoCapture(file)
        # if not cap.isOpened():
        #     print(f"動画を開けません: {file}")
        #     return

        # fps とサイズ取得
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # 回転後は入れ替える
        height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        # fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        # tmp_out = tempfile.NamedTemporaryFile(suffix="."+ext, delete=False)
        # out = cv2.VideoWriter(tmp_out.name, fourcc, fps, (width, height))

        rotated_frames = []

        # 回転処理
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if direction == "right":
                rotated_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif direction == "left":
                rotated_frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            else:
                print("direction は 'left' か 'right' で指定してください")
                cap.release()
                # out.release()
                raise ValueError("direction は 'left' か 'right' で指定してください")

            #out.write(rotated_frame)

            frame_rgb = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2RGB)
            rotated_frames.append(frame_rgb)

        cap.release()
        # out.release()

         # BytesIO に書き出す
        bytes_io = io.BytesIO()
        writer = imageio.get_writer(bytes_io, format='mp4', fps=fps)
        for f in rotated_frames:
            writer.append_data(f)
        writer.close()
        bytes_io.seek(0)
        return bytes_io

        # return tmp_out.name


        # print(f"{video_name} を {direction} に回転して保存しました: {output_path}")
        # return True

@bp.route('/', methods=['POST'])
def rotate():
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                return jsonify({"status": "error", "message": "ファイルがありません"}), 400
            direction = request.form.get("direction")
            if not direction:
              return jsonify({"status": "error", "message": "directionがありません"}), 400

            file = request.files['file']
           

            # filename = os.path.basename(image_path)
            filename = file.filename
            print(filename)
            # direction = filename.split("-")[-1].split(".")[0]
            print(direction)
            name, ext = os.path.splitext(filename)
            print(name)
            print(ext)
            img_ext = [".png",".jpg",".jpeg", ".pdf"]
            pic_ext = [".mp4",".mov"]
            if any(e in ext.lower() for e in img_ext):
                bytes_io = rotate_img(filename, file, direction)
                img_io = io.BytesIO()
                bytes_io.save(img_io, format="PNG")
                img_io.seek(0)
                return send_file(img_io, mimetype="image/png")
            elif any(e in ext.lower() for e in pic_ext):
                rotated_bytes = rotate_mp4(filename, file, direction)
                return send_file(rotated_bytes, mimetype="video/mp4", as_attachment=False, download_name="rotated.mp4")

                # return send_file(bytes_io, mimetype="video/mp4", as_attachment=False, download_name="rotated.mp4")

            
            # return jsonify({
            #     "status": "success", 
            #     "responded_at": get_now_str(), 
            #     "update_device":{
                    
            #     }
            # }), 200
            return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": 'message: This is Error.'
            }), 500
    except Exception as e:
        print(e)
        return jsonify({
                "status": "error", "responded_at": get_now_str(),
                "message": f'message: {e}'
            }), 500
    
