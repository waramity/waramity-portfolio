from flask import Blueprint, render_template, redirect, url_for, request, flash, g, current_app
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
    return redirect(url_for('main.index'))

def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()

@auth.route("/google-auth")
def google_auth():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email"],
    )
    return redirect(request_uri)

@auth.route("/google-auth/callback")
def google_auth_callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
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

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        social_auth_id = userinfo_response.json()["sub"]
    else:
        return "User email not available or not verified by Google.", 400


    # Create a user in your db with the information provided
    # by Google
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

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for('main.index'))

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
        # birthday_datetime = datetime.datetime(year=int(birth_year), month=int(birth_month), day=int(birth_day))
        birthday_datetime = datetime.datetime.strptime(birthday_str, '%m/%d/%Y')

        gender_name = form.gender.data
        gender_id = Gender.query.filter_by(name=gender_name).first().id
        #
        # sexual_orientation_names = form.sexual_orientation.data
        # sexual_orientations = []
        # for name in sexual_orientation_names:
        #     sexual_orientations.append(SexualOrientation.query.filter_by(name=name).first())

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
                    flash(_('*กรุณาอัพโหลดรูปถ่าย'))
                    return redirect(url_for('auth.create_profile'))
                continue

        if file_count == 0:
            flash(_('*กรุณาอัพโหลดรูปถ่าย'))
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
        # current_user.sexual_orientations = sexual_orientations
        current_user.preferences = preferences
        current_user.passions = passions
        current_user.profile_images = profile_images
        current_user.location = location

        db.session.commit()

        return redirect(url_for('auth.geolocation'))

    genders = Gender.query.all()
    passions = Passion.query.all()
    return render_template('auth/create-profile.html', title=_('สร้างโปรไฟล์ - Dootua'), genders=genders, passions=passions, form=form)
    # return render_template('auth/create-profile.html', title=_('สร้างโปรไฟล์ - Dootua'), genders=genders, sexual_orientations=sexual_orientations, passions=passions, form=form)

#
# @auth.route("/create-profile", methods=['POST'])
# @login_required
# def create_profile_post():
#     given_name = request.form.get('given_name')
#
#     birth_day = request.form.get('birth_day')
#     birth_month = request.form.get('birth_month')
#     birth_year = request.form.get('birth_year')
#     birthday_datetime = datetime.datetime(year=int(birth_year), month=int(birth_month), day=int(birth_day))
#
#     gender_id = request.form.get('gender_id')
#
#     sexual_orientation_ids = request.form.getlist('sexual-orientation')
#     sexual_orientations = []
#     for id in sexual_orientation_ids:
#         sexual_orientations.append(SexualOrientation.query.filter_by(id=id).first())
#
#     showme_gender_ids = request.form.getlist('showme')
#     showme_genders = []
#     for id in showme_gender_ids:
#         showme_genders.append(Gender.query.filter_by(id=id).first())
#
#     passion_ids = request.form.getlist('passion')
#     passions = []
#     for id in passion_ids:
#         passions.append(Passion.query.filter_by(id=id).first())
#
#     profile_image_files = request.files.getlist("profile_image")
#     profile_images = []
#
#     for file in profile_image_files:
#         if file.filename == "":
#             continue
#         data = file.read()
#         render_file = render_picture(data)
#
#         profile_image = ProfileImage(name=file.filename, data=data, rendered_data=render_file)
#         profile_images.append(profile_image)
#         db.session.add(profile_image)
#
#     current_user.given_name = given_name
#     current_user.birthday = birthday_datetime
#     current_user.gender = gender_id
#     current_user.sexual_orientations = sexual_orientations
#     current_user.showme_genders = showme_genders
#     current_user.passions = passions
#     current_user.profile_images = profile_images
#
#     db.session.commit()
#
#     return redirect(url_for('auth.profile'))

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
