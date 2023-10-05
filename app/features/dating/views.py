from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, session)
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_login import login_required, current_user

from app.models import Matches, Message, User

import uuid
import json
import datetime, time
from sqlalchemy import func


from app import db

socketio = SocketIO()

def random_uuid(model):
    unique_id = uuid.uuid4().hex
    while model.query.filter_by(id=unique_id).first():
        unique_id = uuid.uuid4().hex
    return unique_id

def stringifyDateTime(dateTimeObject):
    if isinstance(dateTimeObject, datetime.datetime):
        return dateTimeObject.__str__()

@socketio.on("userConnected", namespace='/dating')
@login_required
def userConnected():
    session.pop("current_chat", None)
    join_room(current_user.id)
    matches = Matches.query.filter((Matches.sender_id==current_user.id) | (Matches.recipient_id==current_user.id)).all()

    all_chats = []
    for match in matches:
        if match.sender_id == current_user.id:
            user_id = match.recipient_id
        else:
            user_id = match.sender_id

        recipient_user = User.query.filter(User.id == user_id).first()
        last_message = Message.query.filter(Message.match_id == match.id).order_by(Message.created_date.desc(), func.random()).first()
        message = None
        if last_message:
            message = {"message": last_message.message, "datetime": json.dumps(last_message.created_date, default=stringifyDateTime)}
        else:
            message = {"message": None, "datetime": None}
        if recipient_user:
            all_chats.append({'match_id': match.id, 'user_id': user_id, 'given_name': recipient_user.given_name, 'last_message': message, 'profile_image_uri': recipient_user.profile_images[0].rendered_data})

    socketio.emit("chatRooms", all_chats, room=current_user.id, namespace='/dating')

@socketio.on("changeChat", namespace='/dating')
def changeChat(user_id, match_id):
    session["current_chat"] = user_id
    messages = Message.query.filter(Message.match_id == match_id).all()
    recipient_user = User.query.filter(User.id == user_id).first()
    payload = {"recipient_id": user_id, "profile_image_uri": recipient_user.profile_images[0].rendered_data, "all_messages": []}
    for message in messages:
        message_type = "receivedMessage"
        if current_user.id == message.sender_id:
            message_type = "sentMessage"
        payload['all_messages'].append({"match_id": match_id, "message_type": message_type, "created_date": json.dumps(message.created_date, default=stringifyDateTime), "message": message.message})
    socketio.emit("displayAllMessages", payload, room=current_user.id, namespace='/dating')

@socketio.on("message", namespace='/dating')
def message(form):
    match_id = form['match_id']
    recipient_id = form['recipient_id']
    message = form['message']

    user = User.query.filter(User.id == recipient_id).first()
    if not user:
        flash("No such account exists.")
        return redirect(url_for("dating.index"))

    new_message = Message(id=random_uuid(Message), match_id=match_id, sender_id=current_user.id, message=message)
    db.session.add(new_message)
    db.session.commit()

    socketio.emit("sentMessage", {"match_id": match_id, "recipient_id": recipient_id, "sender_id": current_user.id, "message": message, "created_date": json.dumps(new_message.created_date, default=stringifyDateTime)}, room=current_user.id, namespace='/dating')
    socketio.emit("receivedMessage", {"match_id": match_id, "recipient_id": recipient_id, "sender_id": current_user.id, "message": message, "created_date": json.dumps(new_message.created_date, default=stringifyDateTime), "firstName": current_user.given_name}, room=recipient_id, namespace='/dating')
