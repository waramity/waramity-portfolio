from flask import Blueprint, render_template, redirect, url_for, request, flash, g, current_app, jsonify, make_response
from flask_babel import _
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, app, google_client, user_db, spaces_client, User, feature_db
from werkzeug.datastructures import CombinedMultiDict

import requests
import json
import uuid
import datetime, pytz
import time

import base64
from PIL import Image
import io

import re

from slugify import slugify

import app.utils as utils

profile = Blueprint('profile', __name__, template_folder='templates', url_prefix='/<lang_code>')

# Multiligual Start
@profile.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)

@profile.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')

@profile.before_request
def before_request():
    if g.lang_code not in current_app.config['LANGUAGES']:
        adapter = app.url_map.bind('')
        try:
            endpoint, args = adapter.match(
                '/en' + request.full_path.rstrip('/ ?'))
            return redirect(url_for(endpoint, **args), 301)
        except:
            abort(404)

    dfl = request.url_rule.defaults
    if 'lang_code' in dfl:
        if dfl['lang_code'] != request.full_path.split('/')[1]:
            abort(404)
# Multiligual End

# Function Start

def is_duplicate_profile_name(profile_name):
    if user_db.profile.find_one({'profile_name': profile_name}) and profile_name != current_user.get_profile_name():
        raise Exception('มีคนใช้งานชื่อ Profile นี้แล้ว')
    else:
        return True

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


def initial_upload_image(profile_name, image_url, directory_path, old_image_url=""):
    if not image_url.startswith('https://tdp-public.sgp1.cdn.digitaloceanspaces.com/'):
        utils.is_valid_base64_image(image_url)
        if old_image_url is not "":
            utils.delete_image_in_spaces(old_image_url)
        cdn_url = utils.upload_base64_to_spaces(profile_name, directory_path, image_url)
    elif image_url == current_user.get_profile_image():
        cdn_url = image_url
    else:
        raise Exception('คุณไม่มี Permission สำหรับรูปนี้')

    return cdn_url

# Function End

@profile.route("/profile/<profile_name>", methods=['GET'])
def main(profile_name):
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

@profile.route("/get-prompt-builders-profile/<profile_name>", methods=['GET'])
def get_prompt_builders(profile_name):
    if request.method == 'GET':
        user = user_db.profile.find_one({'profile_name': profile_name})

        prompt_builder = feature_db.prompt_builder.find_one({'user_id': user['_id'] })

        if prompt_builder is None:
            return make_response(jsonify({'status': 1, 'message': 'ยังไม่เคยสร้าง Prompt builder'}), 200)

        prompt_builders = list(feature_db.prompt_builder.find({'user_id': user['_id']}, {'_id': 0, 'name': 1, 'cover_image_url': 1, 'slug': 1, 'updated_date': 1}))

        return make_response(jsonify({'status': 1, 'prompt_builders': prompt_builders}), 200)

    return make_response(jsonify({"status": 0, 'error_message': 'error_code in get_prompt_builders of profile'}), 200)

@profile.route("/get-prompt-collections-profile/<profile_name>", methods=['GET'])
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

@profile.route("/bookmark", methods=['GET'])
@login_required
def bookmark():
    if request.method == 'GET':
        return render_template('profile/bookmark.html', title=_('บุ๊คมาร์คของฉัน - The deep pub'))


@profile.route("/get-prompt-collection-bookmarks", methods=['GET'])
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

@profile.route("/get-prompt-builder-bookmarks", methods=['GET'])
@login_required
def get_prompt_builder_bookmarks():
    if request.method == 'GET':
        user = user_db.profile.find_one({'_id': current_user.get_id()})

        prompt_builder = feature_db.engagement.find_one({'user_id': user['_id'], 'item_type': 'prompt_builder', 'engage_type': 'bookmark'})

        if prompt_builder is None:
            return make_response(jsonify({'status': 1, 'message': 'ยังไม่เคยบุ๊คมาร์ค Prompt builder'}), 200)

        pipeline = [
            {
                "$match": {
                    "user_id": user['_id'],
                    "item_type": "prompt_builder",
                    "engage_type": "bookmark"
                }
            },
            {
                "$lookup": {
                    "from": "prompt_builder",
                    "localField": "item_id",
                    "foreignField": "_id",
                    "as": "prompt_builder"
                }
            },
            {
                "$unwind": "$prompt_builder"
            },
            {
                "$project": {
                    "_id": 0,
                    "name": "$prompt_builder.name",
                    "image_url": "$prompt_builder.cover_image_url",
                    "slug": "$prompt_builder.slug",
                    "updated_date": "$prompt_builder.updated_date"
                }
            },
        ]

        prompt_builders = list(feature_db.engagement.aggregate(pipeline))

        return make_response(jsonify({'status': 1, 'prompt_builders': prompt_builders}), 200)
    return make_response(jsonify({"status": 0, 'error_message': 'error_code in get_prompt_collections of profile'}), 200)

@profile.route("/create-profile", methods=['GET'])
@login_required
def create_profile():
    if request.method == 'GET' and current_user.get_profile_name() is None:
        return render_template('profile/create-profile.html', title=_('สร้างโปรไฟล์ - The deep pub'))

    return redirect(url_for('main.index'))

@profile.route("/edit-profile/<profile_name>", methods=['GET'])
@login_required
def edit_profile(profile_name):
    if request.method == 'GET':
        if current_user.get_profile_name() == profile_name:
            user = user_db.profile.find_one({'profile_name': current_user.get_profile_name()}, {'profile_name': 1, 'description': 1, 'image_url': 1})
            return render_template('profile/edit-profile.html', title=_('แก้ไขโปรไฟล์ - The deep pub'), user=user)

@profile.route("/submit-create-profile", methods=['PATCH'])
@login_required
def submit_create_profile():
    if request.method == 'PATCH' and request.json is not None:
        try:
            is_valid_profile_name(request.json['profile']['name'])
            is_valid_description(request.json['profile']['description'])
            is_duplicate_profile_name(request.json['profile']['name'])
            utils.is_valid_base64_image(request.json['profile']['base64_image'])
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        cdn_url = utils.upload_base64_to_spaces(request.json['profile']['name'], 'profiles/' + request.json['profile']['name'] + '_' + current_user.get_slug(), request.json['profile']['base64_image'])
        profile = {
            "$set": {"profile_name": request.json['profile']['name'], "image_url": cdn_url, 'description': request.json['profile']['description']}
        }

        user_db.profile.update_one({"_id": current_user.get_id()}, profile)
        return make_response(jsonify({'status': 1, 'message': 'สร้างโปรไฟล์แล้ว'}), 200)

    return make_response(jsonify({'status': 0, 'error_message': 'error_code in create_profile of auth'}), 200)

@profile.route("/submit-edit-profile", methods=['PATCH'])
@login_required
def submit_edit_profile():
    if request.method == 'PATCH' and request.json is not None:
        try:
            is_valid_description(request.json['profile']['description'])
            user = user_db.profile.find_one({'_id': current_user.get_id()})
            cdn_url = initial_upload_image(current_user.get_profile_name(), request.json['profile']['base64_image'], 'profiles/' + current_user.get_profile_name() + '_' + current_user.get_slug(), user['image_url'])
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        profile = {
            "$set": {"image_url": cdn_url, 'description': request.json['profile']['description']}
        }

        user_db.profile.update_one({"_id": current_user.get_id()}, profile)
        return make_response(jsonify({'status': 1, 'message': 'แก้ไขโปรไฟล์แล้ว'}), 200)

    return make_response(jsonify({'status': 0, 'error_message': 'error_code in create_profile of auth'}), 200)

@profile.route('/follow', methods=['POST'])
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
