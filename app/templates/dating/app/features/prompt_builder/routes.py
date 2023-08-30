
from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, flash)
from flask_babel import _, refresh
from flask_login import login_required, current_user

from app import db, app, redis, user_db, feature_db, spaces_client

from .views import CreatePromptBuilderForm, DestoryPromptBuilderForm
from werkzeug.datastructures import CombinedMultiDict

import uuid
import datetime, pytz

from slugify import slugify
import base64
from PIL import Image
import io

import time

import json

import app.utils as utils

# from PIL import Image

# from app.models import PromptCategory, PromptSubCategory, PromptDetailCategory, PromptSet, ModelCard

prompt_builder = Blueprint('prompt_builder', __name__, template_folder='templates', url_prefix='/<lang_code>' )

# Multiligual Start
@prompt_builder.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)

@prompt_builder.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')

@prompt_builder.before_request
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

def is_valid_prompt_name(prompt_name):
    if len(prompt_name) >= 2 and len(prompt_name) <= 25:
        return True
    else:
        raise Exception('ชื่อ Prompt ควรมีระหว่าง 2 - 25 ตัวอักษร')

def is_valid_description(description):
    if len(description) <= 150:
        return True
    else:
        raise Exception('Description ควรต่ำกว่า 150 ตัวอักษร')

def is_valid_prompt_builder_name(name):
    if len(name) >= 2 and len(name) <= 35:
        return True
    else:
        raise Exception('ชื่อ Prompt builder ควรมีระหว่าง 2 - 35 ตัวอักษร')

def is_valid_category_name(category_name):
    if len(category_name) >= 2 and len(category_name) <= 15:
        return True
    else:
        raise Exception('Category ควรมีความยาวระหว่าง 2-15 ตัวอักษร')

def is_valid_permission(profile_name, slug):
    prompt_builder = feature_db.prompt_builder.find_one({'slug': slug})
    prompt_builder_creator = user_db.profile.find_one({'_id': prompt_builder['user_id'], 'profile_name': profile_name}, {'profile_name': 1})
    if not prompt_builder_creator or prompt_builder_creator['_id'] != current_user.get_id() or profile_name != current_user.get_profile_name():
        raise Exception('permission_denied')
    return prompt_builder, prompt_builder_creator

def initial_upload_image(profile_name, slug, image_url, old_image_url=""):
    if image_url == "/static/blank-image.png":
        return ""
    if not image_url.startswith('https://tdp-public.sgp1.cdn.digitaloceanspaces.com/'):
        if utils.is_valid_base64_image(image_url):
            if old_image_url is not "":
                utils.delete_image_in_spaces(old_image_url)
            cdn_url = utils.upload_base64_to_spaces(profile_name, 'prompt_builders/' + profile_name + '_' + slug, image_url)
        else:
            raise Exception('กรุณาอัพโหลดรูป')
    else:
        cdn_url = image_url
    return cdn_url

def get_prompt_object(prompt_builder_id, user_id, category_slug, prompt_slug):

    cursor = feature_db.prompt_builder.aggregate([
        { "$unwind": "$categories" },
        { "$unwind": "$categories.prompts" },
        {
            "$match": {
              "categories.prompts.slug": prompt_slug
            }
        },
        {
            "$project": {
                "slug": "$categories.prompts.slug",
                "name": "$categories.prompts.name",
                "image_url": "$categories.prompts.image_url",
            }
        },
        { '$limit': 1 }
    ])
    doc = next(cursor, None)
    return doc

# Function End

# Route Start

@prompt_builder.route('/prompt-builder/<slug>', methods=['GET', 'POST'])
def main(slug):

    prompt_builder = feature_db.prompt_builder.find_one({'slug': slug})
    prompt_builder['updated_date'] = prompt_builder['updated_date'].isoformat()
    prompt_builder_creator = user_db.profile.find_one({'_id': prompt_builder['user_id']})

    liked = False
    bookmarked = False
    followed = False
    if current_user.is_authenticated:
        like = feature_db.engagement.find_one({'item_id': prompt_builder['_id'], 'user_id': current_user.get_id(), 'engage_type': 'like', 'item_type': 'prompt_builder'})
        liked = like is not None

        bookmark = feature_db.engagement.find_one({'item_id': prompt_builder['_id'], 'user_id': current_user.get_id(), 'engage_type': 'bookmark', 'item_type': 'prompt_builder'})
        bookmarked = bookmark is not None

        follow = user_db.follow.find_one({'follower_id': current_user.get_id(), 'following_id': prompt_builder_creator['_id']})
        followed = follow is not None

    prompt_builder = {
        "name": prompt_builder["name"],
        "slug": prompt_builder["slug"],
        "cover_image_url": prompt_builder["cover_image_url"],
        "updated_date": prompt_builder["updated_date"],
        "description": prompt_builder["description"],
        "likes": prompt_builder["likes"]
    }

    prompt_builder_creator = {
        "profile_name": prompt_builder_creator["profile_name"],
        "registered_on": prompt_builder_creator["registered_on"],
        "image_url": prompt_builder_creator["image_url"],
    }

    return render_template('prompt_builder/main.html', title=_('The deep pub'), prompt_builder=prompt_builder, prompt_builder_creator=prompt_builder_creator, liked=liked, bookmarked=bookmarked, followed=followed)

@prompt_builder.route('/prompt-builder/<profile_name>/<slug>/like', methods=['POST'])
@login_required
def like(profile_name, slug):
    if request.method == 'POST':
        user = user_db.profile.find_one({'profile_name': profile_name})
        prompt_builder = feature_db.prompt_builder.find_one({'user_id': user['_id'], 'slug': slug})

        like = feature_db.engagement.find_one({'user_id': current_user.get_id(), 'item_id': prompt_builder['_id'], 'item_type': 'prompt_builder', 'engage_type': 'like'})

        if like:
            feature_db.engagement.delete_one({'_id': like['_id']})
            feature_db.prompt_builder.find_one_and_update({'_id': prompt_builder['_id']}, {'$inc': {'likes': -1}}, return_document=False)
            user_db.profile.find_one_and_update({'_id': prompt_builder['user_id']}, {'$inc': {'total_engagement.likes': -1}}, return_document=False)
            return make_response(jsonify({"status": 1}), 200)

        like = {'user_id': current_user.get_id(), 'item_id': prompt_builder['_id'], 'item_type': 'prompt_builder', 'engage_type': 'like', 'created_at': datetime.datetime.now()}
        feature_db.engagement.insert_one(like)
        feature_db.prompt_builder.find_one_and_update({'_id': prompt_builder['_id']}, {'$inc': {'likes': 1}}, return_document=False)
        user_db.profile.find_one_and_update({'_id': prompt_builder['user_id']}, {'$inc': {'total_engagement.likes': 1}}, return_document=False)
        return make_response(jsonify({"status": 1}), 200)

@prompt_builder.route('/prompt-builder/<profile_name>/<slug>/bookmark', methods=['POST'])
@login_required
def bookmark(profile_name, slug):
    if request.method == 'POST':
        user = user_db.profile.find_one({'profile_name': profile_name})
        prompt_builder = feature_db.prompt_builder.find_one({'user_id': user['_id'], 'slug': slug})

        bookmark = feature_db.engagement.find_one({'user_id': current_user.get_id(), 'item_id': prompt_builder['_id'], 'item_type': 'prompt_builder', 'engage_type': 'bookmark'})

        if bookmark:
            feature_db.engagement.delete_one({'_id': bookmark['_id']})
            user_db.profile.find_one_and_update({'_id': prompt_builder['user_id']}, {'$inc': {'total_engagement.bookmarks': -1}}, return_document=False)
            return make_response(jsonify({"status": 1}), 200)

        bookmark = {'user_id': current_user.get_id(), 'item_id': prompt_builder['_id'], 'item_type': 'prompt_builder', 'engage_type': 'bookmark', 'created_at': datetime.datetime.now()}
        feature_db.engagement.insert_one(bookmark)
        user_db.profile.find_one_and_update({'_id': prompt_builder['user_id']}, {'$inc': {'total_engagement.bookmarks': 1}}, return_document=False)

        return make_response(jsonify({"status": 1}), 200)

@prompt_builder.route('/create-prompt-builder', methods=['GET', 'POST'])
@login_required
def create():

    if current_user.is_authenticated:
        if current_user.get_profile_name() is None:
            return redirect(url_for('auth.create_profile'))

    form = CreatePromptBuilderForm(CombinedMultiDict((request.files, request.form)))
    if request.method == 'POST' and form.validate_on_submit():
        builder_name = form.builder_name.data

        slug = uuid.uuid4().hex[:11]
        while feature_db.prompt_builder.find_one({'slug': slug}):
            slug = uuid.uuid4().hex[:11]

        builder = {
            'name': builder_name,
            'slug':  slug,
            'user_id': current_user.get_id(),
            'created_date': datetime.datetime.now(),
            'updated_date': datetime.datetime.now(),
            'description': '',
            'cover_image_url': '',
            'likes': 0,
            'categories': [],
        }

        prompt_builder = feature_db.prompt_builder.insert_one(builder)

        return redirect(url_for('prompt_builder.main', slug=slug, profile_name=current_user.get_profile_name()))

    return render_template('prompt_builder/create.html', title=_('The deep pub'), form=form)

@prompt_builder.route('/destroy-prompt-builder/<profile_name>/<slug>', methods=['GET', 'POST'])
@login_required
def destroy(profile_name, slug):
    form = DestoryPromptBuilderForm(CombinedMultiDict((request.files, request.form)))

    if request.method == 'POST' and form.validate_on_submit():
        if slug == form.slug.data:
            try:
                prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, form.slug.data)
            except Exception as e:
                return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

            bookmark_result = feature_db.engagement.delete_many({ 'item_id': prompt_builder['_id'], 'item_type': 'prompt_builder', 'engage_type': 'bookmark'})
            like_result = feature_db.engagement.delete_many({ 'item_id': prompt_builder['_id'], 'item_type': 'prompt_builder', 'engage_type': 'like'})

            comment_like_result = feature_db.engagement.delete_many({ 'parent_id': prompt_builder['_id'], 'item_type': 'comment', 'engage_type': 'like'})

            comments = list(feature_db.comment.find({ 'item.id': prompt_builder['_id'], 'item.type': 'prompt_builder'}))

            for comment in comments:
                for prompt in comment['prompts']:
                    utils.delete_image_in_spaces(prompt['image_url'])

            deleted_comment = feature_db.comment.delete_many({ 'item.id': prompt_builder['_id'], 'item.type': 'prompt_builder'})

            user_db.profile.find_one_and_update({'_id': prompt_builder['user_id']}, {'$inc': {'total_engagement.likes': -like_result.deleted_count, 'total_engagement.bookmarks': -bookmark_result.deleted_count, 'total_engagement.comments': -deleted_comment.deleted_count}}, return_document=False)

            if prompt_builder['cover_image_url'] != '':
                utils.delete_image_in_spaces(prompt_builder['cover_image_url'])

            for category in prompt_builder['categories']:
                for prompt in category['prompts']:
                    utils.delete_image_in_spaces(prompt['image_url'])

            feature_db.prompt_builder.delete_one({'_id': prompt_builder['_id']})
            return redirect('/')
        else:
            flash(_('กรุณาใส่ slug ให้ถูกต้อง'))
            return redirect(url_for('prompt_builder.destroy', slug=slug, profile_name=profile_name))

    if request.method == 'GET':
        try:
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)
        return render_template('prompt_builder/destroy.html', title=_('The deep pub'), form=form, slug=prompt_builder['slug'], profile_name=prompt_builder_creator['profile_name'])
    return make_response(jsonify({"status": 0, 'error_message': 'error_code in destroy GET of prompt_builder'}), 200)

@prompt_builder.route('/edit-prompt-builder/<profile_name>/<slug>', methods=['GET'])
@login_required
def edit(profile_name, slug):
    if request.method == 'GET':
        try:
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)
        return render_template('prompt_builder/edit.html', title=_('The deep pub'), slug=prompt_builder['slug'], profile_name=prompt_builder_creator['profile_name'])
    return make_response(jsonify({"status": 0, 'error_message': 'error_code in edit of prompt_builder'}), 200)


@prompt_builder.route('/submit-edit-prompt-builder/<profile_name>/<slug>', methods=['POST'])
@login_required
def submit_edit(profile_name, slug):
    if request.method == 'POST' and request.json is not None:
        try:
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
            is_valid_description(request.json['description'])
            is_valid_prompt_builder_name(request.json['name'])
            cdn_url = initial_upload_image(profile_name, slug, request.json['cover_image'], prompt_builder["cover_image_url"])
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        updated_prompt_builder = {
            '$set': {
                    'name': request.json['name'],
                    'description': request.json['description'],
                    'cover_image_url': cdn_url,
                    'updated_date': datetime.datetime.now(),
            }
        }

        feature_db.prompt_builder.update_one({"_id": prompt_builder['_id'], "user_id": prompt_builder_creator['_id']}, updated_prompt_builder)
        return make_response(jsonify({"status": 1, 'message': 'เซฟเรียบร้อยแล้ว'}), 200)
    return make_response(jsonify({"status": 0, 'error_message': 'error_code in submit_edit of prompt_builder'}), 200)

@prompt_builder.route('/get-prompt-builder-info/<profile_name>/<slug>', methods=['GET'])
@login_required
def get_prompt_builder_info(profile_name, slug):
    if request.method == 'GET':
        try:
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        prompt_builder_info = {
            'name': prompt_builder['name'],
            'description': prompt_builder['description'],
            'cover_image_url': prompt_builder['cover_image_url'],
            'updated_date': prompt_builder['updated_date'],
        }
        return make_response(jsonify({"status": 1, 'prompt_builder_info': prompt_builder_info}), 200)
    return make_response(jsonify({"status": 0, "error_message": "error_code in get_prompt_builder_info of prompt_builder"}), 200)

@prompt_builder.route('/get-categories/<profile_name>/<slug>', methods=['GET'])
@login_required
def get_categories(profile_name, slug):
    if request.method == 'GET':

        try:
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        categories = [{k: v for k, v in category.items() if k != 'prompts'} for category in prompt_builder['categories']]
        categories = sorted(categories, key=lambda x: x['order'])
        return make_response(jsonify({"status": 1, "categories": categories}), 200)
    return make_response(jsonify({"status": 0, "error_message": "error_code in get_categories of prompt_builder"}), 200)

@prompt_builder.route('/add-category-prompt-builder/<profile_name>/<slug>', methods=['POST'])
@login_required
def add_category(profile_name, slug):
    if request.method == 'POST' and request.json is not None:
        try:
            is_valid_category_name(request.json['category_name'])
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        category_slug = slugify(request.json['category_name']) + '-' + uuid.uuid4().hex[:4]
        while feature_db.prompt_builder.find_one({'categories.slug': category_slug}):
            category_slug = slugify(request.json['category_name']) + '-' + uuid.uuid4().hex[:4]

        if len(prompt_builder['categories']) == 0:
            category_json = {"$push": {"categories": {"name": request.json['category_name'], "slug": category_slug, "order": 0, "prompts": []}}}
        else:
            max_order = max([category.get('order', 0) for category in prompt_builder.get('categories', [])])
            category_json = {"$push": {"categories": {"name": request.json['category_name'], "slug": category_slug, "order": max_order + 1, "prompts": []}}}

        feature_db.prompt_builder.update_one({"_id": prompt_builder['_id']}, category_json)
        category = feature_db.prompt_builder.find_one({'categories': {'$elemMatch': {'name': request.json['category_name'], 'slug':category_slug }}}, {"categories.$": 1})['categories'][0]
        return make_response(jsonify({"status": 1, "category": category}), 200)

    return make_response(jsonify({"status": 0, "error_message": "error_code in add_category of prompt_builder"}), 200)

@prompt_builder.route('/submit-edit-category-name-prompt-builder/<profile_name>/<slug>', methods=['POST'])
@login_required
def submit_edit_category_name(profile_name, slug):
    if request.method == 'POST' and request.json is not None:
        try:
            is_valid_category_name(request.json['old_category_name'])
            is_valid_category_name(request.json['new_category_name'])
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        feature_db.prompt_builder.update_one({'_id': prompt_builder['_id'], 'user_id': prompt_builder_creator['_id'], 'categories': {'$elemMatch': {'name': request.json['old_category_name'], 'slug':request.json['category_slug'] }}}, {"$set": {"categories.$.name": request.json['new_category_name']}} )
        category = feature_db.prompt_builder.find_one({'_id': prompt_builder['_id'], 'user_id': prompt_builder_creator['_id'], 'categories': {'$elemMatch': {'name': request.json['new_category_name'], 'slug':request.json['category_slug'] }}}, {"categories.$": 1})['categories'][0]
        return make_response(jsonify({"status": 1, "category": category}), 200)
    return make_response(jsonify({"status": 0, "error_message": "error_code in add_category of prompt_builder"}), 200)

@prompt_builder.route('/submit-delete-category-name-prompt-builder/<profile_name>/<slug>', methods=['POST'])
@login_required
def submit_delete_category_name(profile_name, slug):
    if request.method == 'POST' and request.json is not None:

        try:
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        prompts = feature_db.prompt_builder.find_one({'_id': prompt_builder['_id'], 'user_id': prompt_builder_creator['_id'], 'categories': {'$elemMatch': {'slug': request.json['category_slug'] }}}, {"categories.$": 1})['categories'][0]['prompts']
        for prompt in prompts:
            utils.delete_image_in_spaces(prompt['image_url'])

        feature_db.prompt_builder.update_one({'_id': prompt_builder['_id'], 'user_id': prompt_builder_creator['_id'], 'categories': {'$elemMatch': {'name': request.json['category_name'], 'slug': request.json['category_slug'] }}}, {"$pull": {"categories": {"slug": request.json['category_slug']}}} )
        return make_response(jsonify({"status": 1, "category": {"slug": request.json['category_slug']}}), 200)
    return make_response(jsonify({"status": 0, "error_message": "error_code in submit_delete_category_name of prompt_builder"}), 200)

@prompt_builder.route('/update-category-order-prompt-builder/<profile_name>/<slug>', methods=['POST'])
@login_required
def update_category_order(profile_name, slug):
    if request.method == 'POST' and request.json is not None:

        try:
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        category_order = request.json['category_order']
        for i, category_slug in enumerate(category_order):
            feature_db.prompt_builder.update_one({'_id': prompt_builder['_id'], 'user_id': current_user.get_id(), 'categories': {'$elemMatch': { 'slug': category_slug }}}, {"$set": {"categories.$.order": i}} )
        return make_response(jsonify({"status": 1, "message": "success"}), 200)
    return make_response(jsonify({"status": 0, "error_message": "error_code in update_category_order of prompt_builder"}), 200)


@prompt_builder.route('/add-prompt-prompt-builder/<profile_name>/<slug>/<category_slug>', methods=['POST'])
@login_required
def add_prompt(profile_name, slug, category_slug):
    if request.method == 'POST':
        try:
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
            is_valid_prompt_name(request.json['prompt']['name'])
            # is_valid_prompt_description(request.json['prompt']['description'])

            prompt_slug = slugify(request.json['prompt']['name']) + '-' + uuid.uuid4().hex[:4]

            while feature_db.prompt_builder.find_one({'_id': prompt_builder['_id'], 'user_id': prompt_builder_creator['_id'], 'categories.slug': category_slug, 'categories.prompts': {'$elemMatch': { 'slug': prompt_slug }}}):
                prompt_slug = slugify(request.json['prompt']['name']) + '-' + uuid.uuid4().hex[:4]

            if not request.json['prompt']['base64_image'].startswith('https://tdp-public.sgp1.cdn.digitaloceanspaces.com/'):
                utils.is_valid_base64_image(request.json['prompt']['base64_image'])
                cdn_url = utils.upload_base64_to_spaces(profile_name, 'prompt_builders/' + profile_name + '_' + slug, request.json['prompt']['base64_image'])
            else:
                cdn_url = request.json['prompt']['base64_image']
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        prompt_json = {"$push": {"categories.$[cat].prompts": {"name": request.json['prompt']['name'], "slug": prompt_slug, "image_url": cdn_url}}}
        feature_db.prompt_builder.update_one(
          { '_id': prompt_builder['_id'], 'user_id': prompt_builder_creator['_id'] },
          prompt_json,
          array_filters=[ { "cat.slug": category_slug } ],
          upsert=False
        );

        return make_response(jsonify({"status": 1, "prompt": {"name": request.json['prompt']['name'], "slug": prompt_slug, "image_url": cdn_url}}), 200)
    return make_response(jsonify({"status": 0, "error_message": "error_code in add_prompts of prompt_builder"}), 200)

@prompt_builder.route('/submit-remove-prompt-prompt-builder/<profile_name>/<slug>/<category_slug>', methods=['PATCH'])
@login_required
def submit_remove_prompt(profile_name, slug, category_slug):
    if request.method == 'PATCH' and request.json is not None:
        try:
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)
        prompt_json = {"$pull": {"categories.$[cat].prompts": {"slug": request.json['prompt']['slug']}}}
        result = feature_db.prompt_builder.find_one_and_update(
          { '_id': prompt_builder['_id'], 'user_id': prompt_builder_creator['_id'] },
          prompt_json,
          array_filters=[ { "cat.slug": category_slug } ],
        );

        for category in result['categories']:
            if category['slug'] == category_slug:
                for prompt in category['prompts']:
                        if prompt['slug'] == request.json['prompt']['slug']:
                            utils.delete_image_in_spaces(prompt['image_url'])
                        break
                break

        return make_response(jsonify({"status": 1, "prompt": {"slug": request.json['prompt']['slug']}}), 200)
    return make_response(jsonify({"status": 0, "error_message": "error_code in submit_remove_prompts of prompt_builder"}), 200)

@prompt_builder.route('/submit-edit-prompt-prompt-builder/<profile_name>/<slug>/<category_slug>', methods=['PATCH'])
@login_required
def submit_edit_prompt(profile_name, slug, category_slug):
    if request.method == 'PATCH' and request.json is not None:
        try:
            prompt_builder, prompt_builder_creator = is_valid_permission(profile_name, slug)
            is_valid_prompt_name(request.json['prompt']['name'])
            prompt = get_prompt_object(prompt_builder['_id'], prompt_builder_creator['_id'], category_slug, request.json['prompt']['slug'])
            # cdn_url = initial_upload_image(profile_name, slug, request.json['prompt']['base64_image'], prompt["image_url"])
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        # prompt_json = {"$set": {"categories.$[cat].prompts.$[pro]": {"name": request.json['prompt']['name'], "slug": request.json['prompt']['slug'], ''}}}
        prompt_json = {"$set": {"categories.$[cat].prompts.$[pro]": {"name": request.json['prompt']['name'], "slug": request.json['prompt']['slug'], "image_url": prompt['image_url']}}}
        feature_db.prompt_builder.update_one(
          { '_id': prompt_builder['_id'], 'user_id': prompt_builder_creator['_id'] },
          prompt_json,
          array_filters=[ { "cat.slug": category_slug },  {"pro.slug": request.json['prompt']['slug']} ],
          upsert=False
        );

        return make_response(jsonify({'status': 1, 'prompt': {'name': request.json['prompt']['name'], 'image_url': prompt['image_url'], 'slug': request.json['prompt']['slug']}}), 200)
    return make_response(jsonify({"status": 0, "error_message": "error_code in submit_edit_prompt of prompt_builder"}), 200)

@prompt_builder.route('/get-categories/public/<slug>', methods=['GET'])
def get_categories_public(slug):
    if request.method == 'GET':
        try:

            prompt_builder = feature_db.prompt_builder.find_one({'slug': slug})

        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        categories = sorted(prompt_builder['categories'], key=lambda x: x['order'])
        return make_response(jsonify({"status": 1, "categories": categories}), 200)
    return make_response(jsonify({"status": 0, "error_message": "error_code in get_categories of prompt_builder"}), 200)

@prompt_builder.route('/get-prompts-prompt-builder/<slug>/<category_slug>', methods=['GET'])
def get_prompts(slug, category_slug):
    if request.method == 'GET':
        try:
            prompt_builder = feature_db.prompt_builder.find_one({'slug': slug})
        except Exception as e:
            return make_response(jsonify({"status": 0, 'error_message': str(e)}), 200)

        category = feature_db.prompt_builder.find_one({'_id': prompt_builder['_id'], 'categories.slug': category_slug}, {"categories.$": 1})['categories'][0]
        prompts = category['prompts']

        return make_response(jsonify({"status": 1, "prompts": prompts}), 200)
    return make_response(jsonify({"status": 0, "error_message": "error_code in get_prompts of prompt_builder"}), 200)

# Route End
