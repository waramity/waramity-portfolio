from flask_socketio import SocketIO

# def ping_in_intervals():
#     while True:
#         socketio.sleep(10)
#         socketio.emit('ping')
#

socketio = SocketIO()


# thread = socketio.start_background_task(ping_in_intervals)
@socketio.on('connect', namespace='/crypto')
def on_connect():
    print('Client connected to crypto page')

@socketio.on('disconnect', namespace='/crypto')
def on_disconnect():
    print('Client disconnected from crypto page')

@socketio.on('custom_event', namespace='/crypto')
def on_custom_event(data):
    print('Custom event received:', data)

@socketio.on('my_ping', namespace='/crypto')
def on_my_ping():
    print('Received ping from client')


# Schedule the trigger_tick_update function to run every 5 seconds
