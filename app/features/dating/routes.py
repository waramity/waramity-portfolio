from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, json)

from flask_babel import _, refresh
from flask_login import login_required, current_user



dating = Blueprint('dating', __name__, template_folder='templates', url_prefix='/<lang_code>' )

# Multiligual Start
@dating.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)

@dating.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')

@dating.before_request
def before_request():
    if g.lang_code not in current_app.config['LANGUAGES']:
        abort(404)

# Multiligual End

@dating.route('/dating')
def index():
    if current_user.is_authenticated:
        if current_user.given_name is None:
            return redirect(url_for('auth.create_profile'))
        elif current_user.geolocation_permission == False or current_user.geolocation_permission == None:
            return redirect(url_for('auth.geolocation'))
        else:
            return redirect(url_for('main.app'))

    return render_template('dating/index.html', title=_('Dootua - คู่ชีวิตที่คุณตามหา'))
