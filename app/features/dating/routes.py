from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, json)

from flask_babel import _, refresh
from flask_login import login_required, current_user

import geocoder

from app.models import Location, Preferences, User
from app import db

import datetime, time
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, and_
import random

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
            return redirect(url_for('dating.app'))

    return render_template('dating/index.html', title=_('Dootua - คู่ชีวิตที่คุณตามหา'))

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
    return render_template('dating/match.html', title=_('Dootua - คู่ชีวิตที่คุณตามหา'))

@dating.route('/get-user-based-on-preferences', methods=['POST'])
@login_required
def get_user_based_on_preferences():
    # if request.method == 'POST' and request.json is not None:
    if request.method == 'POST':
        datetime_now = datetime.datetime.now()
        preferences = Preferences.query.filter_by(user_id=current_user.id).first()
        start_datetime = datetime_now - relativedelta(years=preferences.end_age)
        end_datetime = datetime_now - relativedelta(years=preferences.start_age)
        # print(current_user.preferences.showmes)
        # users = [i.serialize for i in User.query.join(User.preferences).join(User.last_location).filter(User.id!=current_user.id, User.birthday.between(start_datetime, end_datetime), User.gender_id.in_(gender.id for gender in current_user.preferences.showmes), distanceMath(current_user.last_location.latitude, float(Location.latitude), current_user.last_location.longitude, float(Location.longitude)) <= Preferences.distance).all()]
        users = [i.serialize for i in User.query.join(User.last_location).filter(User.id!=current_user.id, User.birthday.between(start_datetime, end_datetime), User.gender_id.in_(gender.id for gender in current_user.preferences.showmes), func.acos(func.sin(func.radians(current_user.last_location.latitude)) * func.sin(func.radians(Location.latitude)) + func.cos(func.radians(current_user.last_location.latitude)) * func.cos(func.radians(Location.latitude)) * func.cos(func.radians(Location.longitude) - (func.radians(current_user.last_location.longitude)))) * 6371 <= preferences.distance, User.id.not_in(like.to_user_id for like in current_user.likes)).all()]
        # users = [i.serialize for i in User.query.join(User.last_location, User.likes).filter(User.id!=current_user.id, User.birthday.between(start_datetime, end_datetime), User.gender_id.in_(gender.id for gender in current_user.preferences.showmes), func.acos(func.sin(func.radians(current_user.last_location.latitude)) * func.sin(func.radians(Location.latitude)) + func.cos(func.radians(current_user.last_location.latitude)) * func.cos(func.radians(Location.latitude)) * func.cos(func.radians(Location.longitude) - (func.radians(current_user.last_location.longitude)))) * 6371 <= preferences.distance, and_(Likes.from_user_id!=current_user.id, Likes.to_user_id!=User.id)).all()]
        # print(users)
        random.shuffle(users)
        current_user_last_location = Location.query.filter_by(user_id=current_user.id).first()
        for user in users:
            distance = haversine(current_user_last_location.latitude, current_user_last_location.longitude, user['last_location']['latitude'], user['last_location']['longitude'])
            del user['last_location']
            user['distance'] = distance

        # users = User.query.filter(User.id.in_(like.to_user_id for like in current_user.likes)).all()
        # print(users)
        # print(current_user.likes)
        # for i in User.query.all():
        #     print(i.serialize())
            # print(i)
            # print(i.to_dict(only=('id', 'given_name', 'birthday', 'gender')))
        # print(User.query.all())
        # print([i.serialize for i in User.query.all()])
        return make_response(jsonify(users), 200)
        # return jsonify(users), 201
