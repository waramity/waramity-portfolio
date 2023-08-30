from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    display_name = db.Column(db.String(100))

class PromptCategory(db.Model):
    __tablename__ = 'prompt_category'
    id = db.Column(db.String(32), primary_key=True)
    eng_name = db.Column(db.String(100), nullable=False)
    thai_name = db.Column(db.String(100), nullable=False)
    prompt_sub_categories = db.relationship('PromptSubCategory', backref='prompt_category_prompt_sub_category')

    def __repr__(self):
        return f"PromptCategory('{self.id}', '{self.eng_name}', '{self.thai_name}', '{self.prompt_sub_categories}')"

    @property
    def serialize(self):
       return {
           'id': self.id,
           'eng_name': self.eng_name,
           'thai_name': self.thai_name,
           'sub_categories': self.serialize_prompt_sub_categories,
       }

    @property
    def serialize_prompt_sub_categories(self):
       return [ {'id': item.id, 'eng_name': item.eng_name, 'thai_name': item.thai_name, 'length': len(item.prompt_detail_categories)} for item in self.prompt_sub_categories]

class PromptSubCategory(db.Model):
    __tablename__ = 'prompt_sub_category'
    id = db.Column(db.String(32), primary_key=True)
    eng_name = db.Column(db.String(100), nullable=False)
    thai_name = db.Column(db.String(100), nullable=False)
    prompt_category_id = db.Column(db.Integer, db.ForeignKey('prompt_category.id'))
    prompt_detail_categories = db.relationship('PromptDetailCategory', backref='prompt_sub_category')

    def __repr__(self):
        return f"PromptSubCategory('{self.id}', '{self.eng_name}', '{self.thai_name}', '{self.prompt_category_id}', '{self.prompt_detail_category}')"

    @property
    def serialize(self):
       return {
           'id': self.id,
           'eng_name': self.eng_name,
           'thai_name': self.thai_name,
           'prompt_detail_categories': self.serialize_detail_categories,
       }

    @property
    def serialize_detail_categories(self):
       return [ item.serialize for item in self.prompt_detail_categories]

prompt_detail_category_prompt = db.Table('prompt_detail_category_prompt',
                    db.Column('prompt_detail_category_id', db.Integer, db.ForeignKey('prompt_detail_category.id')),
                    db.Column('prompt_id', db.Integer, db.ForeignKey('prompt.id'))
                    )

class PromptDetailCategory(db.Model):
    __tablename__ = 'prompt_detail_category'
    id = db.Column(db.String(32), primary_key=True)
    eng_name = db.Column(db.String(100), nullable=False)
    thai_name = db.Column(db.String(100), nullable=False)
    prompt_sub_category_id = db.Column(db.Integer, db.ForeignKey('prompt_sub_category.id'))
    prompts = db.relationship('Prompt', secondary=prompt_detail_category_prompt, backref='prompt_detail_categories')

    def __repr__(self):
        return f"PromptDetailCategory('{self.id}', '{self.eng_name}', '{self.thai_name}')"

    @property
    def serialize(self):
       serialize_prompts = self.serialize_prompts
       return {
           'id': self.id,
           'eng_name': self.eng_name,
           'thai_name': self.thai_name,
           'prompts': serialize_prompts,
           'length': len(serialize_prompts),
       }

    @property
    def serialize_prompts(self):
       return [ {'id': item.id, 'eng_name': item.eng_name, 'thai_name': item.thai_name, 'copies': item.copies} for item in self.prompts]

class Prompt(db.Model):
    __tablename__ = 'prompt'
    id = db.Column(db.String(32), primary_key=True)
    eng_name = db.Column(db.String(100), nullable=False)
    thai_name = db.Column(db.String(100), nullable=False)
    copies = db.Column(db.Integer, default=0)
    # prompt_detail_category_id = db.Column(db.Integer, db.ForeignKey('prompt_detail_category.id'))

    @property
    def serialize(self):
       return {
           'id': self.id,
           'eng_name': self.eng_name,
           'thai_name': self.thai_name,
           'copies': self.copies,
       }

prompt_set_prompt = db.Table('prompt_set_prompt',
                    db.Column('prompt_set_id', db.Integer, db.ForeignKey('prompt_set.id')),
                    db.Column('prompt_id', db.Integer, db.ForeignKey('prompt.id'))
                    )

prompt_set_prompt_category = db.Table('prompt_set_prompt_category',
                    db.Column('prompt_set_id', db.Integer, db.ForeignKey('prompt_set.id')),
                    db.Column('prompt_category_id', db.Integer, db.ForeignKey('prompt_category.id'))
                    )

class PromptSet(db.Model):
    __tablename__ = 'prompt_set'
    id = db.Column(db.String(32), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    copies = db.Column(db.Integer, default=0)
    prompts = db.relationship('Prompt', secondary=prompt_set_prompt, backref='prompt_set_prompts')
    prompt_categories = db.relationship('PromptCategory', secondary=prompt_set_prompt_category, backref='prompt_set_prompt_categories')
    # prompt_set_category_id = db.Column(db.Integer, db.ForeignKey('prompt_set_category.id'))

    def __repr__(self):
        return f"PromptSet('{self.id}', '{self.title}', '{self.copies}', '{self.prompts}')"

    @property
    def serialize(self):
       serialize_prompts = self.serialize_prompts
       serialize_prompt_categories = self.serialize_prompt_categories
       return {
           'id': self.id,
           'title': self.title,
           'copies': self.copies,
           'prompts': serialize_prompts,
           'prompt_categories': serialize_prompt_categories,
           'length': len(serialize_prompts),
       }

    @property
    def serialize_prompts(self):
       return [ {'id': item.id, 'eng_name': item.eng_name, 'thai_name': item.thai_name, 'copies': item.copies} for item in self.prompts]

    @property
    def serialize_prompt_categories(self):
       return [ {'id': item.id, 'eng_name': item.eng_name} for item in self.prompt_categories]

model_card_model_file_type = db.Table('model_card_model_file_type',
                    db.Column('model_card_id', db.Integer, db.ForeignKey('model_card.id')),
                    db.Column('model_file_type_id', db.Integer, db.ForeignKey('model_file_type.id'))
                    )

model_card_model_collection = db.Table('model_card_model_collection',
                    db.Column('model_card_id', db.Integer, db.ForeignKey('model_card.id')),
                    db.Column('model_collection_id', db.Integer, db.ForeignKey('model_collection.id'))
                    )

class ModelFileType(db.Model):
    __tablename__ = 'model_file_type'
    id = db.Column(db.String(32), primary_key=True)
    title = db.Column(db.String(100), nullable=False)

class ModelCollection(db.Model):
    __tablename__ = 'model_collection'
    id = db.Column(db.String(32), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(150), nullable=False)

class ModelImage(db.Model):
    __tablename__ = 'image'
    id = db.Column(db.String(32), primary_key=True)
    model_card_id = db.Column(db.Integer, db.ForeignKey('model_card.id'))

class ModelCard(db.Model):
    __tablename__ = 'model_card'
    id = db.Column(db.String(32), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    short_description = db.Column(db.String(150), nullable=False)
    downloads = db.Column(db.Integer, default=0)
    images = db.relationship('ModelImage', backref="model_card_model_images")
    file_types = db.relationship('ModelFileType', secondary=model_card_model_file_type, backref='model_card_model_file_types')
    collections = db.relationship('ModelCollection', secondary=model_card_model_collection, backref='model_card_model_collections')
    # description = db.Column(db.Text, nullable=False)
    # model_path = db.Column(db.URLType, nullable=False)
    # vae_path = db.Column(db.URLType)

    @property
    def serialize(self):
       return {
           'id': self.id,
           'title': self.title,
           'short_description': self.short_description,
       }
