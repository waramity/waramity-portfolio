import base64
from PIL import Image
import io
import uuid
import os
import time
from app import user_db, feature_db
import re
from flask_login import current_user

def is_valid_permission(profile_name, slug):
    prompt_collection = feature_db.prompt_collection.find_one({'slug': slug})
    prompt_collection_creator = user_db.profile.find_one({'_id': prompt_collection['user_id'], 'profile_name': profile_name}, {'profile_name': 1})
    if not prompt_collection_creator or prompt_collection_creator['_id'] != current_user.get_id() or profile_name != current_user.get_profile_name():
        raise Exception('permission_denied')
    return prompt_collection, prompt_collection_creator

def is_valid_profile_name(profile_name):
    if not isinstance(profile_name, str):
        raise Exception('ชื่อ Profile is not instance')

    if not profile_name[0].isalpha():
        raise Exception('ตัวอักษรแรกของชื่อ Profile ควรเป็นภาษาอังกฤษ')

    pattern = re.compile("[A-Za-z0-9]+")

    if pattern.fullmatch(profile_name) is None:
        raise Exception('ชื่อ Profile ควรมีแค่ภาษาอังกฤษ, และตัวเลข')

    if len(profile_name) >= 2 and len(profile_name) <= 15:
        return True
    else:
        raise Exception('ชื่อ Profile ควรมีความยาวระหว่าง 2-15 ตัวอักษร')

def is_valid_description(description):
    if not isinstance(description, str):
        raise Exception('Description is not instance')

    if len(description) <= 188:
        return True
    else:
        raise Exception('Description ควรต่ำกว่า 188 ตัวอักษร')

def is_duplicate_profile_name(profile_name):
    if user_db.profile.find_one({'profile_name': profile_name}) and profile_name != current_user.get_profile_name():
        raise Exception('มีคนใช้งานชื่อ Profile นี้แล้ว')
    else:
        return True

def is_valid_base64_image(image_string):
    image_string = image_string.split(',', 1)[-1]

    if len(image_string) * 3 / 4 > 2 * 1024 * 1024:
        raise Exception('ขนาดของไฟล์ควรต่ำกว่า 2 MBs')

    print(image_string)

    if is_valid_image(image_string):
        image = base64.b64decode(image_string)
        img = Image.open(io.BytesIO(image))
        if img.width > 2048 or img.height > 2048:
            raise Exception('ขนาดของภาพควรต่ำกว่า 2048px')
        if img.format.lower() not in ["jpg", "jpeg", "png"]:
            raise Exception('กรุณาอัพโหลดไฟล์นามสกุล jpg, jpeg หรือ png เท่านั้น')
        return True
    return False

def is_valid_image(image_string):
    image = base64.b64decode(image_string)
    Image.open(io.BytesIO(image))
    return True

def is_valid_topic(topic):
    if len(topic) > 0 and len(topic) <= 32:
        return True
    elif len(topic) == 0:
        raise Exception('กรุณาใส่ Topic')
    else:
        raise Exception('Topic ควรต่ำกว่า 32 ตัวอักษร')

def is_valid_model_name(model_name):
    if len(model_name) <= 100:
        return True
    else:
        raise Exception('ชื่่อโมเดลควรต่ำกว่า 100 ตัวอักษร')

def is_valid_prompts(prompts):
    if len(prompts) == 0:
        raise Exception('กรุณาอัพโหลดภาพ')

    elif len(prompts) > 6:
        raise Exception('ควรอัพโหลดภาพต่ำกว่า 6 รูป')
    else:
        return True

def is_valid_prompts_comment(prompts):
    if len(prompts) > 6:
        raise Exception('ควรอัพโหลดภาพต่ำกว่า 6 รูป')
    else:
        return True

def is_valid_comment(comment):
    if comment == "":
        raise Exception('กรุณาเขียนคอมเมนต์')
    return True

def upload_base64_to_file_system(profile_name, directory_path, base64_data):
    base64_data_without_prefix = base64_data.split(',', 1)[-1]
    binary_data = base64.b64decode(base64_data_without_prefix)

    unique_id = uuid.uuid4().hex

    directory_path = "app\\static\\assets\\images\\ai_hub\\" + directory_path

    os.makedirs(directory_path, exist_ok=True)

    file_path = os.path.join(directory_path, f'{profile_name}-{unique_id}-{time.time()}.png')

    with open(file_path, 'wb') as file:
        file.write(binary_data)

    file_path = file_path.split(os.path.sep)

    if file_path[0] == 'app':
        file_path.pop(0)

    file_path = "\\" + os.path.sep.join(file_path)
    file_path = file_path.replace("/", "\\")

    return file_path

def initial_upload_image(profile_name, image_url, directory_path, old_image_url=""):
    if not image_url.startswith('\\static\\assets\\images\\ai_hub\\'):
        is_valid_base64_image(image_url)
        if old_image_url is not "":
            os.remove(os.getcwd() + '\\app' + old_image_url)
        cdn_url = upload_base64_to_file_system(profile_name, directory_path, image_url)
    elif image_url == current_user.get_profile_image():
        cdn_url = image_url
    else:
        raise Exception('คุณไม่มี Permission สำหรับรูปนี้')

    return cdn_url
