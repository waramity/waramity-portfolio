from flask import Flask, g, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_babel import Babel
from config import Config
from config import BaseConfig
from oauthlib.oauth2 import WebApplicationClient
from flask_socketio import SocketIO
from eventlet import wsgi
import eventlet
from flask_session import Session


# FOr test google authentication
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

db = SQLAlchemy()

app = Flask(__name__)

# TODO run this only in dev
from werkzeug.debug import DebuggedApplication
app.debug = True
app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)
# End TODO run this only in dev

app.config.from_object(Config)
app.config.from_object(BaseConfig)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db.init_app(app)
migrate = Migrate(app, db)
client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])
login_manager = LoginManager()
babel = Babel(app)
socketio = SocketIO()
sess = Session()
sess.init_app(app)

login_manager.login_view = 'auth.login'
login_manager.init_app(app)
socketio.init_app(app, manage_session=False)

from app.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

from app.features.auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from app.features.main import main as main_blueprint
app.register_blueprint(main_blueprint)

from app.features.multilingual import multilingual as multilingual_blueprint
app.register_blueprint(multilingual_blueprint)

from app.features.legal import legal as legal_blueprint
app.register_blueprint(legal_blueprint)

from app.features.management import management as management_blueprint
app.register_blueprint(management_blueprint)

# wsgi.server(eventlet.listen(("127.0.0.1", 8000), app))


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


with app.app_context():

    from app.features.management import destroy_db, create_db, social_generator, gender_generator, passion_generator, user_generator
    #
    # destroy_db()
    # create_db()
    # social_generator()
    # gender_generator()
    # # sexual_orientation_generator()
    # passion_generator()
    #
    # for x in range(20):
    #     user_generator("male")
    #
    # for x in range(20):
    #     user_generator("female")
    #

#     db.session.query(User).delete()
#     db.session.commit()

wsgi.server(eventlet.listen(('127.0.0.1', 5000)), app)
