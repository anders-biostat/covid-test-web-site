from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_babel import _

class RegistrationForm(FlaskForm):
    bcode = StringField(_('Barcode'), validators=[DataRequired()])
    name = StringField(_('Name'), validators=[DataRequired()])
    address = StringField(_('Addresse'), validators=[DataRequired()])

    contact = StringField(_('Kontaktinformationen'), validators=[DataRequired()])

    psw = PasswordField(_('Passwort'), validators=[DataRequired()])
    psw_repeat = PasswordField(_('Passwort wiederholen'), validators=[DataRequired(), EqualTo('psw', message=_('Passwörter müssen übereinstimmen'))])


class ResultsQueryForm(FlaskForm):
	bcode = StringField(_('Barcode'), validators=[DataRequired()])
	psw = PasswordField(_('Passwort'), validators=[DataRequired()])