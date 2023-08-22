from flask import Flask, g, request, redirect, url_for
from flask_babel import Babel
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2 import WebApplicationClient
import os
from flask_socketio import SocketIO

from config import Config
from dotenv import load_dotenv
from pymongo import MongoClient
from flask_login import UserMixin
from bson import ObjectId



load_dotenv()

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)

app.debug = True  # Enable debug mode
app.config.from_object(Config)

babel = Babel(app)
db = SQLAlchemy()
client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

mongo_client = MongoClient()
user_db = mongo_client["user"]
feature_db = mongo_client["feature"]



# socketio.init_app(app, manage_session=False)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

from app.features.main import main as main_blueprint
app.register_blueprint(main_blueprint)

from app.features.crypto import crypto as crypto_blueprint, socketio as crypto_socket
app.register_blueprint(crypto_blueprint)

from app.features.dating import dating as dating_blueprint, socketio as dating_socket
app.register_blueprint(dating_blueprint)

from app.features.auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from app.features.ai_hub import ai_hub as ai_hub_blueprint
app.register_blueprint(ai_hub_blueprint)

crypto_socket.init_app(app)
dating_socket.init_app(app)
db.init_app(app)

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

from .models import Social, User as DatingUser, Gender, Passion

@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('mongo_'):
        user_id = ObjectId(user_id)
        user_json = user_db.profile.find_one({'_id': user_id})
        if not user_json:
            return None
        return User(user_json)
    else:
        return DatingUser.query.get(user_id)

class User(UserMixin):
    def __init__(self, user_json):
        # user_json['_id'] = str(user_json.get('_id'))
        self.user_json = user_json

    def get_id(self):
        object_id = self.user_json.get('_id')
        return object_id

    def get_slug(self):
        slug = self.user_json.get('slug')
        return slug

    def get_profile_name(self):
        profile_name = self.user_json.get('profile_name')
        if not profile_name:
            return None
        return str(profile_name)

    def get_profile_image(self):
        profile_image = self.user_json.get('image_url')
        if not profile_image:
            return None
        return str(profile_image)

    def is_authenticated():
        return True

    def is_active():
        return True

    def is_anonymous():
        return True


def social_generator():
    social_names = ['google', 'facebook', 'twitter', 'apple']

    for name in social_names:
        social = Social(
            name=name
        )
        db.session.add(social)

    db.session.commit()

gender_names = ['Man', 'Woman']

def gender_generator():
    for name in gender_names:
        gender = Gender(
            name=name
        )
        db.session.add(gender)

    db.session.commit()

def passion_generator():
    passion_names = ['Cycling', 'Outdoors', 'Walking', 'Cooking', 'Working out', 'Athlete', 'Craft Beer', 'Writer', 'Politics', 'Climbing', 'Foodie', 'Art', 'Karaoke', 'Yoga', 'Blogging', 'Disney', 'Surfing', 'Soccer', 'Dog lover', 'Cat lover', 'Movies', 'Swimming', 'Hiking', 'Running', 'Music', 'Fashion', 'Vlogging', 'Astrology', 'Coffee', 'Instagram', 'DIY', 'Board Games', 'Environmentalism', 'Dancing', 'Volunteering', 'Trivia', 'Reading', 'Tea', 'Language Exchange', 'Shopping', 'Wine', 'Travel']

    for name in passion_names:
        passion = Passion(
            name=name
        )
        db.session.add(passion)

    db.session.commit()

with app.app_context():
    # db.drop_all()
    db.create_all()
    social_generator()
    gender_generator()
    passion_generator()
