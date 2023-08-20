from flask_login import UserMixin
from . import db
import datetime, time, pytz


# user_sexual_orientation = db.Table('user_sexual_orientation',
#                     db.Column('user_id', db.String(100), db.ForeignKey('user.id')),
#                     db.Column('sexual_orientation_id', db.Integer, db.ForeignKey('sexual_orientation.id'))
#                     )

user_passion = db.Table('user_passion',
                    db.Column('user_id', db.String(100), db.ForeignKey('user.id')),
                    db.Column('passion_id', db.Integer, db.ForeignKey('passion.id'))
                    )

# user_like = db.Table('user_like',
#                     db.Column('user_id', db.String(100), db.ForeignKey('user.id')),
#                     db.Column('like_id', db.String(100), db.ForeignKey('likes.id'))
#                     )

user_match = db.Table('user_match',
                    db.Column('user_id', db.String(100), db.ForeignKey('user.id')),
                    db.Column('match_id', db.String(100), db.ForeignKey('matches.id'))
                    )

showme_gender = db.Table('showme_gender',
                    db.Column('preferences_id', db.Integer, db.ForeignKey('preferences.id')),
                    db.Column('gender_id', db.Integer, db.ForeignKey('gender.id'))
                    )

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    # serialize_only = ('id', 'given_name', 'birthday', 'gender.name')
    # serialize_rules = ('-user_social')
    id = db.Column(db.String(32), primary_key=True, unique=True)
    given_name = db.Column(db.String(100))
    birthday = db.Column(db.DateTime)
    registered_on = db.Column(db.DateTime, nullable=False)
    user_social = db.relationship('UserSocial', uselist=False, backref="user_social")
    gender_id = db.Column(db.Integer, db.ForeignKey('gender.id'))
    # gender = db.relationship('Gender', uselist=False, backref="gender")
    # sexual_orientations = db.relationship('SexualOrientation', secondary=user_sexual_orientation, backref='user_sexual_orientations')
    # showmes = db.relationship('Gender', secondary=showme_gender, backref='showme_genders')
    passions = db.relationship('Passion', secondary=user_passion, backref='user_passions')
    profile_images = db.relationship('ProfileImage', backref='user_profile_image')
    geolocation_permission = db.Column(db.Boolean, default=False)
    # last_location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    preferences = db.relationship('Preferences', uselist=False, backref="user_preferences")
    last_location = db.relationship('Location', uselist=False, backref="last_location")
    likes = db.relationship('Likes', primaryjoin="User.id==Likes.from_user_id")
    # likes = db.relationship('Likes', secondary=user_like, backref="user_like")
    matches = db.relationship('Matches', secondary=user_match, backref="user_match")
    # matches = db.relationship('Matches', backref="user_matches")

    def __repr__(self):
        return f"User('{self.id}', '{self.given_name}', '{self.birthday}', '{self.gender_id}', '{self.passions}', '{self.profile_images}')"

    @property
    def serialize(self):
       """Return object data in easily serializable format"""
       return {
           'id': self.id,
           'given_name': self.given_name,
           'birthday': int(time.mktime(self.birthday.timetuple())) * 1000,
           'gender': self.gender_id,
           'passions': self.serialize_passions,
           'profile_images': self.serialize_profile_images,
           'last_location': self.serialize_last_location,
           # 'passions': self.serialize_passions,
           # 'profile_images': self.serialize_profile_images,
           # 'passions': self.serialize_passions
           # 'last_location': self.serialize_last_location
       }

    # @property
    # def serialize_gender(self):
    #    return [ item.name for item in self.gender]

    @property
    def serialize_passions(self):
       return [ item.name for item in self.passions]

    @property
    def serialize_profile_images(self):
       return [ {'name': item.name, 'rendered_data': item.rendered_data} for item in self.profile_images]

    @property
    def serialize_last_location(self):
        location = Location.query.filter_by(user_id=self.id).first()
        return {'latitude': location.latitude, 'longitude': location.longitude}
       # return  {'latitude': self.last_location.latitude, 'longitude': self.last_location.longitude}

class UserSocial(db.Model):
    __tablename__ = 'user_social'
    social_auth_id = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.String(32), db.ForeignKey('user.id'))
    social_id = db.Column(db.Integer, db.ForeignKey('social.id'))

class Social(db.Model):
    __tablename__ = 'social'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # user_social = db.relationship('UserSocial', backref='social')

class Gender(db.Model):
    __tablename__ = 'gender'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # user_id = db.Column(db.String(100), db.ForeignKey('user.id'))
    # user = db.relationship('User', backref='user_gender')

    def __repr__(self):
        return f"Gender('{self.id}', '{self.name}')"

# class SexualOrientation(db.Model):
#     __tablename__ = 'sexual_orientation'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)

class Passion(db.Model):
    __tablename__ = 'passion'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class ProfileImage(db.Model):
    __tablename__ = 'profile_image'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False) #Actual data, needed for Download
    rendered_data = db.Column(db.Text, nullable=False)#Data to render the pic in browser
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(pytz.timezone('Asia/Bangkok')))
    user_id = db.Column(db.String(32), db.ForeignKey('user.id'))

class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    user_id = db.Column(db.String(32), db.ForeignKey('user.id'))

    def __repr__(self):
        return f"Location('{self.id}', '{self.latitude}', '{self.longitude}')"

class Preferences(db.Model):
    __tablename__ = 'preferences'
    id = db.Column(db.Integer, primary_key=True)
    start_age = db.Column(db.Integer, default=20)
    end_age = db.Column(db.Integer, default=65)
    distance = db.Column(db.Integer, default=700)
    # showmes = db.Column(db.Integer)
    showmes = db.relationship('Gender', secondary=showme_gender, backref='showme_genders')
    user_id = db.Column(db.String(32), db.ForeignKey('user.id'))

    def __repr__(self):
        return f"Preferences('{self.id}', '{self.start_age}', '{self.end_age}', '{self.distance}', '{self.showmes}')"

    @property
    def serialize(self):
       """Return object data in easily serializable format"""
       return {
           'start_age': self.start_age,
           'end_age': self.end_age,
           'distance': self.distance,
           'showmes': self.serialize_showmes,
       }

    @property
    def serialize_showmes(self):
       return [ item.id for item in self.showmes]

class Likes(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.String(32), primary_key=True)
    from_user_id = db.Column(db.String(32), db.ForeignKey('user.id'))
    to_user_id = db.Column(db.String(32), db.ForeignKey('user.id'))
    like = db.Column(db.Boolean, default=None)
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(pytz.timezone('Asia/Bangkok')))

    def __repr__(self):
        return f"Likes('{self.id}', '{self.from_user_id}', '{self.to_user_id}', '{self.like}', '{self.date}')"

class Matches(db.Model):
    __tablename__ = 'matches'
    id = db.Column(db.String(32), primary_key=True)
    sender_id = db.Column(db.String(32), db.ForeignKey('user.id'))
    recipient_id = db.Column(db.String(32), db.ForeignKey('user.id'))
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(pytz.timezone('Asia/Bangkok')))

    def __repr__(self):
        return f"Matches('{self.id}', '{self.sender_id}', '{self.recipient_id}', '{self.created_date}')"

    # @property
    # def serialize(self):
    #    """Return object data in easily serializable format"""
    #    user = User.query.filter_by(id=self.user_id).first()
    #    return {
    #        'id': user.recipient_id,
    #        'given_name': user.given_name,
    #        'profile_image_uri': user.profile_images[0].rendered_data,
    #        'updated_date': int(time.mktime(self.updated_date.timetuple())) * 1000
    #    }

class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.String(32), primary_key=True)
    message = db.Column(db.Text)
    sender_id = db.Column(db.String(32), db.ForeignKey('user.id'))
    match_id = db.Column(db.String(32), db.ForeignKey('matches.id'))
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(pytz.timezone('Asia/Bangkok')))
    is_read = db.Column(db.Boolean, default=False)
    parent_message_id = db.Column(db.String(32), db.ForeignKey('message.id'))
