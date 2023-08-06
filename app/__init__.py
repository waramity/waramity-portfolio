from flask import Flask, g, request, redirect, url_for
from flask_babel import Babel
from config import Config

from pycoingecko import CoinGeckoAPI
from flask_socketio import SocketIO

app = Flask(__name__)
babel = Babel(app)
coin_gecko = CoinGeckoAPI()
socketio = SocketIO()

socketio.init_app(app, manage_session=False)

app.config.from_object(Config)

from app.features.main import main as main_blueprint
app.register_blueprint(main_blueprint)

from app.features.crypto import crypto as crypto_blueprint
app.register_blueprint(crypto_blueprint)


@babel.localeselector
def get_locale():
    if not g.get('lang_code', None):
        g.lang_code = request.accept_languages.best_match(
            app.config['LANGUAGES']) or app.config['LANGUAGES'][0]
    return g.lang_code

@app.route('/')
def index():
    if not g.get('lang_code', None):
        get_locale()
    return redirect(url_for('main.index'))
