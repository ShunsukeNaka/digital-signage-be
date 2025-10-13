import os
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

CONTENTS_PATH = os.getenv("CONTENTS_PATH")
THUMBNAIL_PATH = os.getenv("THUMBNAIL_PATH")

ALLOWED_EXTENSIONS_IMG = {'png', 'jpg', 'jpeg'}
ALLOWED_EXTENSIONS_MOV = {'mp4', 'mov'}
# ALLOWED_EXTENSIONS_PPT = {'ppt', 'pptx'}
ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS_IMG.union(ALLOWED_EXTENSIONS_MOV)

UPDATE_INDEX_CONTENT_SET=1
UPDATE_INDEX_DEVICENAME_CHANGE=2
UPDATE_INDEX_DEVICETOKEN_CHANGE=3