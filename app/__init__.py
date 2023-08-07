from flask import Flask, g, request, redirect, url_for
from flask_babel import Babel
from config import Config

from pycoingecko import CoinGeckoAPI

from threading import Lock

from flask_socketio import SocketIO, Namespace, emit

app = Flask(__name__)
babel = Babel(app)
coin_gecko = CoinGeckoAPI()

# socketio.init_app(app, manage_session=False)

app.debug = True  # Enable debug mode

app.config.from_object(Config)

from app.features.main import main as main_blueprint
app.register_blueprint(main_blueprint)

from app.features.crypto import crypto as crypto_blueprint, socketio as crypto_socket
app.register_blueprint(crypto_blueprint)

crypto_socket.init_app(app)

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
