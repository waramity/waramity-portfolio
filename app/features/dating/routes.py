from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, json, session)

from flask_babel import _, refresh
from flask_login import login_required, current_user, logout_user

import geocoder

from app.models import Location, Preferences, User, Gender, Likes, Matches
from app import db

import datetime, time
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, and_
import random
from math import radians, cos, sin, asin, sqrt

import uuid


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

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees)
    """

    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r


@dating.route('/dating')
def index():

    if session['platform'] != 'dating':
        logout_user()
    if current_user.is_authenticated:
        if current_user.given_name is None:
            return redirect(url_for('auth.create_profile'))
        elif current_user.geolocation_permission == False or current_user.geolocation_permission == None:
            return redirect(url_for('auth.geolocation'))
        else:
            return redirect(url_for('dating.app'))

    return render_template('dating/index.html', title=_('Life partner you are looking for'))

def get_geolocation():
    ip = geocoder.ip('me')
    location = Location.query.filter_by(user_id=current_user.id).first()
    location.latitude = float(ip.lat)
    location.longitude = float(ip.lng)
    current_user.last_location = location
    db.session.commit()

@dating.route('/dating/app')
@login_required
def app():
    get_geolocation()
    return render_template('dating/match.html', title=_('Life partner you are looking for'))

@dating.route('/get-user-based-on-preferences', methods=['POST'])
@login_required
def get_user_based_on_preferences():
    if request.method == 'POST':
        datetime_now = datetime.datetime.now()
        preferences = Preferences.query.filter_by(user_id=current_user.id).first()
        start_datetime = datetime_now - relativedelta(years=preferences.end_age)
        end_datetime = datetime_now - relativedelta(years=preferences.start_age)
        users = [i.serialize for i in User.query.join(User.last_location).filter(User.id!=current_user.id, User.birthday.between(start_datetime, end_datetime), User.gender_id.in_(gender.id for gender in current_user.preferences.showmes), func.acos(func.sin(func.radians(current_user.last_location.latitude)) * func.sin(func.radians(Location.latitude)) + func.cos(func.radians(current_user.last_location.latitude)) * func.cos(func.radians(Location.latitude)) * func.cos(func.radians(Location.longitude) - (func.radians(current_user.last_location.longitude)))) * 6371 <= preferences.distance, User.id.not_in(like.to_user_id for like in current_user.likes)).all()]
        random.shuffle(users)
        current_user_last_location = Location.query.filter_by(user_id=current_user.id).first()
        for user in users:
            distance = haversine(current_user_last_location.latitude, current_user_last_location.longitude, user['last_location']['latitude'], user['last_location']['longitude'])
            del user['last_location']
            user['distance'] = distance

        return make_response(jsonify(users), 200)

@dating.route('/get-user-preferences', methods=['POST'])
@login_required
def get_user_preferences():
    if request.method == 'POST':
        preferences = Preferences.query.filter_by(user_id=current_user.id).first().serialize
        return make_response(jsonify(preferences), 200)

@dating.route('/save-changes-preferences', methods=['POST'])
@login_required
def save_changes_preferences():

    if request.method == 'POST' and request.json is not None:
        preferences = Preferences.query.filter_by(user_id=current_user.id).first()
        if request.json['start_age'] < 20 or request.json['start_age'] > 65:
            request.json['start_age'] = 20
        if request.json['end_age'] < 20 or request.json['end_age'] > 65:
            request.json['end_age'] = 65
        if request.json['distance'] < 10 or request.json['distance'] > 700:
            request.json['distance'] = 700

        showmes = []
        for gender_id in request.json['showmes']:
            if isinstance(gender_id,int) and gender_id > 0 and gender_id < 3:
                showmes.append(Gender.query.filter_by(id=gender_id).first())
            else:
                continue

        if showmes == []:
            showmes.append(Gender.query.filter_by(id=1).first())

        preferences.start_age = request.json['start_age']
        preferences.end_age = request.json['end_age']
        preferences.distance = request.json['distance']
        preferences.showmes = showmes

        db.session.commit()

        preferences = Preferences.query.filter_by(user_id=current_user.id).first().serialize
        return make_response(jsonify(preferences), 200)

def random_uuid(model):
    unique_id = uuid.uuid4().hex
    while model.query.filter_by(id=unique_id).first():
        unique_id = uuid.uuid4().hex
    return unique_id

@dating.route('/update-like', methods=['POST'])
@login_required
def update_like():
    if request.method == 'POST' and request.json is not None:
        result = {}
        from_user_like = Likes.query.filter(Likes.from_user_id==str(current_user.id), Likes.to_user_id==str(request.json["res_user_id"])).first()
        if from_user_like is None:
            from_user_like = Likes(id=random_uuid(Likes), from_user_id=current_user.id, to_user_id=str(request.json["res_user_id"]), like=bool(request.json["like"]))
            current_user.likes.append(from_user_like)
            db.session.add(from_user_like)
            if from_user_like.like is True:
                to_user_like = Likes.query.filter(Likes.from_user_id==str(request.json["res_user_id"]), Likes.to_user_id==current_user.id, Likes.like==True).first()
                if to_user_like is not None:
                    match = Matches(id=random_uuid(Matches), sender_id=current_user.id, recipient_id=str(request.json["res_user_id"]))
                    db.session.add(match)
                    current_user.matches.append(match)
                    to_user = User.query.filter_by(id=str(request.json["res_user_id"])).first()
                    to_user.matches.append(match)
                    db.session.commit()
                    result['result'] = 'Match'
                    result.update({'match_id': match.id, 'user_id': to_user.id, 'given_name': to_user.given_name, 'profile_image_uri': to_user.profile_images[0].rendered_data, 'last_message': {"message": None, "datetime": None}})
                    return make_response(jsonify(result), 200)
            db.session.commit()
            result["result"] = "Like"
            return make_response(jsonify(result), 200)

@dating.route('/update-dislike', methods=['POST'])
@login_required
def update_dislike():
    if request.method == 'POST' and request.json is not None:
        result = {}
        from_user_like = Likes.query.filter(Likes.from_user_id==str(current_user.id), Likes.to_user_id==str(request.json["res_user_id"])).first()
        if from_user_like is None:
            from_user_like = Likes(id=random_uuid(Likes), from_user_id=current_user.id, to_user_id=str(request.json["res_user_id"]), like=bool(request.json["like"]))
            if from_user_like.like is False:
                current_user.likes.append(from_user_like)
                db.session.add(from_user_like)
                db.session.commit()
                result["result"] = "Dislike"
                return make_response(jsonify(result), 200)
