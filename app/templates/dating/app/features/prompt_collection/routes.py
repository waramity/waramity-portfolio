from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, flash)
from flask_babel import _, refresh
from flask_login import login_required, current_user

from app import db, app, redis, user_db, feature_db, spaces_client

from werkzeug.datastructures import CombinedMultiDict

import uuid
import datetime, pytz

from slugify import slugify
import base64
from PIL import Image
import io

import time

import json

import sys

from .views import DestoryPromptCollectionForm

import app.utils as utils

prompt_collection = Blueprint('prompt_collection', __name__, template_folder='templates', url_prefix='/<lang_code>' )

# Multiligual Start
@prompt_collection.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)

@prompt_collection.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')

@prompt_collection.before_request
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

def is_valid_permission(profile_name, slug):
    prompt_collection = feature_db.prompt_collection.find_one({'slug': slug})
    prompt_collection_creator = user_db.profile.find_one({'_id': prompt_collection['user_id'], 'profile_name': profile_name}, {'profile_name': 1})
    if not prompt_collection_creator or prompt_collection_creator['_id'] != current_user.get_id() or profile_name != current_user.get_profile_name():
        raise Exception('permission_denied')
    return prompt_collection, prompt_collection_creator

def is_valid_topic(topic):
    if len(topic) > 0 and len(topic) <= 32:
        return True
    elif len(topic) == 0:
        raise Exception('กรุณาใส่ Topic')
    else:
        raise Exception('Topic ควรต่ำกว่า 32 ตัวอักษร')

def is_valid_description(description):
    if len(description) <= 188:
        return True
    else:
        raise Exception('รายละเอียดควรต่ำกว่า 188 ตัวอักษร')

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

@prompt_collection.route('/prompt-collection/<slug>', methods=['GET'])
def main(slug):
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

        return render_template('prompt_collection/main.html', title=_('The deep pub'), prompt_collection=prompt_collection, creator=creator, liked=liked, bookmarked=bookmarked, followed=followed)

@prompt_collection.route('/prompt-collection/<profile_name>/<slug>/like', methods=['POST'])
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

@prompt_collection.route('/prompt-collection/<profile_name>/<slug>/bookmark', methods=['POST'])
@login_required
def bookmark(profile_name, slug):
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

@prompt_collection.route('/upload-prompt', methods=['GET', 'POST'])
@login_required
def upload_prompt():
    if request.method == 'GET':
        return render_template('prompt_collection/upload.html', title=_('The deep pub'))
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

@prompt_collection.route('/destroy-prompt/<profile_name>/<slug>', methods=['GET', 'POST'])
@login_required
def destroy(profile_name, slug):
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
                utils.delete_image_in_spaces(prompt['image_url'])
            feature_db.prompt_collection.delete_one({'_id': prompt_collection['_id']})
            return redirect('/')
        else:
            flash(_('กรุณาใส่ slug ให้ถูกต้อง'))
            return redirect(url_for('prompt_collection.destroy', slug=slug, profile_name=profile_name))

    if request.method == 'GET':
        try:
            prompt_collection, prompt_collection_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)
        return render_template('prompt_collection/destroy.html', title=_('The deep pub'), form=form, slug=prompt_collection['slug'], profile_name=prompt_collection_creator['profile_name'])
    return make_response(jsonify({"status": 0, 'error_message': 'error_code in destroy GET of prompt_collection'}), 200)

@prompt_collection.route('/edit-prompt-collection/<profile_name>/<slug>', methods=['GET'])
@login_required
def edit(profile_name, slug):
    if request.method == 'GET':
        try:
            prompt_collection, prompt_collection_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)
        return render_template('prompt_collection/edit.html', title=_('The deep pub'), slug=prompt_collection['slug'], profile_name=prompt_collection_creator['profile_name'])
    return make_response(jsonify({"status": 0, 'error_message': 'error_code in edit of prompt_collection'}), 200)

@prompt_collection.route('/get-prompt-collection/<profile_name>/<slug>/edit', methods=['GET'])
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

@prompt_collection.route('/submit-edit-prompt/<slug>', methods=['PATCH'])
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
            if prompt['image_url'] in original_prompt_urls:
                prompts.append(prompt)
                original_prompts.remove(prompt)
            elif not prompt['image_url'].startswith('https://tdp-public.sgp1.cdn.digitaloceanspaces.com/') and utils.is_valid_base64_image(prompt['image_url']):
                prompt['image_url'] = utils.upload_base64_to_spaces(current_user.get_profile_name(), 'prompt_collections/' + current_user.get_profile_name() + '_' + slug, prompt['image_url'])
                prompts.append(prompt)

        if len(prompts) == 0:
            return make_response(jsonify({'status': 0, 'error_message': 'กรุณาอัพโหลดรูปภาพ'}), 200)

        for prompt in original_prompts:
            utils.delete_image_in_spaces(prompt['image_url'])

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
        return make_response(jsonify({"status": 1, "redirect_url": '/en/prompt-collection/' + slug}), 200)
