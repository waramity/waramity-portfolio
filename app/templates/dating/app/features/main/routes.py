
from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response)
from flask_babel import _, refresh
from flask_login import login_required, current_user


from app import db, app, redis, user_db, feature_db

from app.models import PromptCategory, PromptSubCategory, PromptDetailCategory, PromptSet, ModelCard

main = Blueprint('main', __name__, template_folder='templates', url_prefix='/<lang_code>' )

# Multiligual Start
@main.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)

@main.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')

@main.before_request
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

@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.get_profile_name() is None:
            return redirect(url_for('profile.create_profile'))

    model_cards = [ model_card.serialize for model_card in ModelCard.query.all()]

    prompt_builder_per_page = 10
    prompt_builder_page = 1
    prompt_builders = list(feature_db.prompt_builder.find({}, {'name': 1, 'slug': 1, 'user_id': 1, 'updated_date': 1, 'description': 1, 'cover_image_url': 1}).skip((prompt_builder_page - 1) * prompt_builder_per_page).limit(prompt_builder_per_page))

    for prompt_builder in prompt_builders:
        prompt_builder_creator = user_db.profile.find_one({'_id': prompt_builder['user_id']}, {'profile_name': 1})
        del prompt_builder["user_id"]
        prompt_builder["profile_name"] = prompt_builder_creator["profile_name"]
        prompt_builder.pop('_id')

    return render_template('main/index.html', title=_('The deep pub'), model_cards=model_cards, prompt_builders=prompt_builders)

@main.route('/prompt-builder-demo')
def prompt_builder_demo():
    prompt_categories = [ prompt_category.serialize for prompt_category in PromptCategory.query.all()]
    return render_template('prompt_builder/demo.html', title=_('The deep pub'), prompt_categories=prompt_categories)

@main.route('/get-prompt-details/<sub_category_id>', methods=['GET'])
def get_prompt_details(sub_category_id):
    if request.method == 'GET':
        prompt_sub_category = PromptSubCategory.query.filter(PromptSubCategory.id==str(sub_category_id)).first()
        if prompt_sub_category is not None:
            prompt_detail_categories = prompt_sub_category.serialize
            return make_response(jsonify(prompt_detail_categories), 200)

@main.route('/get-prompt-sets', methods=['GET'])
def get_prompt_sets():
    if request.method == 'GET':
        prompt_sets = PromptSet.query.all()
        if prompt_sets is not None:
            prompt_sets_json = []
            for prompt_set in prompt_sets:
                prompt_sets_json.append(prompt_set.serialize)
            return make_response(jsonify(prompt_sets_json), 200)
        # return make_response("", 204)

@main.route('/get-prompts/<prompt_detail_category_id>', methods=['GET'])
def get_prompts(prompt_detail_category_id):
    if request.method == 'GET':
        prompt_detail_category = PromptDetailCategory.query.filter(PromptDetailCategory.id==str(prompt_detail_category_id)).first()
        if prompt_detail_category is not None:
            prompts = prompt_detail_category.serialize
            return make_response(jsonify(prompts), 200)

@main.route('/copy-prompt/<prompt_id>', methods=['PUT'])
def copy_prompt(prompt_id):
    if request.method == 'PUT':
        redis.incr(f'prompt:{prompt_id}:copies')
        return '', 204

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.display_name)
