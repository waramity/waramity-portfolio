from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, json)

from flask_babel import _, refresh
from flask_login import login_user, logout_user, login_required, current_user

import requests
import uuid
from app import db, app, google_client, user_db, feature_db
import datetime
from app.features.ai_hub.models import User
import re
import base64

from PIL import Image
import io
import os
import time

from .forms import DestoryPromptCollectionForm
from werkzeug.datastructures import CombinedMultiDict



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

def upload_base64_to_file_system(profile_name, directory_path, base64_data):
    base64_data_without_prefix = base64_data.split(',', 1)[-1]
    binary_data = base64.b64decode(base64_data_without_prefix)

    unique_id = uuid.uuid4().hex

    directory_path = "app\\static\\assets\\images\\ai_hub\\" + directory_path

    os.makedirs(directory_path, exist_ok=True)

    # Define the path where you want to save the file on your local filesystem
    file_path = os.path.join(directory_path, f'{profile_name}-{unique_id}-{time.time()}.png')

    # Write the binary data to the local file
    with open(file_path, 'wb') as file:
        file.write(binary_data)

    file_path = file_path.split(os.path.sep)

    # Remove the 'app' part if it exists
    if file_path[0] == 'app':
        file_path.pop(0)

    file_path = "\\" + os.path.sep.join(file_path)
    file_path = file_path.replace("/", "\\")
    print(file_path)

    # Return the local file path (if needed)
    return file_path

def initial_upload_image(profile_name, image_url, directory_path, old_image_url=""):
    print(image_url)
    # return kuy
    if not image_url.startswith('\\static\\assets\\images\\ai_hub\\'):
        print('kuy')
        is_valid_base64_image(image_url)
        if old_image_url is not "":
            # utils.delete_image_in_spaces(old_image_url)
            os.remove(os.getcwd() + '\\app' + old_image_url)
        cdn_url = upload_base64_to_file_system(profile_name, directory_path, image_url)
    elif image_url == current_user.get_profile_image():
        print('sus')
        cdn_url = image_url
    else:
        raise Exception('คุณไม่มี Permission สำหรับรูปนี้')

    return cdn_url

def delete_image_in_spaces(image_url):
    object_key = image_url.replace("https://tdp-public.sgp1.cdn.digitaloceanspaces.com/", "")
    spaces_client.delete_object(Bucket='tdp-public', Key=object_key)

def delete_file_in_local_system(file_path):
    os.remove(file_path)

@ai_hub.route('/ai_hub')
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
                is_valid_base64_image(prompt['image_url'])

        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        slug = uuid.uuid4().hex[:11]
        while feature_db.prompt_collection.find_one({'slug': slug}):
            slug = uuid.uuid4().hex[:11]

        for prompt in prompts:
            image_url = upload_base64_to_file_system(current_user.get_profile_name(), 'prompt_collections/' + current_user.get_profile_name() + '_' + slug, prompt['image_url'])
            prompt['image_url'] = image_url

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
        return make_response(jsonify({"status": 1, "redirect_url": '/en/ai_hub/prompt-collection/' + slug}), 200)

@ai_hub.route('/prompt-collection/<slug>', methods=['GET'])
def prompt_collection(slug):
    if request.method == 'GET':
        prompt_collection = feature_db.prompt_collection.find_one({'slug': slug})
        creator = user_db.profile.find_one({'_id': prompt_collection['user_id']})

        liked = False
        bookmarked = False
        followed = False
        if current_user.is_authenticated:
            like = feature_db.engagement.find_one({'item_id': prompt_collection['_id'], 'user_id': current_user.get_id(), 'engage_type': 'like', 'item_type': 'prompt_collection'})
            liked = like is not None

            bookmark = feature_db.engagement.find_one({'item_id': prompt_collection['_id'], 'user_id': current_user.get_id(), 'engage_type': 'bookmark', 'item_type': 'prompt_collection'})
            bookmarked = bookmark is not None

            follow = user_db.follow.find_one({'follower_id': current_user.get_id(), 'following_id': prompt_collection['user_id']})
            followed = follow is not None


        prompt_collection = {
            "topic": prompt_collection["topic"],
            "slug": prompt_collection["slug"],
            "prompts": prompt_collection["prompts"],
            "created_date": prompt_collection["created_date"],
            "description": prompt_collection["description"],
            "likes": prompt_collection["likes"],
            "model_name": prompt_collection["model_name"],
        }

        creator = {
            "profile_name": creator["profile_name"],
            "registered_on": creator["registered_on"],
            "image_url": creator["image_url"],
        }

        return render_template('ai_hub/prompt_collection.html', title=_('The deep pub'), prompt_collection=prompt_collection, creator=creator, liked=liked, bookmarked=bookmarked, followed=followed)

@ai_hub.route('/edit-prompt-collection/<profile_name>/<slug>', methods=['GET'])
@login_required
def edit_prompt(profile_name, slug):
    if request.method == 'GET':
        try:
            prompt_collection, prompt_collection_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)
        return render_template('prompt_collection/edit.html', title=_('The deep pub'), slug=prompt_collection['slug'], profile_name=prompt_collection_creator['profile_name'])
    return make_response(jsonify({"status": 0, 'error_message': 'error_code in edit of prompt_collection'}), 200)

@ai_hub.route('/destroy-prompt/<profile_name>/<slug>', methods=['GET', 'POST'])
@login_required
def destroy_prompt(profile_name, slug):
    form = DestoryPromptCollectionForm(CombinedMultiDict((request.files, request.form)))

    if request.method == 'POST' and form.validate_on_submit():
        if slug == form.slug.data:
            try:
                prompt_collection, prompt_collection_creator = is_valid_permission(profile_name, form.slug.data)
            except Exception as e:
                return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

            bookmark_result = feature_db.engagement.delete_many({ 'item_id': prompt_collection['_id'], 'item_type': 'prompt_collection', 'engage_type': 'bookmark'})
            like_result = feature_db.engagement.delete_many({ 'item_id': prompt_collection['_id'], 'item_type': 'prompt_collection', 'engage_type': 'like'})
            comment_like_result = feature_db.engagement.delete_many({ 'parent_id': prompt_collection['_id'], 'item_type': 'comment', 'engage_type': 'like'})

            comments = list(feature_db.comment.find({ 'item.id': prompt_collection['_id'], 'item.type': 'prompt_collection'}))

            for comment in comments:
                for prompt in comment['prompts']:
                    utils.delete_image_in_spaces(prompt['image_url'])

            deleted_comment = feature_db.comment.delete_many({ 'item.id': prompt_collection['_id'], 'item.type': 'prompt_collection'})

            user_db.profile.find_one_and_update({'_id': prompt_collection['user_id']}, {'$inc': {'total_engagement.likes': -like_result.deleted_count, 'total_engagement.bookmarks': -bookmark_result.deleted_count, 'total_engagement.comments': -deleted_comment.deleted_count}}, return_document=False)

            for prompt in prompt_collection["prompts"]:
                os.remove(os.getcwd() + '\\app' + prompt['image_url'])
            feature_db.prompt_collection.delete_one({'_id': prompt_collection['_id']})
            return redirect(url_for('ai_hub.index'))
        else:
            flash(_('กรุณาใส่ slug ให้ถูกต้อง'))
            return redirect(url_for('prompt_collection.destroy', slug=slug, profile_name=profile_name))

    if request.method == 'GET':
        try:
            prompt_collection, prompt_collection_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)
        return render_template('ai_hub/destroy_prompt.html', title=_('The deep pub'), form=form, slug=prompt_collection['slug'], profile_name=prompt_collection_creator['profile_name'])
    return make_response(jsonify({"status": 0, 'error_message': 'error_code in destroy GET of prompt_collection'}), 200)

@ai_hub.route('/prompt-collection/<profile_name>/<slug>/like', methods=['POST'])
@login_required
def like(profile_name, slug):
    if request.method == 'POST':
        user = user_db.profile.find_one({'profile_name': profile_name})
        prompt_collection = feature_db.prompt_collection.find_one({'user_id': user['_id'], 'slug': slug})

        like = feature_db.engagement.find_one({'user_id': current_user.get_id(), 'item_id': prompt_collection['_id'], 'item_type': 'prompt_collection', 'engage_type': 'like'})

        if like:
            feature_db.engagement.delete_one({'_id': like['_id']})
            feature_db.prompt_collection.find_one_and_update({'_id': prompt_collection['_id']}, {'$inc': {'likes': -1}}, return_document=False)
            user_db.profile.find_one_and_update({'_id': prompt_collection['user_id']}, {'$inc': {'total_engagement.likes': -1}}, return_document=False)
            return make_response(jsonify({"status": 1}), 200)

        like = {'user_id': current_user.get_id(), 'item_id': prompt_collection['_id'], 'item_type': 'prompt_collection', 'engage_type': 'like', 'created_at': datetime.datetime.now()}
        feature_db.engagement.insert_one(like)
        feature_db.prompt_collection.find_one_and_update({'_id': prompt_collection['_id']}, {'$inc': {'likes': 1}}, return_document=False)
        user_db.profile.find_one_and_update({'_id': prompt_collection['user_id']}, {'$inc': {'total_engagement.likes': 1}}, return_document=False)

        return make_response(jsonify({"status": 1}), 200)

@ai_hub.route('/prompt-collection/<profile_name>/<slug>/bookmark', methods=['POST'])
@login_required
def bookmark_prompt(profile_name, slug):
    if request.method == 'POST':
        user = user_db.profile.find_one({'profile_name': profile_name})
        prompt_collection = feature_db.prompt_collection.find_one({'user_id': user['_id'], 'slug': slug})

        bookmark = feature_db.engagement.find_one({'user_id': current_user.get_id(), 'item_id': prompt_collection['_id'], 'item_type': 'prompt_collection', 'engage_type': 'bookmark'})

        if bookmark:
            feature_db.engagement.delete_one({'_id': bookmark['_id']})
            user_db.profile.find_one_and_update({'_id': prompt_collection['user_id']}, {'$inc': {'total_engagement.bookmarks': -1}}, return_document=False)
            return make_response(jsonify({"status": 1}), 200)

        bookmark = {'user_id': current_user.get_id(), 'item_id': prompt_collection['_id'], 'item_type': 'prompt_collection', 'engage_type': 'bookmark', 'created_at': datetime.datetime.now()}
        feature_db.engagement.insert_one(bookmark)
        user_db.profile.find_one_and_update({'_id': prompt_collection['user_id']}, {'$inc': {'total_engagement.bookmarks': 1}}, return_document=False)

        return make_response(jsonify({"status": 1}), 200)

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
            return render_template('ai_hub/profile.html', title=_('โปรไฟล์ของฉัน - The deep pub'), user=user, profile_name=profile_name, followed=followed)
        else:
            return redirect(url_for('ai_hub.index'))

@ai_hub.route("/bookmark", methods=['GET'])
@login_required
def bookmark():
    if request.method == 'GET':
        return render_template('ai_hub/bookmark.html', title=_('บุ๊คมาร์คของฉัน - The deep pub'))

@ai_hub.route("/edit-profile/<profile_name>", methods=['GET'])
@login_required
def edit_profile(profile_name):
    if request.method == 'GET':
        if current_user.get_profile_name() == profile_name:
            user = user_db.profile.find_one({'profile_name': current_user.get_profile_name()}, {'profile_name': 1, 'description': 1, 'image_url': 1})
            return render_template('ai_hub/edit-profile.html', title=_('แก้ไขโปรไฟล์ - The deep pub'), user=user)

@ai_hub.route("/submit-edit-profile", methods=['PATCH'])
@login_required
def submit_edit_profile():
    if request.method == 'PATCH' and request.json is not None:
        try:
            is_valid_description(request.json['profile']['description'])
            user = user_db.profile.find_one({'_id': current_user.get_id()})
            cdn_url = initial_upload_image(current_user.get_profile_name(), request.json['profile']['base64_image'], 'profiles\\' + current_user.get_profile_name() + '_' + current_user.get_slug(), user['image_url'])
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        profile = {
            "$set": {"image_url": cdn_url, 'description': request.json['profile']['description']}
        }

        user_db.profile.update_one({"_id": current_user.get_id()}, profile)
        return make_response(jsonify({'status': 1, 'message': 'แก้ไขโปรไฟล์แล้ว'}), 200)

    return make_response(jsonify({'status': 0, 'error_message': 'error_code in create_profile of auth'}), 200)


@ai_hub.route("/get-prompt-collection-bookmarks", methods=['GET'])
@login_required
def get_prompt_collection_bookmarks():
    if request.method == 'GET':
        user = user_db.profile.find_one({'_id': current_user.get_id()})

        prompt_collection = feature_db.engagement.find_one({'user_id': user['_id'], 'item_type': 'prompt_collection', 'engage_type': 'bookmark'})

        if prompt_collection is None:
            return make_response(jsonify({'status': 1, 'message': 'ยังไม่เคยบุ๊คมาร์ค Prompt collection'}), 200)

        pipeline = [
            {
                "$match": {
                    "user_id": user['_id'],
                    "item_type": "prompt_collection",
                    "engage_type": "bookmark"
                }
            },
            {
                "$lookup": {
                    "from": "prompt_collection",
                    "localField": "item_id",
                    "foreignField": "_id",
                    "as": "prompt_collection"
                }
            },
            {
                "$unwind": "$prompt_collection"
            },
            {
                "$project": {
                    "_id": 0,
                    "image_url": { "$arrayElemAt": ["$prompt_collection.prompts.image_url", 0] },
                    "slug": "$prompt_collection.slug",
                    "multiple_images": { "$gt": [{ "$size": "$prompt_collection.prompts.image_url" }, 1] },
                }
            },
        ]

        prompt_collections = list(feature_db.engagement.aggregate(pipeline))

        return make_response(jsonify({'status': 1, 'prompt_collections': prompt_collections}), 200)
    return make_response(jsonify({"status": 0, 'error_message': 'error_code in get_prompt_collections of profile'}), 200)

@ai_hub.route("/get-prompt-collections-profile/<profile_name>", methods=['GET'])
def get_prompt_collections(profile_name):
    if request.method == 'GET':
        user = user_db.profile.find_one({'profile_name': profile_name})

        prompt_collection = feature_db.prompt_collection.find_one({'user_id': user['_id']})

        if prompt_collection is None:
            return make_response(jsonify({'status': 1, 'message': 'ยังไม่เคยสร้าง Prompt collection'}), 200)

        prompt_collections = list(feature_db.prompt_collection.find({'user_id': user['_id']}, {'_id': 0, "image_url": { "$arrayElemAt": ["$prompts.image_url", 0] }, 'slug': 1, "multiple_images": {
            "$gt": [{ "$size": { "$ifNull": [ "$prompts.image_url", [] ] } }, 1]}}))

        return make_response(jsonify({'status': 1, 'prompt_collections': prompt_collections}), 200)
    return make_response(jsonify({"status": 0, 'error_message': 'error_code in get_prompt_collections of profile'}), 200)

@ai_hub.route('/get-comments/<item_type>/<item_slug>', methods=['GET'])
def get_comments(item_type, item_slug):
    if request.method == 'GET':

        if item_type == "prompt_collection":
            item_collection = feature_db.prompt_collection.find_one({'slug': item_slug})
        elif item_type == "prompt_builder":
            item_collection = feature_db.prompt_builder.find_one({'slug': item_slug})

        match_comments = feature_db.comment.find({'item.id': item_collection['_id'], 'item.type': item_type})

        comments = []
        for comment in match_comments:
            user_id = comment['user_id']
            user_profile = user_db.profile.find_one({'_id': user_id}, {'_id': 0, 'profile_name': 1, 'image_url': 1, 'slug': 1})
            tmp_comment = {
                'user': {
                    'profile_name': user_profile['profile_name'],
                    'image_url': user_profile['image_url'],
                    'slug': user_profile['slug']
                },
                'slug': comment['slug'],
                'comment': comment['comment'],
                'created_date': comment['created_date'].isoformat(),
                'total_engagement': {
                    'likes': comment['total_engagement']['likes'],
                },
                'prompts': comment['prompts'],
                'current_user_liked': False,
            }

            if current_user.is_authenticated:
                comment_liked = feature_db.engagement.find_one({'user_id': current_user.get_id(), 'item_id': comment['_id'], 'item_type': 'comment', 'engage_type': 'like'})
                if comment_liked:
                    tmp_comment['current_user_liked'] = True

            comments.append(tmp_comment)

        if len(comments) != 0:
            return make_response(jsonify({'status': 1, 'comments': comments}), 200)
        else:
            return make_response(jsonify({'status': 1, 'message': 'ยังไม่มีคอมเมนท์'}), 200)
