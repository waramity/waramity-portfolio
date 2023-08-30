from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response)
from flask_babel import _, refresh
from flask_login import login_required, current_user


from app import db, app, redis, user_db, feature_db, spaces_client

import uuid

import datetime

import base64

from PIL import Image

import io

import time

from bson.objectid import ObjectId

import app.utils as utils

comment = Blueprint('comment', __name__, template_folder='templates', url_prefix='/<lang_code>' )

# Multiligual Start
@comment.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)

@comment.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')

@comment.before_request
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

def is_valid_prompts(prompts):
    if len(prompts) > 6:
        raise Exception('ควรอัพโหลดภาพต่ำกว่า 6 รูป')
    else:
        return True

def is_valid_comment(comment):
    if comment != "<p><br></p>":
        return True
    else:
        raise Exception('กรุณาเขียนคอมเมนต์')

@comment.route('/comment/<item_type>/<item_slug>', methods=['POST', 'GET'])
@login_required
def create(item_type, item_slug):

    if request.method == 'POST' and request.json is not None:

        prompts = request.json['prompts']
        comment = request.json['comment']

        try:
            is_valid_comment(request.json['comment'])
            is_valid_prompts(request.json['prompts'])

            for prompt in prompts:
                utils.is_valid_base64_image(prompt['image_url'])

        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        comment_slug = uuid.uuid4().hex[:11]
        while feature_db.comment.find_one({'slug': comment_slug}):
            comment_slug = uuid.uuid4().hex[:11]

        if item_type == "prompt_collection":
            item_collection = feature_db.prompt_collection
            spaces_path = 'comments/' + 'collection_' + current_user.get_profile_name() + '_' + comment_slug
            redirect_url = '/en/prompt-collection/'
        elif item_type == "prompt_builder":
            item_collection = feature_db.prompt_builder
            spaces_path = 'comments/' + 'builder_' + current_user.get_profile_name() + '_' + comment_slug
            redirect_url = '/en/prompt-builder/'

        for prompt in prompts:
            prompt['image_url'] = utils.upload_base64_to_spaces(current_user.get_profile_name(), spaces_path, prompt['image_url'])

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
        return render_template('comment/create.html', title=_('The deep pub'), item_type=item_type, item_slug=item_slug)

    return make_response(jsonify({"status": 0, 'message': 'error in post comment.'}), 200)


@comment.route('/get-comments/<item_type>/<item_slug>', methods=['GET'])
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


@comment.route('/comment/<item_type>/<item_slug>/<comment_slug>/like', methods=['POST'])
@login_required
def like(item_type, item_slug, comment_slug):
    if request.method == 'POST':
        if item_type == "prompt_collection":
            item_collection = feature_db.prompt_collection

        elif item_type == "prompt_builder":
            item_collection = feature_db.prompt_builder

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

@comment.route('/delete-comment/<comment_slug>', methods=['POST'])
@login_required
def delete(comment_slug):
    if request.method == 'POST':
        comment = feature_db.comment.find_one({'slug': comment_slug})

        if comment['user_id'] == current_user.get_id():

            like_result = feature_db.engagement.delete_many({ 'item_id': comment['_id'], 'item_type': 'comment', 'engage_type': 'like'})
            user_db.profile.find_one_and_update({'_id': comment['user_id']}, {'$inc': {'total_engagement.likes': -like_result.deleted_count}}, return_document=False)

            for prompt in comment["prompts"]:
                utils.delete_image_in_spaces(prompt['image_url'])

            feature_db.comment.delete_one({'_id': comment['_id']})

            return make_response(jsonify({'status': 1}), 200)
