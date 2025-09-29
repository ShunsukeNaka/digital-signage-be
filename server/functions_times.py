from .common import *

def get_jst_time():
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst)

def get_now_str():
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

def UtcGmt2JST(time: str):
    jst = pytz.timezone('Asia/Tokyo')

    if isinstance(time, str):
        # 文字列を datetime に変換（UTC と仮定）
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        time = time.replace(tzinfo=pytz.utc)
        
    if time.tzinfo is None:
        # naive datetime は UTC と仮定
        time = time.replace(tzinfo=pytz.utc)
    return time.astimezone(jst).strftime("%Y-%m-%d %H:%M:%S")
