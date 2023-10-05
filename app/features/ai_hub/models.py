from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_json):
        # user_json['_id'] = str(user_json.get('_id'))
        self.user_json = user_json

    def get_id(self):
        object_id = self.user_json.get('_id')
        return object_id

    def get_slug(self):
        slug = self.user_json.get('slug')
        return slug

    def get_profile_name(self):
        profile_name = self.user_json.get('profile_name')
        if not profile_name:
            return None
        return str(profile_name)

    def get_profile_image(self):
        profile_image = self.user_json.get('image_url')
        if not profile_image:
            return None
        return str(profile_image)

    def is_authenticated():
        return True

    def is_active():
        return True

    def is_anonymous():
        return True
