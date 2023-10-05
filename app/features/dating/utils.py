from app.models import Social,  Gender, Passion
from app import db

def social_generator():
    social_names = ['google', 'facebook', 'twitter', 'apple']

    for name in social_names:
        social = Social(
            name=name
        )
        db.session.add(social)

    db.session.commit()

gender_names = ['Man', 'Woman']

def gender_generator():
    for name in gender_names:
        gender = Gender(
            name=name
        )
        db.session.add(gender)

    db.session.commit()

def passion_generator():
    passion_names = ['Cycling', 'Outdoors', 'Walking', 'Cooking', 'Working out', 'Athlete', 'Craft Beer', 'Writer', 'Politics', 'Climbing', 'Foodie', 'Art', 'Karaoke', 'Yoga', 'Blogging', 'Disney', 'Surfing', 'Soccer', 'Dog lover', 'Cat lover', 'Movies', 'Swimming', 'Hiking', 'Running', 'Music', 'Fashion', 'Vlogging', 'Astrology', 'Coffee', 'Instagram', 'DIY', 'Board Games', 'Environmentalism', 'Dancing', 'Volunteering', 'Trivia', 'Reading', 'Tea', 'Language Exchange', 'Shopping', 'Wine', 'Travel']

    for name in passion_names:
        passion = Passion(
            name=name
        )
        db.session.add(passion)

    db.session.commit()
