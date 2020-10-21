from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_babel import _


class ConsentForm(FlaskForm):
    terms = BooleanField(_('Einverständnis'))


class RegistrationForm(FlaskForm):
    bcode = StringField(_('Barcode'), validators=[DataRequired()])
    name = StringField(_('Name'), validators=[DataRequired()])
    address = StringField(_('Addresse'), validators=[DataRequired()])

    contact = StringField(_('Kontaktinformationen'), validators=[DataRequired()])

    psw = PasswordField(_('Passwort'), validators=[DataRequired()])
    psw_repeat = PasswordField(_('Passwort wiederholen'), validators=[DataRequired(), EqualTo('psw', message=_(
        'Passwörter müssen übereinstimmen'))])


class ResultsQueryForm(FlaskForm):
    bcode = StringField(_('Barcode'), validators=[DataRequired()])
    psw = PasswordField(_('Passwort'), validators=[DataRequired()])

class LabQueryForm(FlaskForm):
    search = StringField(_('Barcode'), validators=[DataRequired()])

class LabCheckInForm(FlaskForm):
    barcode = StringField(_('Barcode'), validators=[DataRequired()])
    rack = StringField(_('Rack'), validators=[DataRequired()])

class LabRackResultsForm(FlaskForm):
    rack = StringField(_('Rack'), validators=[DataRequired()])

    lamp_positive = StringField(_('LAMP positiv'))
    lamp_inconclusive = StringField(_('LAMP unklares Ergebnis'))

class LabProbeEditForm(FlaskForm):
    barcode = StringField(_('Barcode'))
    rack = StringField(_('Rack'))
    status = SelectField(
        _('Probenstatus'),
        choices=[
            ('-', '-'),
            ('printed', 'Printed'),
            ('wait', 'Waiting'),
            ('negative', 'LAMP negative'),
            ('lamppos', 'LAMP positive'),
            ('lampinc', 'LAMP inconclusive'),
            ('pcrpos', 'PCR positive'),
            ('pcrneg', 'PCR negative'),
            ('undef', 'Undefined'),
        ]
    )