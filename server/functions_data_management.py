from .common import *
from .functions_times import get_now_str
from .static import ALLOWED_EXTENSIONS, ALLOWED_EXTENSIONS_IMG, ALLOWED_EXTENSIONS_MOV, CONTENTS_PATH, THUMBNAIL_PATH


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def change_filename(file, newfilename):
    _, ext = os.path.splitext(file.filename)
    return secure_filename(f"{newfilename}{ext}")

def check_content_type(file):
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower().lstrip('.')
    ext = ext.lower()
    if ext == "pdf":
        return "TYPYISPDF"
    if ext in ALLOWED_EXTENSIONS_IMG:
        print(ext)
        return 'image'
    if ext in ALLOWED_EXTENSIONS_MOV:
        return 'video'
    # if ext in ALLOWED_EXTENSIONS_PPT:
    #     return 'powerpoint'
    return 'NOTALLOWEDTYPE'

def check_content_type_forPath(filepath):
    _, ext = os.path.splitext(filepath)
    ext = ext.lower().lstrip('.')
    ext = ext.lower()
    if ext in ALLOWED_EXTENSIONS_IMG:
        return 'image'
    if ext in ALLOWED_EXTENSIONS_MOV:
        return 'video'
    # if ext in ALLOWED_EXTENSIONS_PPT:
    #     return 'powerpoint'
    return 'NOTALLOWEDTYPE'

def check_content_type_forPath_ext(filepath):
    _, ext = os.path.splitext(filepath)
    ext = ext.lower().lstrip('.')
    ext = ext.lower()
    if ext in ALLOWED_EXTENSIONS_IMG:
        return ext
    if ext in ALLOWED_EXTENSIONS_MOV:
        return ext
    # if ext in ALLOWED_EXTENSIONS_PPT:
    #     return 'powerpoint'
    return 'NOTALLOWEDTYPE'

# def get_content_path(content_id):
#     content_dir = './datas/contents/'
#     # ファイルパスを探索（拡張子は任意）
#     possible_files = [f for f in os.listdir(content_dir) if f.startswith(content_id + ".")]
#     if not possible_files:
#         return None
    
#     file_path = os.path.join(content_dir, possible_files[0])
#     return file_path

def get_content_path(content_id):
    # content_dir = './datas/contents/'
    content_dir = CONTENTS_PATH
    # ファイルパスを探索（拡張子は任意）
    possible_files = [f for f in os.listdir(content_dir) if f.startswith(content_id + ".")]
    if not possible_files:
        return None
    
    file_path = os.path.join(content_dir, possible_files[0])
    return file_path


def create_square_thumbnail(input_path, output_path,size: int = 300, video_frame_sec: float = 1.0):
    """
    画像 or 動画ファイルから中央正方形サムネイルを作成する。

    Parameters
    ----------
    input_path : str
        入力ファイルパス（画像 or 動画）
    output_path : str
        出力するサムネイル画像ファイルパス
    size : int
        出力サムネイルの一辺のピクセル数
    video_frame_sec : float
        動画の場合に切り出す秒位置
    """

    # 判定用の拡張子セット
    img_exts = {'.png', '.jpg', '.jpeg'}
    vid_exts = {'.mp4', '.mov'}

    ext = os.path.splitext(input_path)[1].lower()

    if ext in img_exts:
        # ----- 画像 -----
        with Image.open(input_path) as img:
            w, h = img.size
            min_side = min(w, h)
            left   = (w - min_side) // 2
            top    = (h - min_side) // 2
            right  = left + min_side
            bottom = top + min_side
            img_cropped = img.crop((left, top, right, bottom))
            img_cropped = img_cropped.resize((size, size), Image.LANCZOS)
            img_cropped.save(output_path)

    elif ext in vid_exts:
        # ----- 動画 -----
        cap = cv2.VideoCapture(input_path)
        cap.set(cv2.CAP_PROP_POS_MSEC, video_frame_sec * 1000)
        success, frame = cap.read()
        cap.release()
        if not success:
            raise RuntimeError("動画フレームを取得できませんでした。")

        h, w, _ = frame.shape
        min_side = min(w, h)
        left   = (w - min_side) // 2
        top    = (h - min_side) // 2
        square = frame[top:top+min_side, left:left+min_side]
        square = cv2.resize(square, (size, size))
        cv2.imwrite(output_path, square)

    else:
        raise ValueError(f"対応していない拡張子です: {ext}")
