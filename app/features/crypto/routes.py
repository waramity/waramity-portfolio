
from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, json)

from flask_babel import _, refresh

from app import coin_gecko, socketio

crypto = Blueprint('crypto', __name__, template_folder='templates', url_prefix='/<lang_code>' )

# Multiligual Start
@crypto.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)

@crypto.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')

@crypto.before_request
def before_request():
    if g.lang_code not in current_app.config['LANGUAGES']:
        abort(404)

# Multiligual End

coin = coin_gecko.get_coin_market_chart_by_id(id="bitcoin", vs_currency="thb", days="1")
print(coin)

@crypto.route('/crypto')
def index():
    return render_template('crypto/index.html', title=_('waramity portfolio'))

@socketio.on('tick')
def handle_tick(data):
    global tick_count
    tick_count += 1
    socketio.emit('tick', {'tick_count': tick_count}, broadcast=True)
