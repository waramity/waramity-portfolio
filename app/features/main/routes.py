
from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response)
# from flask_babel import _, refresh
# from flask_login import login_required, current_user


# from app import db, app, redis, user_db, feature_db
#
# from app.models import PromptCategory, PromptSubCategory, PromptDetailCategory, PromptSet, ModelCard

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
    # if current_user.is_authenticated:
    #     if current_user.get_profile_name() is None:
    #         return redirect(url_for('profile.create_profile'))
    #
    # model_cards = [ model_card.serialize for model_card in ModelCard.query.all()]
    #
    # prompt_builder_per_page = 10
    # prompt_builder_page = 1
    # prompt_builders = list(feature_db.prompt_builder.find({}, {'name': 1, 'slug': 1, 'user_id': 1, 'updated_date': 1, 'description': 1, 'cover_image_url': 1}).skip((prompt_builder_page - 1) * prompt_builder_per_page).limit(prompt_builder_per_page))
    #
    # for prompt_builder in prompt_builders:
    #     prompt_builder_creator = user_db.profile.find_one({'_id': prompt_builder['user_id']}, {'profile_name': 1})
    #     del prompt_builder["user_id"]
    #     prompt_builder["profile_name"] = prompt_builder_creator["profile_name"]
    #     prompt_builder.pop('_id')

    return render_template('main/index.html', title=_('waramity portfolio'))
