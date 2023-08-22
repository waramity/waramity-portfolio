from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, json)

from flask_babel import _, refresh


ai_hub = Blueprint('ai_hub', __name__, template_folder='templates', url_prefix='/<lang_code>' )

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
    return render_template('ai_hub/index.html', title=_('waramity portfolio'))
