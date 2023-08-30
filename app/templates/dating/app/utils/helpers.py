import base64
from PIL import Image
import uuid
import io
import time

from app import spaces_client

def is_valid_image(image_string):
    try:
        image = base64.b64decode(image_string)
        Image.open(io.BytesIO(image))
        return True
    except Exception:
        raise Exception('Format ของภาพไม่ถูกต้อง')

def is_valid_base64_image(image_string):
    image_string = image_string.split(',', 1)[-1]

    if len(image_string) * 3 / 4 > 2 * 1024 * 1024:
        raise Exception('ขนาดของไฟล์ควรต่ำกว่า 2 MBs')

    if is_valid_image(image_string):
        image = base64.b64decode(image_string)
        img = Image.open(io.BytesIO(image))
        if img.width > 2048 or img.height > 2048:
            raise Exception('ขนาดของภาพควรต่ำกว่า 2048px')
        if img.format.lower() not in ["jpg", "jpeg", "png"]:
            raise Exception('กรุณาอัพโหลดไฟล์นามสกุล jpg, jpeg หรือ png เท่านั้น')
        return True
    return False


def upload_base64_to_spaces(profile_name, directory_path, base64_data):

    base64_data_without_prefix = base64_data.split(',', 1)[-1]
    binary_data = base64.b64decode(base64_data_without_prefix)

    unique_id = uuid.uuid4().hex

    object_key = f'{directory_path}/{profile_name}-{unique_id}-{time.time()}.png'

    spaces_client.put_object(Bucket='tdp-public',
          ACL='public-read',
          Key=object_key,
          Body=binary_data,
          ContentType='image/png'
    )

    cdn_endpoint = 'https://tdp-public.sgp1.cdn.digitaloceanspaces.com'
    cdn_url = f'{cdn_endpoint}/{object_key}'

    return cdn_url

def check_image_url(prompt):
    if not prompt['image_url'].startswith('https://tdp-public.sgp1.cdn.digitaloceanspaces.com/'):
        return False
    else:
        return True

def delete_image_in_spaces(image_url):
    object_key = image_url.replace("https://tdp-public.sgp1.cdn.digitaloceanspaces.com/", "")
    spaces_client.delete_object(Bucket='tdp-public', Key=object_key)
