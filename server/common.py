from flask import Flask, send_file, request, jsonify, abort, Blueprint
from flask_cors import CORS  # 追加
from flask_restx import Resource, Api
import os
import uuid
import mimetypes
import pytz
import json
from PIL import Image
import cv2
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
from sqlalchemy import or_
from pdf2image import convert_from_bytes
from io import BytesIO
from models import db
from models.user import User
from models.device import Device
from models.content import Content
from models.product import Product
from models.update_device import UpdateDevice
from models.device_content import DeviceContent
from models.onetimetoken import OneTimeToken
from models.tokens import Token
from models.device_setting import DeviceSetting
from models.device_group import DeviceGroup