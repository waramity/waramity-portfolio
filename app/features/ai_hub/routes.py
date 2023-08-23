from flask import (render_template, Blueprint, g, redirect,
                   request, current_app, abort, url_for, jsonify, make_response, json)

from flask_babel import _, refresh
from flask_login import login_user, logout_user, login_required, current_user

import requests
import uuid
from app import db, app, google_client, user_db
import datetime
from app.features.ai_hub.models import User

ai_hub = Blueprint('ai_hub', __name__, template_folder='templates', url_prefix='/<lang_code>/ai_hub' )

# Multiligual Start
@ai_hub.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)

@ai_hub.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')

@ai_hub.before_request
def before_request():
    if g.lang_code not in current_app.config['LANGUAGES']:
        abort(404)

# Multiligual End

@ai_hub.route('/')
def index():
    return render_template('ai_hub/index.html', title=_('waramity portfolio'))

@ai_hub.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('ai_hub.index'))

def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()

@ai_hub.route("/google-auth")
def google_auth():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = google_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email"],
    )

    return redirect(request_uri)

@ai_hub.route("/google-auth/callback")
def google_auth_callback():
    code = request.args.get("code")

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = google_client.prepare_token_request(
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

    google_client.parse_request_body_response(json.dumps(token_response.json()))
    print('kuy')

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = google_client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        social_auth_id = userinfo_response.json()["sub"]
    else:
        return "User email not available or not verified by Google.", 400

    print('nhee')
    print(user_db)
    print(user_db.profile)
    print(social_auth_id)
    print(user_db.profile.find_one({'social_auth.social_auth_id': social_auth_id}))

    user = user_db.profile.find_one({'social_auth.social_auth_id': social_auth_id})
    print('sus')

    print(user)

    if not user:

        slug = uuid.uuid4().hex[:11]
        while user_db.profile.find_one({'slug': slug}):
            slug = uuid.uuid4().hex[:11]

        user_id = 'mongo_' + uuid.uuid4().hex[:11]
        while user_db.profile.find_one({'_id': user_id}):
            user_id = 'mongo_' + uuid.uuid4().hex[:11]

        user = {
            '_id': user_id,
            'registered_on': datetime.datetime.now(),
            'slug': slug,
            'social_auth': {
                'social_auth_id': social_auth_id,
                'social_provider': 'google'
            },
            'description': '',
            'image_url': '',
            'profile_name': '',
            'total_engagement': {
                'likes': 0,
                'bookmarks': 0,
                'comments': 0,
                'followers': 0,
                'followings': 0
            }
        }

        print(user)

        # Insert the new user document into the collection
        result = user_db.profile.insert_one(user)
        user['_id'] = str(result.inserted_id)
    else:
        user['_id'] = str(user['_id'])

    user = User(user)
    login_user(user)
    return redirect(url_for('main.index'))
