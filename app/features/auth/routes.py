from flask import Blueprint, render_template, redirect, url_for, request, flash, g, current_app, session
from flask_babel import _
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, UserSocial, Social, Gender, Passion, ProfileImage, Preferences, Location
from app import db, app, client
import datetime
import requests
import json
import uuid
import base64
import pytz
from .forms import CreateProfileForm
from werkzeug.datastructures import CombinedMultiDict

auth = Blueprint('auth', __name__, template_folder='templates', url_prefix='/<lang_code>')

# Multiligual Start
@auth.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)

@auth.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')

@auth.before_request
def before_request():
    if g.lang_code not in current_app.config['LANGUAGES']:
        adapter = app.url_map.bind('')
        try:
            endpoint, args = adapter.match(
                '/en' + request.full_path.rstrip('/ ?'))
            return redirect(url_for(endpoint, **args), 301)
        except:
            abort(404)

    dfl = request.url_rule.defaults
    if 'lang_code' in dfl:
        if dfl['lang_code'] != request.full_path.split('/')[1]:
            abort(404)
# Multiligual End

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session['platform'] = 'none'
    return redirect(url_for('dating.index'))

def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()

@auth.route("/google-auth")
def google_auth():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email"],
    )
    return redirect(request_uri)

@auth.route("/google-auth/callback")
def google_auth_callback():
    code = request.args.get("code")

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET']),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        social_auth_id = userinfo_response.json()["sub"]
    else:
        return "User email not available or not verified by Google.", 400

    user_social = UserSocial.query.filter_by(social_auth_id=social_auth_id).first()
    if not user_social:
        unique_id = uuid.uuid4().hex
        while User.query.filter_by(id=unique_id).first():
            unique_id = uuid.uuid4().hex

        user_social = UserSocial(
            social_auth_id=social_auth_id,
            social_id=Social.query.filter_by(name='google').first().id,
            user_id=unique_id
        )

        user = User(
            id=unique_id,
            registered_on=datetime.datetime.now(pytz.timezone('Asia/Bangkok')),
            user_social=user_social
        )

        db.session.add(user)
        db.session.commit()
    else:
        user = User.query.filter_by(id=user_social.user_id).first()

    login_user(user)

    session['platform'] = 'dating'

    return redirect(url_for('dating.index'))

def render_picture(data):
    render_pic = base64.b64encode(data).decode('ascii')
    return render_pic

@auth.route("/create-profile", methods=['GET', 'POST'])
@login_required
def create_profile():
    form = CreateProfileForm(CombinedMultiDict((request.files, request.form)))
    if request.method == 'POST' and form.validate_on_submit():

        given_name = form.given_name.data

        birth_day = form.birth_day.data
        birth_month = form.birth_month.data
        birth_year = form.birth_year.data
        birthday_str = str(birth_month) + "/" + str(birth_day) + "/" + str(birth_year)
        birthday_datetime = datetime.datetime.strptime(birthday_str, '%m/%d/%Y')

        gender_name = form.gender.data
        gender_id = Gender.query.filter_by(name=gender_name).first().id

        showme_names = form.showme.data
        showmes = []
        for name in showme_names:
            showmes.append(Gender.query.filter_by(name=name).first())

        passion_names = form.passion.data
        passions = []
        for name in passion_names:
            passions.append(Passion.query.filter_by(name=name).first())

        profile_image_files = request.files.getlist("profile_image")
        profile_images = []
        file_count = 0

        for file in profile_image_files:
            if file.filename != "":
                file_count += 1
                if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) == False:
                    flash(_('*Please upload a photo.'))
                    return redirect(url_for('auth.create_profile'))
                continue

        if file_count == 0:
            flash(_('*Please upload a photo.'))
            return redirect(url_for('auth.create_profile'))

        for file in profile_image_files:
            if file.filename != "":
                data = file.read()
                render_file = render_picture(data)

                profile_image = ProfileImage(name=file.filename, data=data, rendered_data=render_file, user_id=current_user.id)
                profile_images.append(profile_image)
                db.session.add(profile_image)

        preferences = Preferences(
            user_id=current_user.id,
            showmes=showmes
        )
        db.session.add(preferences)

        location = Location(
            user_id=current_user.id
        )
        db.session.add(location)

        current_user.given_name = given_name
        current_user.birthday = birthday_datetime
        current_user.gender_id = gender_id
        current_user.preferences = preferences
        current_user.passions = passions
        current_user.profile_images = profile_images
        current_user.location = location

        db.session.commit()

        return redirect(url_for('auth.geolocation'))

    genders = Gender.query.all()
    passions = Passion.query.all()
    return render_template('auth/create-profile.html', title=_('Create profile'), genders=genders, passions=passions, form=form)

@auth.route('/profile')
@login_required
def profile():
    if current_user.is_authenticated:
        return render_template('auth/profile.html')

    return redirect(url_for("dating.index"))

@auth.route('/geolocation', methods=['GET', 'POST'])
@login_required
def geolocation():
    if request.method == 'POST' and request.json['geolocation_permission'] is not None:
        current_user.geolocation_permission = request.json['geolocation_permission']
        db.session.commit()
        return redirect(url_for('dating.app'))
    else:
        return render_template('auth/geolocation.html')
