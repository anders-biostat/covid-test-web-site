#!/usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib, binascii, os
import click, glob, polib
from envparse import env
from termcolor import colored
from bson.json_util import dumps
import pytz

from flask import Flask, request, render_template, Blueprint, g, redirect, url_for, session, flash, jsonify, Response
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel, _

from forms import RegistrationForm, ResultsQueryForm, ConsentForm
import scripts.encryption_helper as encryption_helper

from common.statuses import SampleStatus
from common.models import Sample, Event, Registration

# file names
dir = os.path.abspath('')

# Creating RSA Instance for encryption
rsa_public_filename = env("RSA_PUBLIC_FILENAME", cast=str, default="public.pem")
PUBLIC_KEY_FILENAME = os.path.join(dir, "../data/", rsa_public_filename)
rsa_instance = encryption_helper.rsa_instance(PUBLIC_KEY_FILENAME)

RESULTS_FILENAME = os.path.join(dir, "../data/results.txt")

TEMPLATE_DIR = os.path.join(dir, "../static/i18n/")
STATIC_DIR = os.path.join(dir, "../static/assets/")
TRANSLATIONS_DIR = os.path.join(dir, "../translations/")
timezone = pytz.timezone('Europe/Berlin')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config['SECRET_KEY'] = env("SECRET_KEY", cast=str, default="secret")

csrf = CSRFProtect()
app.config['BABEL_TRANSLATION_DIRECTORIES'] = TRANSLATIONS_DIR
babel = Babel(app)
bp = Blueprint('site', __name__)


@bp.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang', g.lang_code)


@bp.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang')


@babel.localeselector
def get_locale():
    return g.lang_code


@bp.route('/', methods=['GET'])
def index():
    barcode = request.args.get('barcode')
    if barcode is not None:
        session['barcode'] = barcode.upper()
        return redirect(url_for('site.consent'))
    return render_template('index.html')


@bp.route('/instructions', methods=['GET'])
def instructions():
    if 'barcode' in session:
        barcode = session.get("barcode")
    else:
        barcode = None
    return render_template('instructions.html', barcode=barcode)


@bp.route('/consent', methods=['GET', 'POST'])
def consent():
    form = ConsentForm()
    if request.method == 'POST':
        if request.form.get('terms') == '1':
            session['consent'] = True
            return redirect(url_for('site.register'))
        else:
            flash(_('Sie müssen erst der Teilnahme zustimmen, um fortzufahren'))
            return render_template('consent.html', form=form)
    else:
        return render_template('consent.html', form=form)


@bp.route('/extern/query/<string:barcode>', methods=['GET'])
def query_dataset(barcode):
    null_response = Response(response="{}", status=200, mimetype="application/json")
    if barcode is not None:
        barcode = barcode.strip().upper()
        sample = Sample.objects.filter(barcode=barcode).first()
        if sample is not None:
            return Response(response=dumps(sample), status=200, mimetype="application/json")
        else:
            return null_response
    else:
        return null_response


@bp.route('/results', methods=['GET', 'POST'])
def results_query():
    form = ResultsQueryForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            barcode = form.bcode.data.upper()
            form_password = form.psw.data

            # Hash entered password
            sha_instance = hashlib.sha3_384()
            sha_instance.update(form_password.encode("utf-8"))
            form_password_hashed = binascii.b2a_base64(sha_instance.digest(), newline=False).decode("ascii")

            # Check if barcode exists
            sample = Sample.objects.get(barcode=barcode)
            if sample is None:
                flash(_('Der Barcode ist unbekannt. Bitte erneut versuchen.'), 'error')
                return redirect(url_for('site.results_query'))
            else:
                registration_count = len(sample['registrations'])
                if registration_count > 1:
                    return render_template("pages/multiple-registeration.html", barcode=barcode)
                if registration_count < 1:
                    flash(_('Der Barcode wurde nicht registriert. Bitte registrieren Sie den Barcode vorher'),
                          'warning')
                    session['barcode'] = barcode
                    return redirect(url_for('site.register'))
                else:
                    if form_password_hashed != sample['registrations'][0]['password_hash']:  # Wrong password
                        flash(_(
                            'Das Passwort stimmt nicht mit dem überein, dass Sie beim Registrieren der Barcodes gewählt haben. Bitte versuchen Sie es noch einmal.'),
                            'error')
                        return redirect(url_for('site.results_query'))
                    else:
                        status = sample.get_status()
                        if status is not None:
                            status = SampleStatus[status['status']]

                            if status == SampleStatus.PCRPOS:
                                return render_template("pages/test-PCRPOS.html")
                            if status == SampleStatus.PCRNEG:
                                return render_template("pages/test-PCRNEG.html")
                            if status == SampleStatus.LAMPPOS:
                                return render_template("pages/test-LAMPPOS.html")
                            if status == SampleStatus.LAMPNEG:
                                return render_template("pages/test-LAMPNEG.html")
                            if status == SampleStatus.LAMPINC:
                                return render_template("pages/test-LAMPINC.html")
                            if status == SampleStatus.UNDEF:
                                return render_template("pages/test-UNDEF.html")
                            if status == SampleStatus.WAIT:
                                return render_template("pages/test-WAIT.html")
                            else:
                                return render_template("pages/test-UNDEF.html")
                        else:  # No results list
                            return render_template("pages/test-WAIT.html")
    else:
        return render_template('result-query.html', form=form)


@bp.route('/information', methods=['GET'])
def information():
    return render_template('pages/information.html')


@bp.route('/registration', methods=['GET', 'POST'])
def register():
    if "barcode" in session:
        barcode = session.get('barcode')
    else:
        barcode = request.args.get('barcode')

    if session.get("consent") != True:
        return redirect(url_for('site.consent'))

    session["barcode"] = None

    form = RegistrationForm()
    if request.method == 'POST':  # POST
        if form.validate_on_submit():
            barcode = form.bcode.data.upper().strip()
            name = form.name.data
            address = form.address.data
            contact = form.contact.data
            psw = form.psw.data
            psw_repeat = form.psw_repeat.data

            sample = Sample.objects.get(barcode=barcode)

            if sample is None:
                flash(_('Der Barcode ist unbekannt. Bitte erneut versuchen.'), 'error')
                return render_template('register.html', form=form)
            else:
                session["barcode"] = barcode

                doc = encryption_helper.encode_subject_data(rsa_instance, barcode, name, address, contact, psw)

                registration = Registration(
                    barcode=doc['barcode'],
                    time=doc['time'],
                    name_encrypted=doc['name_encrypted'],
                    address_encrypted=doc['address_encrypted'],
                    contact_encrypted=doc['contact_encrypted'],
                    password_hash=doc['password_hash'],
                    public_key_fingerprint=doc['key_information']['public_key_fingerprint'],
                    session_key_encrypted=doc['key_information']['session_key_encrypted'],
                    aes_instance_iv=doc['key_information']['aes_instance_iv'],
                )

                added_registration = sample.modify(push__registrations=registration)
                if added_registration:
                    flash(_('Erfolgreich registriert'), 'success')
                    return redirect(url_for('site.instructions'))
        else:
            return render_template('register.html', form=form)
    return render_template('register.html', form=form, barcode=barcode)


@bp.route('/sites/<string:page>', methods=['GET'])
def pages(page):
    return render_template("pages/" + page)


# Variant A: https://example.com/index for "de" else https://example.com/en/index
app.register_blueprint(bp, url_defaults={'lang': 'de'})
app.register_blueprint(bp, url_prefix='/<lang>')


@app.cli.group()
def translate():
    """Translation and localization commands."""
    pass


@translate.command()
def update():
    """Update all languages."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot ..'):
        raise RuntimeError('extract command failed')
    if os.system('pybabel update -i messages.pot -d ../translations'):
        raise RuntimeError('update command failed')
    try:
        print("=" * 40)
        print("Translation Percentages: ")
        print("---")
        translation_directories = glob.glob(TRANSLATIONS_DIR + "/*/")
        for directory in translation_directories:
            try:
                po = polib.pofile(os.path.join(directory, "LC_MESSAGES/messages.po"))
                percentage_translated = po.percent_translated()
                color = 'blue'

                if percentage_translated == 100:
                    color = 'green'
                if percentage_translated < 100:
                    color = 'yellow'
                if percentage_translated <= 90:
                    color = 'red'

                print(colored(("Language: %s" % directory.split("/")[-2]), color))
                print(colored(("Directory: %s" % directory), color))
                print(colored("Percentage translated: %s" % str(percentage_translated), color))
                print("---")
            except Exception as e:
                print(e)
                print("Error parsing ", directory)
                pass
    except:
        print("Error parsing translation directory")
        pass
    os.remove('messages.pot')


@translate.command()
def compile():
    """Compile all languages."""
    if os.system('pybabel compile -d ../translations'):
        raise RuntimeError('compile command failed')


@translate.command()
@click.argument('lang')
def init(lang):
    """Initialize a new language."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot ..'):
        raise RuntimeError('extract command failed')
    if os.system(
            'pybabel init -i messages.pot -d ../translations -l ' + lang):
        raise RuntimeError('init command failed')
    os.remove('messages.pot')


if __name__ == '__main__':
    debug = env("DEBUG", cast=bool, default=False)
    if debug:
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
    csrf.init_app(app)
    app.run(debug=debug)
