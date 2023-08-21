from flask import Flask, g, request, redirect, url_for
from flask_babel import Babel
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2 import WebApplicationClient
import os

from config import Config
from dotenv import load_dotenv

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



# socketio.init_app(app, manage_session=False)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

from app.features.main import main as main_blueprint
app.register_blueprint(main_blueprint)

from app.features.crypto import crypto as crypto_blueprint, socketio as crypto_socket
app.register_blueprint(crypto_blueprint)

from app.features.dating import dating as dating_blueprint
app.register_blueprint(dating_blueprint)

from app.features.auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

crypto_socket.init_app(app)
db.init_app(app)

from .models import Social, User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

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


def social_generator():
    social_names = ['google', 'facebook', 'twitter', 'apple']

    for name in social_names:
        social = Social(
            name=name
        )
        db.session.add(social)

    db.session.commit()


with app.app_context():
    db.create_all()
    social_generator()


# async_mode = None
# socketio = SocketIO(app, async_mode=async_mode)
# thread = None
# thread_lock = Lock()
#
# def background_thread():
#     count = 0
#     while True:
#         socketio.sleep(10)
#         count += 1
#         print(count)
#         # socketio.emit('my_response',
#         #               {'data': 'Server generated event', 'count': count},
#         #               namespace='/test')
#
# class MyNamespace(Namespace):
#     # def on_my_event(self, message):
#     #     session['receive_count'] = session.get('receive_count', 0) + 1
#     #     emit('my_response',
#     #          {'data': message['data'], 'count': session['receive_count']})
#
#     # def on_my_broadcast_event(self, message):
#     #     session['receive_count'] = session.get('receive_count', 0) + 1
#     #     emit('my_response',
#     #          {'data': message['data'], 'count': session['receive_count']},
#     #          broadcast=True)
#     #
#     # def on_join(self, message):
#     #     join_room(message['room'])
#     #     session['receive_count'] = session.get('receive_count', 0) + 1
#     #     emit('my_response',
#     #          {'data': 'In rooms: ' + ', '.join(rooms()),
#     #           'count': session['receive_count']})
#     #
#     # def on_leave(self, message):
#     #     leave_room(message['room'])
#     #     session['receive_count'] = session.get('receive_count', 0) + 1
#     #     emit('my_response',
#     #          {'data': 'In rooms: ' + ', '.join(rooms()),
#     #           'count': session['receive_count']})
#     #
#     # def on_close_room(self, message):
#     #     session['receive_count'] = session.get('receive_count', 0) + 1
#     #     emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
#     #                          'count': session['receive_count']},
#     #          room=message['room'])
#     #     close_room(message['room'])
#     #
#     # def on_my_room_event(self, message):
#     #     session['receive_count'] = session.get('receive_count', 0) + 1
#     #     emit('my_response',
#     #          {'data': message['data'], 'count': session['receive_count']},
#     #          room=message['room'])
#     #
#     # def on_disconnect_request(self):
#     #     session['receive_count'] = session.get('receive_count', 0) + 1
#     #     emit('my_response',
#     #          {'data': 'Disconnected!', 'count': session['receive_count']})
#     #     disconnect()
#
#     def on_my_ping(self):
#         # emit('my_pong')
#         print("ping")
#
#     def on_connect(self):
#         global thread
#         with thread_lock:
#             if thread is None:
#                 thread = socketio.start_background_task(background_thread)
#         # emit('my_response', {'data': 'Connected', 'count': 0})
#
#     def on_disconnect(self):
#         print('Client disconnected', request.sid)
#
#
# socketio.on_namespace(MyNamespace('/crypto'))
#
# socketio.init_app(app)
