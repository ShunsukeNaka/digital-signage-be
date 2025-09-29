from .common import *
from .functions_times import get_now_str

def update_device_true(user_id, device_id, UPDATE_INDEX):
    try:
        check_device = UpdateDevice.query.filter_by(user_id=user_id, device_id=device_id).first()
        user = User.query.filter_by(id=user_id).first()
        device = Device.query.filter_by(id=device_id).first()

        if user is None or device is None:
            return False

        if check_device is None:
            update_index = list("00000000")
            update_index[UPDATE_INDEX] = "1"
            update_index = "".join(update_index)

            updatedevice = UpdateDevice(
                user_id=user_id,
                device_id=device_id,
                update=True,
                update_index=update_index
            )
            db.session.add(updatedevice)
            db.session.commit()
            db.session.refresh(updatedevice)
        else:
            update_index = list(check_device.update_index)
            update_index[UPDATE_INDEX] = "1"
            check_device.update_index = "".join(update_index)
            check_device.update = True
            db.session.commit()
        return True
    except Exception as e:
        print(f"update_device_true error: {e}")
        return False


# def update_device_true(user_id, device_id, UPDATE_INDEX):
#     try:
#         check_device = UpdateDevice.query.filter_by(user_id=user_id, device_id=device_id).first()
#         user = User.query.filter_by(id=user_id).first()
#         device = Device.query.filter_by(id=device_id).first()

        

#         if check_device is None:
#             if user is not None and device is not None:
#                 with flask_app.app_context():
#                     update_index = "00000000"
#                     update_index[UPDATE_INDEX] = "1"

#                     updatedevice = UpdateDevice(user_id=user_id, device_id=device_id, update=True, update_index=update_index)
#                     db.session.add(updatedevice)
#                     db.session.commit()
#                     db.session.refresh(updatedevice)
#         else:
#             if user is not None and device is not None:
#                 with flask_app.app_context():
#                     check_device.update = True
#                     update_index = check_device.update_index
#                     update_index[UPDATE_INDEX] = "1"

#                     check_device.update_index = update_index
#                     db.session.commit()
#         return True
#     except Exception as e:
#         return jsonify({
#             "status": "error", "responded_at": get_now_str(),
#             "message": f'message: {e}'
#         }), 500

def update_device_false(user_id, device_id) -> bool:
    try:
        check_device = UpdateDevice.query.filter_by(user_id=user_id, device_id=device_id).first()
        user = User.query.filter_by(id=user_id).first()
        device = Device.query.filter_by(id=device_id).first()

        if check_device is None:
            print("IS NONE")
            return False
        else:
            if user is not None and device is not None:
                print("ELSE")
                # with flask_app.app_context():
                check_device.update = False
                check_device.update_index = "00000000"
                db.session.commit()
                db.session.refresh(check_device)
                return True   # ← 成功を表すブール値に統一
            else:
                return False
    except Exception as e:
        print(f"update_device_false error: {e}")
        return False
    
def check_update_device(user_id, device_id):
    try:
        check_device = UpdateDevice.query.filter_by(user_id=user_id, device_id=device_id).first()
        user = User.query.filter_by(id=user_id).first()
        device = Device.query.filter_by(id=device_id).first()
        if check_device is None:
            if user is not None and device is not None:
            # with flask_app.app_context():
                updatedevice = UpdateDevice(user_id=user_id, device_id=device_id, update=True, update_index="11111111")
                db.session.add(updatedevice)
                db.session.commit()
                db.session.refresh(updatedevice)
            return updatedevice
        else:
            if user is not None and device is not None:
                return check_device
    except Exception as e:
        return jsonify({
            "status": "error", "responded_at": get_now_str(),
            "message": f'message: {e}'
        }), 500