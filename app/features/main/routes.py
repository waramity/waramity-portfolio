
from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, json, session)
from flask_babel import _, refresh
import os
from app import app

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
        abort(404)

# Multiligual End

def load_json(filename):
    filename = os.path.join(app.static_folder, filename)
    with open(filename) as json_file:
        json_data = json.load(json_file)
    return json_data

@main.route('/')
def index():
    session['platform'] = 'none'
    skill_data = load_json('data/skill.json')
    system_architecture_icons = ['python.png', 'javascript.png', 'html.png', 'css.png', 'jquery.png', 'scss.png', 'type-script.png', 'babel.png', 'flask.png', 'sqlalchemy.png', 'react.png', 'socket-io.png', 'digital-ocean.png', 'mongo.jpg', 'tailwind.png', 'oauth.png', 'postgres.png', 'bootstrap.webp']
    return render_template('main/index.html', title=_('waramity portfolio'), skill_data=skill_data, system_architecture_icons=system_architecture_icons)

@main.route('/get_skill_data/<int:index>')
def get_skill_data(index):
    index -= 1
    skill_data = load_json('data/skill.json')
    if index < 1 or index > len(skill_data):
        return jsonify({"error": "Invalid index"})
    return jsonify(skill_data[index - 1])

@main.route('/get_skill_nav')
def get_skill_nav():
    skill_data = load_json('data/skill.json')
    return jsonify(skill_data)
