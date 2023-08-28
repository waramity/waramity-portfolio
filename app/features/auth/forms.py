from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, SelectMultipleField, widgets, RadioField, MultipleFileField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, InputRequired, NumberRange
from flask_wtf.file import FileField, FileRequired

from flask_babel import _

import datetime

def generate_date_choices(option):
    choices = []
    if option == 'day':
        for i in range(1, 31):
            choices.append((i, i))
    elif option == 'month':
        month_names = [_('January'), _('February'), _('March'), _('April'), _('May'), _('June'), _('July'), _('August'), _('September'), _('October'), _('November'), _('December')];
        for i in range(0, 12):
            choices.append((i+1, month_names[i]))
    elif option == 'year':
        curr_dt = datetime.datetime.now()
        start_year = int(curr_dt.year-120)
        end_year = int(curr_dt.year-20)
        for i in reversed(range(start_year, end_year)):
            choices.append((i, i))
    elif option == 'start_year':
        curr_dt = datetime.datetime.now()
        start_year = curr_dt.year-120
        return start_year
    elif option == 'end_year':
        curr_dt = datetime.datetime.now()
        end_year = curr_dt.year-20
        return end_year
    return choices

def generate_gender_choices():
        choices = []
        gender_names = ['Man', 'Woman']

        for name in gender_names:
            choices.append((name, name))
        return choices

def generate_passion_choices():
        choices = []
        passion_names = ['Cycling', 'Outdoors', 'Walking', 'Cooking', 'Working out', 'Athlete', 'Craft Beer', 'Writer', 'Politics', 'Climbing', 'Foodie', 'Art', 'Karaoke', 'Yoga', 'Blogging', 'Disney', 'Surfing', 'Soccer', 'Dog lover', 'Cat lover', 'Movies', 'Swimming', 'Hiking', 'Running', 'Music', 'Fashion', 'Vlogging', 'Astrology', 'Coffee', 'Instagram', 'DIY', 'Board Games', 'Environmentalism', 'Dancing', 'Volunteering', 'Trivia', 'Reading', 'Tea', 'Language Exchange', 'Shopping', 'Wine', 'Travel']

        for name in passion_names:
            choices.append((name, name))
        return choices

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class CreateProfileForm(FlaskForm):
    given_name = StringField(_('Given name'), validators=[InputRequired(message=_('*Please enter your given name.')), Length(min=2, max=35, message=_('*Given name must be between 2-35 characters.'))])
    birth_day = SelectField(_('Day'), validators=[NumberRange(min=1, max=31, message=_('*Please select birth day.'))], coerce=int, choices=generate_date_choices('day'))
    birth_month = SelectField(_('Month'), validators=[NumberRange(min=1, max=12, message=_('*Please select birth month'))], coerce=int, choices=generate_date_choices('month'))
    birth_year = SelectField(_('Year'), validators=[NumberRange(min=generate_date_choices('start_year'), max=generate_date_choices('end_year'), message=_('*Please select birth year'))], coerce=int, choices=generate_date_choices('year'))
    gender = RadioField(_('Gender'), validators=[InputRequired(message=_('*Please select gender'))], coerce=str, choices=generate_gender_choices())
    showme = MultiCheckboxField(_('Show me to'), validators=[Length(min=1, message=_('*Please select which one you desired'))], coerce=str, choices=generate_gender_choices())
    passion = MultiCheckboxField(_('Interests'), validators=[Length(min=1, message=_('*Please select your interests'))], coerce=str, choices=generate_passion_choices())
