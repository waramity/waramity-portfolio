from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, json, session)

from flask_babel import _, refresh
from flask_login import login_user, logout_user, login_required, current_user

import requests
import uuid
from app import db, app, google_client, user_db, feature_db
import datetime
from app.features.ai_hub.models import User
import re

import os
import time

from .forms import DestoryPromptCollectionForm
from werkzeug.datastructures import CombinedMultiDict

from urllib.parse import urlparse
import shutil

from .utils import is_valid_permission, is_valid_profile_name, is_valid_description, is_duplicate_profile_name, is_valid_base64_image, is_valid_topic, is_valid_model_name, is_valid_prompts, is_valid_prompts_comment, is_valid_comment, upload_base64_to_file_system, initial_upload_image

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

@ai_hub.route('/ai_hub')
def index():

    if session['platform'] != 'ai_hub':
        logout_user()
    if current_user.is_authenticated:
        if current_user.get_profile_name() is None:
            return redirect(url_for('ai_hub.create_profile'))
    prompts = feature_db.prompt_collection.find()
    return render_template('ai_hub/index.html', title=_('waramity portfolio'), prompts=prompts)

@ai_hub.route('/get-prompts/<int:page_index>', methods=["GET"])
def get_prompts(page_index):
    prompts = list(feature_db.prompt_collection.find().sort('created_date', -1).skip(page_index).limit(page_index * 9))
    prompt_payload = []
    for prompt in prompts:
        user = user_db.profile.find_one({'_id': prompt['user_id']})
        if user:
            if current_user.is_authenticated:
                like = feature_db.engagement.find_one({'item_id': prompt['_id'], 'user_id': current_user.get_id(), 'engage_type': 'like', 'item_type': 'prompt_collection'})
                bookmark = feature_db.engagement.find_one({'item_id': prompt['_id'], 'user_id': current_user.get_id(), 'engage_type': 'bookmark', 'item_type': 'prompt_collection'})
                prompt.pop("_id")
                combined_object = {
                    'prompt': prompt,
                    'user': user,
                    'like': False,
                    'bookmark': False
                }
                if like:
                    combined_object['like'] = True
                if bookmark:
                    combined_object['bookmark'] = True
            else:
                prompt.pop("_id")
                combined_object = {
                    'prompt': prompt,
                    'user': user
                }
        prompt_payload.append(combined_object)

    return make_response(jsonify({"status": 0, 'payload': prompt_payload}), 200)


@ai_hub.route('/logout')
@login_required
def logout():
    logout_user()
    session['platform'] = 'none'
    return redirect(url_for('ai_hub.index'))

def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()

@ai_hub.route("/google-auth")
def google_auth():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

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

        result = user_db.profile.insert_one(user)
        user['_id'] = str(result.inserted_id)
    else:
        user['_id'] = str(user['_id'])

    user = User(user)
    login_user(user)
    session['platform'] = 'ai_hub'
    return redirect(url_for('ai_hub.index'))

@ai_hub.route("/create-profile", methods=['GET'])
@login_required
def create_profile():
    if request.method == 'GET' and current_user.get_profile_name() is None:
        return render_template('ai_hub/create-profile.html', title=_('Create profile'))
    return redirect(url_for('ai_hub.index'))


@ai_hub.route("/submit-create-profile", methods=['PATCH'])
@login_required
def submit_create_profile():
    if request.method == 'PATCH' and request.json is not None:
        try:
            is_valid_profile_name(request.json['profile']['name'])
            is_valid_description(request.json['profile']['description'])
            is_duplicate_profile_name(request.json['profile']['name'])
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
        return render_template('ai_hub/edit_prompt.html', title=_('The deep pub'), slug=prompt_collection['slug'], profile_name=prompt_collection_creator['profile_name'])
    return make_response(jsonify({"status": 0, 'error_message': 'error_code in edit of prompt_collection'}), 200)

@ai_hub.route('/get-prompt-collection/<profile_name>/<slug>/edit', methods=['GET'])
@login_required
def get_prompt_collection_edit(profile_name, slug):
    if request.method == 'GET':
        try:
            prompt_collection, prompt_collection_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        keys_to_remove = ["_id", "user_id", "comments"]
        for key in keys_to_remove:
            prompt_collection.pop(key, None)

        return make_response(jsonify({"status": 1, 'prompt_collection': prompt_collection}), 200)
    return make_response(jsonify({"status": 0, "error_message": "error_code in get_prompt_collection_edit of prompt_collection"}), 200)

@ai_hub.route('/submit-edit-prompt/<slug>', methods=['PATCH'])
@login_required
def submit_edit_prompt(slug):
    if request.method == 'PATCH' and request.json is not None:

        try:
            is_valid_topic(request.json['topic'])
            is_valid_description(request.json['description'])
            is_valid_model_name(request.json['model_name'])
            is_valid_prompts(request.json['prompts'])

            prompt_collection, prompt_collection_creator = is_valid_permission(current_user.get_profile_name(), slug)

        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        new_prompts = request.json['prompts']
        original_prompts = prompt_collection["prompts"]

        original_prompt_urls = [prompt['image_url'] for prompt in prompt_collection["prompts"]]

        prompts = []

        for prompt in new_prompts[:]:
            prompt_image_path = urlparse(prompt['image_url']).path
            prompt_image_path = prompt_image_path.replace("/", "\\")
            if prompt_image_path in original_prompt_urls:
                prompt["image_url"] = prompt_image_path
                prompts.append(prompt)
                for tmp_prompt in original_prompts:
                    if tmp_prompt["image_url"] == prompt_image_path:
                        original_prompts.remove(tmp_prompt)
                        break
            elif 'static\\assets\\images\\ai_hub\\' not in prompt_image_path and is_valid_base64_image(prompt['image_url']):
                prompt['image_url'] = upload_base64_to_file_system(current_user.get_profile_name(), 'prompt_collections\\' + current_user.get_profile_name() + '_' + slug, prompt['image_url'])
                prompts.append(prompt)

        if len(prompts) == 0:
            return make_response(jsonify({'status': 0, 'error_message': 'กรุณาอัพโหลดรูปภาพ'}), 200)

        for prompt in original_prompts:
            os.remove(os.getcwd() + '\\app' + prompt["image_url"])

        prompt_collection_json = {
            '$set': {
                'topic': request.json['topic'],
                'description': request.json['description'],
                'model_name': request.json['model_name'],
                'updated_date': datetime.datetime.now(),
                'prompts': prompts
            }
        }

        feature_db.prompt_collection.update_one({'_id': prompt_collection['_id'], 'user_id': prompt_collection_creator['_id']},  prompt_collection_json)
        return make_response(jsonify({"status": 1, "redirect_url": '/en/ai_hub/prompt-collection/' + slug}), 200)


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

            if comments and len(comments) > 0:
                comment_folder_name = comments[0]['prompts'][0]['image_url'].split("\\")[6]
                shutil.rmtree(os.getcwd() + '\\app\\static\\assets\\images\\ai_hub\\comments\\' + comment_folder_name)

            deleted_comment = feature_db.comment.delete_many({ 'item.id': prompt_collection['_id'], 'item.type': 'prompt_collection'})

            user_db.profile.find_one_and_update({'_id': prompt_collection['user_id']}, {'$inc': {'total_engagement.likes': -like_result.deleted_count, 'total_engagement.bookmarks': -bookmark_result.deleted_count, 'total_engagement.comments': -deleted_comment.deleted_count}}, return_document=False)

            prompt_folder_name = prompt_collection['prompts'][0]['image_url'].split("\\")[6]
            shutil.rmtree(os.getcwd() + '\\app\\static\\assets\\images\\ai_hub\\prompt_collections\\' + prompt_folder_name)
            feature_db.prompt_collection.delete_one({'_id': prompt_collection['_id']})
            return redirect(url_for('ai_hub.index'))
        else:
            flash(_('Please enter a correct slug.'))
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
            return render_template('ai_hub/profile.html', title=_('My profile'), user=user, profile_name=profile_name, followed=followed)
        else:
            return redirect(url_for('ai_hub.index'))

@ai_hub.route("/bookmark", methods=['GET'])
@login_required
def bookmark():
    if request.method == 'GET':
        return render_template('ai_hub/bookmark.html', title=_('My bookmark'))

@ai_hub.route("/edit-profile/<profile_name>", methods=['GET'])
@login_required
def edit_profile(profile_name):
    if request.method == 'GET':
        if current_user.get_profile_name() == profile_name:
            user = user_db.profile.find_one({'profile_name': current_user.get_profile_name()}, {'profile_name': 1, 'description': 1, 'image_url': 1})
            return render_template('ai_hub/edit-profile.html', title=_('Edit profile'), user=user)

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

@ai_hub.route('/comment/<item_type>/<item_slug>', methods=['POST', 'GET'])
@login_required
def create_comment(item_type, item_slug):

    if request.method == 'POST' and request.json is not None:

        prompts = request.json['prompts']
        comment = request.json['comment']

        try:
            print(request.json['comment'])
            is_valid_comment(request.json['comment'])
            is_valid_prompts_comment(request.json['prompts'])

            for prompt in prompts:
                is_valid_base64_image(prompt['image_url'])

        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        comment_slug = uuid.uuid4().hex[:11]
        while feature_db.comment.find_one({'slug': comment_slug}):
            comment_slug = uuid.uuid4().hex[:11]

        if item_type == "prompt_collection":
            item_collection = feature_db.prompt_collection
            spaces_path = 'comments/' + 'collection_' + current_user.get_profile_name() + '_' + comment_slug
            redirect_url = '/en/ai_hub/prompt-collection/'

        for prompt in prompts:
            prompt['image_url'] = upload_base64_to_file_system(current_user.get_profile_name(), spaces_path, prompt['image_url'])

        item = item_collection.find_one({'slug': item_slug})

        new_comment = {
            'item': {
                'id': item['_id'],
                'type': item_type
            },
            'user_id': current_user.get_id(),
            'slug': comment_slug,
            'comment': comment,
            'created_date': datetime.datetime.now(),
            'updated_date': datetime.datetime.now(),
            'total_engagement': {
                'likes': 0
            },
            'prompts': prompts,
        }

        user_db.profile.update_one(
            {'_id': item['user_id']},
            {'$inc': {'total_engagement.comments': 1}}
        )

        feature_db.comment.insert_one(new_comment)

        return make_response(jsonify({"status": 1, "redirect_url": redirect_url + item_slug}), 200)


    elif request.method == 'GET':
        return render_template('ai_hub/create_comment.html', title=_('The deep pub'), item_type=item_type, item_slug=item_slug)

    return make_response(jsonify({"status": 0, 'message': 'error in post comment.'}), 200)

@ai_hub.route('/comment/<item_type>/<item_slug>/<comment_slug>/like', methods=['POST'])
@login_required
def like_comment(item_type, item_slug, comment_slug):
    if request.method == 'POST':
        if item_type == "prompt_collection":
            item_collection = feature_db.prompt_collection

        item = item_collection.find_one({'slug': item_slug})

        comment = feature_db.comment.find_one({'item.id': item['_id'], 'slug': comment_slug})
        like = feature_db.engagement.find_one({'user_id': current_user.get_id(), 'item_id': comment['_id'], 'item_type': 'comment', 'engage_type': 'like', 'parent_id': item['_id']})

        if like:
            feature_db.engagement.delete_one({'_id': like['_id']})
            feature_db.comment.update_one({'_id': comment['_id']}, {"$inc": {"total_engagement.likes": -1}} )
            user_db.profile.find_one_and_update({'_id': comment['user_id']}, {'$inc': {'total_engagement.likes': -1}}, return_document=False)
            return make_response(jsonify({"status": 1}), 200)

        like = {'user_id': current_user.get_id(), 'item_id': comment['_id'], 'item_type': 'comment', 'engage_type': 'like', 'created_at': datetime.datetime.now(), 'parent_id': item['_id']}
        feature_db.engagement.insert_one(like)

        feature_db.comment.update_one({'_id': comment['_id']}, {"$inc": {"total_engagement.likes": 1}} )
        user_db.profile.find_one_and_update({'_id': comment['user_id']}, {'$inc': {'total_engagement.likes': 1}}, return_document=False)

        return make_response(jsonify({"status": 1}), 200)

@ai_hub.route('/delete-comment/<comment_slug>', methods=['POST'])
@login_required
def delete_comment(comment_slug):
    if request.method == 'POST':
        comment = feature_db.comment.find_one({'slug': comment_slug})

        if comment['user_id'] == current_user.get_id():

            like_result = feature_db.engagement.delete_many({ 'item_id': comment['_id'], 'item_type': 'comment', 'engage_type': 'like'})
            user_db.profile.find_one_and_update({'_id': comment['user_id']}, {'$inc': {'total_engagement.likes': -like_result.deleted_count}}, return_document=False)

            comment_folder_name = comment['prompts'][0]['image_url'].split("\\")[6]
            shutil.rmtree(os.getcwd() + '\\app\\static\\assets\\images\\ai_hub\\comments\\' + comment_folder_name)


            feature_db.comment.delete_one({'_id': comment['_id']})

            return make_response(jsonify({'status': 1}), 200)

@ai_hub.route('/follow', methods=['POST'])
@login_required
def follow():
    if request.method == 'POST' and request.json is not None:
        follower_id = current_user.get_id()

        user = user_db.profile.find_one({'profile_name': request.json['following_profile_name']})

        following_id = user['_id']

        if follower_id == following_id:
            return make_response(jsonify({"status": 0, 'error_message': 'Cannot follow yourself.'}), 200)

        follow = user_db.follow.find_one({'follower_id': follower_id, 'following_id': following_id})

        if follow:
            user_db.follow.delete_one({'_id': follow['_id']})
            user_db.profile.find_one_and_update({'_id': user['_id']}, {'$inc': {'total_engagement.followers': -1}}, return_document=False)
            user_db.profile.find_one_and_update({'_id': current_user.get_id()}, {'$inc': {'total_engagement.followings': -1}}, return_document=False)
            return make_response(jsonify({"status": 1, 'message': 'Unfollowed user.'}), 200)

        user_db.follow.insert_one({'follower_id': follower_id, 'following_id': following_id})

        user_db.profile.find_one_and_update({'_id': user['_id']}, {'$inc': {'total_engagement.followers': 1}}, return_document=False)
        user_db.profile.find_one_and_update({'_id': current_user.get_id()}, {'$inc': {'total_engagement.followings': 1}}, return_document=False)
        return make_response(jsonify({"status": 1, 'message': 'Followed user.'}), 200)
