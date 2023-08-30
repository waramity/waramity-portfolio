from app.features.management.scheduler import sync_copies

from app.models import PromptCategory, PromptSubCategory, PromptDetailCategory, Prompt, PromptSet, ModelCard
from app import db
import uuid

def destroy_db():
    db.drop_all()

def create_db():
    db.create_all()

def add_prompt_category(eng_name, thai_name):

    unique_id = uuid.uuid4().hex
    while PromptCategory.query.filter_by(id=unique_id).first():
        unique_id = uuid.uuid4().hex

    prompt_category = PromptCategory(
        id=unique_id,
        eng_name=eng_name,
        thai_name=thai_name
    )

    db.session.add(prompt_category)
    db.session.commit()

def add_prompt_sub_category(eng_name, thai_name, category_eng_name):

    unique_id = uuid.uuid4().hex
    while PromptSubCategory.query.filter_by(id=unique_id).first():
        unique_id = uuid.uuid4().hex

    prompt_category = PromptCategory.query.filter_by(eng_name=category_eng_name).first()

    prompt_sub_category = PromptSubCategory(
        id=unique_id,
        eng_name=eng_name,
        thai_name=thai_name,
        prompt_category_id=prompt_category.id
    )

    # prompt_category.prompt_sub_categories.append(prompt_sub_category)

    db.session.add(prompt_sub_category)
    db.session.commit()

def add_prompt_detail_category(eng_name, thai_name, sub_category_eng_name, category_eng_name):

    unique_id = uuid.uuid4().hex
    while PromptDetailCategory.query.filter_by(id=unique_id).first():
        unique_id = uuid.uuid4().hex

    prompt_category = PromptCategory.query.filter_by(eng_name=category_eng_name).first()
    prompt_sub_category = PromptSubCategory.query.filter_by(eng_name=sub_category_eng_name, prompt_category_id=prompt_category.id).first()

    prompt_detail_category = PromptDetailCategory(
        id=unique_id,
        eng_name=eng_name,
        thai_name=thai_name,
        prompt_sub_category_id=prompt_sub_category.id
    )

    # prompt_sub_category.prompt_detail_categories.append(prompt_detail_category)

    db.session.add(prompt_detail_category)
    db.session.commit()

def add_prompt(eng_name, thai_name, sub_category_eng_name, detail_category_eng_name, category_eng_name):

    unique_id = uuid.uuid4().hex
    while Prompt.query.filter_by(id=unique_id).first():
        unique_id = uuid.uuid4().hex

    prompt_category = PromptCategory.query.filter_by(eng_name=category_eng_name).first()
    prompt_sub_category = PromptSubCategory.query.filter_by(eng_name=sub_category_eng_name, prompt_category_id=prompt_category.id).first()
    prompt_detail_category = PromptDetailCategory.query.filter_by(eng_name=detail_category_eng_name, prompt_sub_category_id=prompt_sub_category.id).first()

    prompt = Prompt(
        id=unique_id,
        eng_name=eng_name,
        thai_name=thai_name,
        # prompt_detail_category_id=prompt_detail_category.id
    )

    prompt_detail_category.prompts.append(prompt)

    db.session.add(prompt)
    db.session.commit()

def add_prompt_set(title, prompt_eng_names, prompt_category_eng_names):

    unique_id = uuid.uuid4().hex
    while PromptSet.query.filter_by(id=unique_id).first():
        unique_id = uuid.uuid4().hex

    prompt_categories = []
    for eng_name in prompt_category_eng_names:
        prompt_categories.append(PromptCategory.query.filter_by(eng_name=eng_name).first())

    prompt_set = PromptSet(
        id=unique_id,
        title=title,
        # prompt_set_category_id=prompt_set_category.id
        prompt_categories=prompt_categories
    )

    for prompt_eng_name in prompt_eng_names:
        prompt = Prompt.query.filter_by(eng_name=prompt_eng_name).first()
        prompt_set.prompts.append(prompt)

    db.session.add(prompt_set)
    db.session.commit()

def add_model_card(title, short_description):

    unique_id = uuid.uuid4().hex
    while ModelCard.query.filter_by(id=unique_id).first():
        unique_id = uuid.uuid4().hex

    model_card = ModelCard(
        id=unique_id,
        title=title,
        short_description=short_description
    )

    db.session.add(model_card)
    db.session.commit()
