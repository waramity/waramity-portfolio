from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, SelectMultipleField, widgets, RadioField, MultipleFileField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, InputRequired, NumberRange

from flask_babel import _

import datetime

class DestoryPromptCollectionForm(FlaskForm):
    slug = StringField(_('Type the name \'Slug\' to delete the Prompt.'), validators=[InputRequired(message=_('*Please enter the Prompt')), Length(min=2, max=35, message=_('*Prompt must be between 2-35 characters'))])
    submit = SubmitField(_('Delete prompt'))
