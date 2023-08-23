from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, json)

from flask_babel import _, refresh
from flask_login import login_user, logout_user, login_required, current_user

import requests
import uuid
from app import db, app, google_client, user_db
import datetime
from app.features.ai_hub.models import User
import re
import base64

from PIL import Image
import io
import os
import time


ai_hub = Blueprint('ai_hub', __name__, template_folder='templates', url_prefix='/<lang_code>/ai_hub' )

# Multiligual Start
@ai_hub.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)

@ai_hub.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')

@ai_hub.before_request
def before_request():
    if g.lang_code not in current_app.config['LANGUAGES']:
        abort(404)

# Multiligual End

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
    try:
        image = base64.b64decode(image_string)
        Image.open(io.BytesIO(image))
        return True
    except Exception:
        raise Exception('Format ของภาพไม่ถูกต้อง')

def upload_base64_to_file_system(profile_name, directory_path, base64_data):
    base64_data_without_prefix = base64_data.split(',', 1)[-1]
    binary_data = base64.b64decode(base64_data_without_prefix)

    unique_id = uuid.uuid4().hex
    os.makedirs(directory_path, exist_ok=True)


    # Define the path where you want to save the file on your local filesystem
    file_path = os.path.join(directory_path, f'{profile_name}-{unique_id}-{time.time()}.png')

    # Write the binary data to the local file
    with open(file_path, 'wb') as file:
        file.write(binary_data)

    # Return the local file path (if needed)
    return file_path

@ai_hub.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.get_profile_name() is None:
            return redirect(url_for('ai_hub.create_profile'))
    return render_template('ai_hub/index.html', title=_('waramity portfolio'))

@ai_hub.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('ai_hub.index'))

def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()

@ai_hub.route("/google-auth")
def google_auth():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = google_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email"],
    )

    return redirect(request_uri)

@ai_hub.route("/google-auth/callback")
def google_auth_callback():
    code = request.args.get("code")

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = google_client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET']),
    )

    google_client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = google_client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        social_auth_id = userinfo_response.json()["sub"]
    else:
        return "User email not available or not verified by Google.", 400

    user = user_db.profile.find_one({'social_auth.social_auth_id': social_auth_id})

    if not user:

        slug = uuid.uuid4().hex[:11]
        while user_db.profile.find_one({'slug': slug}):
            slug = uuid.uuid4().hex[:11]

        user_id = 'mongo_' + uuid.uuid4().hex[:11]
        while user_db.profile.find_one({'_id': user_id}):
            user_id = 'mongo_' + uuid.uuid4().hex[:11]

        user = {
            '_id': user_id,
            'registered_on': datetime.datetime.now(),
            'slug': slug,
            'social_auth': {
                'social_auth_id': social_auth_id,
                'social_provider': 'google'
            },
            'description': '',
            'image_url': '',
            'profile_name': '',
            'total_engagement': {
                'likes': 0,
                'bookmarks': 0,
                'comments': 0,
                'followers': 0,
                'followings': 0
            }
        }

        # Insert the new user document into the collection
        result = user_db.profile.insert_one(user)
        user['_id'] = str(result.inserted_id)
    else:
        user['_id'] = str(user['_id'])

    user = User(user)
    login_user(user)
    return redirect(url_for('ai_hub.index'))

@ai_hub.route("/create-profile", methods=['GET'])
@login_required
def create_profile():
    if request.method == 'GET' and current_user.get_profile_name() is None:
        return render_template('ai_hub/create-profile.html', title=_('สร้างโปรไฟล์ - The deep pub'))
    return redirect(url_for('ai_hub.index'))


@ai_hub.route("/submit-create-profile", methods=['PATCH'])
@login_required
def submit_create_profile():
    if request.method == 'PATCH' and request.json is not None:
        try:
            print(request.json['profile']['name'])
            is_valid_profile_name(request.json['profile']['name'])
            is_valid_description(request.json['profile']['description'])
            is_duplicate_profile_name(request.json['profile']['name'])
            print(request.json['profile']['base64_image'])
            is_valid_base64_image(request.json['profile']['base64_image'])
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        image_url = upload_base64_to_file_system(request.json['profile']['name'], 'profiles\\' + request.json['profile']['name'] + '_' + current_user.get_slug(), request.json['profile']['base64_image'])
        profile = {
            "$set": {"profile_name": request.json['profile']['name'], "image_url": image_url, 'description': request.json['profile']['description']}
        }

        user_db.profile.update_one({"_id": current_user.get_id()}, profile)
        return make_response(jsonify({'status': 1, 'message': 'สร้างโปรไฟล์แล้ว'}), 200)

    return make_response(jsonify({'status': 0, 'error_message': 'error_code in create_profile of auth'}), 200)

@ai_hub.route('/upload-prompt', methods=['GET', 'POST'])
@login_required
def upload_prompt():
    if request.method == 'GET':
        return render_template('ai_hub/upload.html', title=_('The deep pub'))
    if request.method == 'POST' and request.json is not None:
        try:
            is_valid_topic(request.json['topic'])
            is_valid_description(request.json['description'])
            is_valid_model_name(request.json['model_name'])
            is_valid_prompts(request.json['prompts'])

            prompts = request.json['prompts']

            for prompt in prompts:
                utils.is_valid_base64_image(prompt['image_url'])

        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        slug = uuid.uuid4().hex[:11]
        while feature_db.prompt_collection.find_one({'slug': slug}):
            slug = uuid.uuid4().hex[:11]

        for prompt in prompts:
            cdn_url = utils.upload_base64_to_spaces(current_user.get_profile_name(), 'prompt_collections/' + current_user.get_profile_name() + '_' + slug, prompt['image_url'])
            prompt['image_url'] = cdn_url

        prompt_collection_json = {
            'topic': request.json['topic'],
            'slug': slug,
            'user_id': current_user.get_id(),
            'description': request.json['description'],
            'model_name': request.json['model_name'],
            'created_date': datetime.datetime.now(),
            'updated_date': datetime.datetime.now(),
            'likes': 0,
            'prompts': prompts,
        }

        prompt_collection = feature_db.prompt_collection.insert_one(prompt_collection_json)
        return make_response(jsonify({"status": 1, "redirect_url": '/en/prompt-collection/' + slug}), 200)

@ai_hub.route("/profile/<profile_name>", methods=['GET'])
def profile(profile_name):
    if request.method == 'GET':
        user = user_db.profile.find_one({'profile_name': profile_name}, {'_id': 1, 'profile_name': 1, 'description': 1, 'image_url': 1, 'total_engagement': 1})
        if user is not None:
            followed = False
            if current_user.is_authenticated:
                follow = user_db.follow.find_one({'follower_id': current_user.get_id(), 'following_id': user['_id']})
                followed = follow is not None
            user.pop('_id', None)
            return render_template('profile/profile.html', title=_('โปรไฟล์ของฉัน - The deep pub'), user=user, profile_name=profile_name, followed=followed)
        else:
            return redirect(url_for('main.index'))

@ai_hub.route("/bookmark", methods=['GET'])
@login_required
def bookmark():
    if request.method == 'GET':
        return render_template('profile/bookmark.html', title=_('บุ๊คมาร์คของฉัน - The deep pub'))

@ai_hub.route("/edit-profile/<profile_name>", methods=['GET'])
@login_required
def edit_profile(profile_name):
    if request.method == 'GET':
        if current_user.get_profile_name() == profile_name:
            user = user_db.profile.find_one({'profile_name': current_user.get_profile_name()}, {'profile_name': 1, 'description': 1, 'image_url': 1})
            return render_template('profile/edit-profile.html', title=_('แก้ไขโปรไฟล์ - The deep pub'), user=user)
