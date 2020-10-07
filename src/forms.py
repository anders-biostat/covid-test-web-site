from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_babel import _

class RegistrationForm(FlaskForm):
    bcode = StringField('Barcode', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])

    contact = StringField('Contact information', validators=[DataRequired()])

    psw = PasswordField('Password', validators=[DataRequired()])
    psw_repeat = PasswordField('Password repeat', validators=[DataRequired(), EqualTo('psw', message=_('Passwords must match'))])


class ResultsQueryForm(FlaskForm):
	bcode = StringField('Barcode', validators=[DataRequired()])
	psw = PasswordField('Password', validators=[DataRequired()])