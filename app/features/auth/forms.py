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
        month_names = [_('มกราคม'), _('กุมภาพันธ์'), _('มีนาคม'), _('เมษายน'), _('พฤษภาคม'), _('มิถุนายน'), _('กรกฎาคม'), _('สิงหาคม'), _('กันยายน'), _('ตุลาคม'), _('พฤศจิกายน'), _('ธันวาคม')];
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
        # gender_names = ['Man', 'Woman', 'Agender', 'Androgyne', 'Androgynous', 'Bigender', 'Female to male', 'Gender fluid', 'Gender nonconforming', 'Gender questioning', 'Gender variant', 'Genderqueer', 'Male to female', 'Trans', 'Trans man', 'Trans person', 'Trans woman', 'Transfeminine', 'Transgender' , 'Transgender female', 'Transgender male', 'Transgender man', 'Transgender person', 'Transgender woman', 'Transmasculine', 'Transsexual', 'Transsexual female', 'Transsexual male', 'Transsexual man', 'Transsexual person', 'Transsexual woman', 'Two-spirit', 'Neither', 'Neutrois', 'Non-binary', 'Other', 'Pangender']
        gender_names = ['Man', 'Woman']

        for name in gender_names:
            choices.append((name, name))
        return choices

# def generate_sexual_orientation_choices():
#         choices = []
#         sexual_orientation_names = ['Straight', 'Gay', 'Lesbian', 'Bisexual', 'Asexual', 'Demisexual', 'Pansexual', 'Queer', 'Questioning']
#
#         for name in sexual_orientation_names:
#             choices.append((name, name))
#         return choices

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
    given_name = StringField(_('ชื่อต้น'), validators=[InputRequired(message=_('*กรุณากรอกชื่อต้น')), Length(min=2, max=35, message=_('*ชื่อต้นต้องมี 2-35 ตัวอักษร'))])
    birth_day = SelectField(_('วันเกิด'), validators=[NumberRange(min=1, max=31, message=_('*กรุณาเลือกวันเกิด'))], coerce=int, choices=generate_date_choices('day'))
    birth_month = SelectField(_('เดือนเกิด'), validators=[NumberRange(min=1, max=12, message=_('*กรุณาเลือกเดือนเกิด'))], coerce=int, choices=generate_date_choices('month'))
    birth_year = SelectField(_('ปีเกิด'), validators=[NumberRange(min=generate_date_choices('start_year'), max=generate_date_choices('end_year'), message=_('*กรุณาเลือกปีเกิด'))], coerce=int, choices=generate_date_choices('year'))
    gender = RadioField(_('เพศ'), validators=[InputRequired(message=_('*กรุณาเลือกเพศ'))], coerce=str, choices=generate_gender_choices())
    # sexual_orientation = MultiCheckboxField(_('เพศวิถี'), validators=[Length(min=1, message=_('*กรุณาเลือกเพศวิถี'))], coerce=str, choices=generate_sexual_orientation_choices())
    showme = MultiCheckboxField(_('โชว์ฉันกับ'), validators=[Length(min=1, message=_('*กรุณาเลือกเพศที่ต้องการโชว์'))], coerce=str, choices=generate_gender_choices())
    passion = MultiCheckboxField(_('ความสนใจ'), validators=[Length(min=1, message=_('*กรุณาเลือกความสนใจของคุณ'))], coerce=str, choices=generate_passion_choices())
    # photo = FileField(validators=[FileRequired()],  render_kw = {'multiple': True},)
    # birthday = DateField(_('วันเกิด'), format='%d/%m/%Y')
    # submit = SubmitField(label=(_('Submit')))
