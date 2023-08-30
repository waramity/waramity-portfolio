from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, SelectMultipleField, widgets, RadioField, MultipleFileField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, InputRequired, NumberRange
from flask_wtf.file import FileField, FileRequired

from flask_babel import _

import datetime

class CreatePromptBuilderForm(FlaskForm):
    builder_name = StringField(_('ชื่อ Prompt builder ของคุณ'), validators=[InputRequired(message=_('*กรุณากรอกชื่อ Builder')), Length(min=2, max=35, message=_('*ชื่อ Builder ต้องมี 2-35 ตัวอักษร'))])
    submit = SubmitField(_('สร้าง'))

class DestoryPromptBuilderForm(FlaskForm):
    slug = StringField(_('พิมพ์ชื่อ Slug เพื่อลบ Prompt builder'), validators=[InputRequired(message=_('*กรุณากรอกชื่อ Builder')), Length(min=2, max=35, message=_('*ชื่อ Builder ต้องมี 2-35 ตัวอักษร'))])
    submit = SubmitField(_('ลบ Prompt builder'))

class EditPromptBuilderForm(FlaskForm):
    builder_name = StringField(_('ชื่อ Prompt builder'), validators=[InputRequired(message=_('*กรุณากรอกชื่อ Builder')), Length(min=2, max=35, message=_('*ชื่อ Builder ต้องมี 2-35 ตัวอักษร'))])
    description = StringField(_('รายละเอียด'), validators=[Length(min=0, max=150, message=_('*รายละเอียดต้องน้อยกว่า 150 ตัวอักษร'))])
    submit = SubmitField(_('บันทึก'))
