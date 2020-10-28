#!/usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib, binascii, os
from urllib.parse import urljoin
import click, glob, polib
from envparse import env
from termcolor import colored
from pymongo import MongoClient
from bson.json_util import dumps
from bson.codec_options import CodecOptions
import pytz

from flask import Flask, request, render_template, Blueprint, g, redirect, url_for, session, flash, jsonify, Response
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel, _

from forms import RegistrationForm, ResultsQueryForm, ConsentForm, LabQueryForm, LabCheckInForm, LabRackResultsForm, LabProbeEditForm
import scripts.encryption_helper as encryption_helper
import scripts.database_actions as database_actions
from scripts.statuses import SampleStatus

client = MongoClient()
DATABASE = 'covidtest'
db = client[DATABASE]

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

@bp.route('/dashboard', methods=['GET'])
def dashboard():
    overall_count = db['samples'].count({})
    negative = db['samples'].count({'$expr': {'$eq': [{'$last': "$results.status"}, "negative"]}})
    positive = db['samples'].count({ '$expr': { '$eq': [{ '$last': "$results.status" }, "positive"] } })
    stats = {
        'overall_count': overall_count,
        'negative': negative,
        'positive': positive
    }
    return render_template('pages/dashboard.html', stats=stats)

@bp.route('/lab', methods=['GET'])
def labview_home():
    return render_template('lab/home.html')

@bp.route('/lab/check_in', methods=['GET', 'POST'])
def probe_check_in():
    form = LabCheckInForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            barcode = form.barcode.data.upper().strip()
            rack = form.rack.data.upper().strip()

            sample = database_actions.update_status(db, barcode, SampleStatus.WAIT, rack=rack)
            if sample is None:
                flash(_('Barcode nicht in Datenbank'), 'error')
            else:
                flash(_('Probe erfolgreich eingetragen'), 'positive')
            return render_template('lab/probe_check_in.html', form=form, sample=sample, rack=rack)
    return render_template('lab/probe_check_in.html', form=form, display_sample=False)

@bp.route('/lab/rack', methods=['GET', 'POST'])
def probe_rack():
    form = LabRackResultsForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            rack = form.rack.data.upper().strip()

            lamp_positive = form.lamp_positive.data.replace(',', '\n').replace(';', '\n')
            lamp_inconclusive = form.lamp_inconclusive.data.replace(',', '\n').replace(';', '\n')

            lamp_positive = [x.strip() for x in lamp_positive.split()]
            lamp_inconclusive = [x.strip() for x in lamp_inconclusive.split()]

            wrong_status_sequence = database_actions.rack_results(db, rack, lamp_positive, lamp_inconclusive)
            if wrong_status_sequence is None:
                flash(_('Keine Barcodes zu Rack gefunden'), 'error')
            else:
                for barcode in wrong_status_sequence:
                    flash(_('Falsche Statusfolge: ') + str(barcode), 'warning')
            return render_template('lab/probe_rack_results.html', form=form)
    return render_template('lab/probe_rack_results.html', form=form)

@bp.route('/lab/query', methods=['GET', 'POST'])
def probe_query():
    form = LabQueryForm()
    edit_form = LabProbeEditForm()
    if request.method == 'POST':
        if 'search' in request.form:
            if form.validate_on_submit():
                samples = db['samples'].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=timezone))
                search = form.search.data.upper().strip()
                sample = samples.find_one({'_id': search})
                return render_template('lab/probe_query.html', form=form, edit_form=edit_form, sample=sample, search=search)
        if 'edit' in request.form:
            if edit_form.validate_on_submit():
                samples = db['samples'].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=timezone))
                barcode = edit_form.barcode.data.upper().strip()
                status = edit_form.status.data.upper().strip()
                rack = edit_form.rack.data.upper().strip()

                sample = samples.find_one({'_id': barcode})
                if sample is None:
                    flash(_('Sample nicht gefunden'), 'error')
                else:
                    if rack != sample['rack']:
                        samples.update_one({'_id': sample['_id']}, {'$set': {'rack': rack}}, upsert=True)
                        flash(_('Sample rack geupdated'), 'positive')

                    if status != '-':
                        status = SampleStatus[status]
                        new_sample = database_actions.update_status(db, sample['_id'], status, rack=None)
                        if new_sample is not None:
                            flash(_('Status geupdated'), 'positive')
                    else:
                        new_sample = sample
                return render_template('lab/probe_query.html', form=form, edit_form=edit_form, sample=new_sample)

    return render_template('lab/probe_query.html', form=form, edit_form=edit_form)

@bp.route('/favicon.ico', methods=['GET'])
def favicon():
    return ""

@bp.route('/apple-touch-icon/', methods=['GET'])
def touch_icon():
    return ""


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
    resp = Response(response="{}",status=200,mimetype="application/json")
    if barcode is not None:
        sample = db['samples'].find_one({'_id': barcode})
        if sample is not None:
            return Response(response=dumps(sample),status=200,mimetype="application/json")
        else:
            return resp
    else:
        return resp

@bp.route('/results', methods=['GET', 'POST'])
def results_query():
    form = ResultsQueryForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            form_barcode = form.bcode.data.upper()
            form_password = form.psw.data

            # Hash entered password
            sha_instance = hashlib.sha3_384()
            sha_instance.update(form_password.encode("utf-8"))
            form_password_hashed = binascii.b2a_base64(sha_instance.digest(), newline=False).decode("ascii")

            # Check if barcode exists
            sample = db['samples'].find_one({'_id': form_barcode})
            if sample is None:
                flash(_('Der Barcode ist unbekannt. Bitte erneut versuchen.'), 'error')
                return redirect(url_for('site.results_query'))
            else:
                if 'registrations' not in sample:
                    flash(_('Der Barcode wurde nicht registriert. Bitte registrieren Sie den Barcode vorher'),
                          'warning')
                    session['barcode'] = form_barcode
                    return redirect(url_for('site.register'))
                else:  # Barcode found
                    registration_count = len(sample['registrations'])
                    if registration_count > 1:
                        return render_template("pages/multiple-registeration.html", barcode=form_barcode)
                    if registration_count < 1:
                        flash(_('Der Barcode wurde nicht registriert. Bitte registrieren Sie den Barcode vorher'), 'warning')
                        session['barcode'] = form_barcode
                        return redirect(url_for('site.register'))
                    else:
                        if form_password_hashed != sample['registrations'][0]['password_hash']:  # Wrong password
                            flash(_('Das Passwort stimmt nicht mit dem überein, dass Sie beim Registrieren der Barcodes gewählt haben. Bitte versuchen Sie es noch einmal.'),'error')
                            return redirect(url_for('site.results_query'))
                        else:
                            if 'results' in sample and len(sample['results']) > 0:
                                results = sample['results']
                                latest_result = results[-1]
                                latest_status = SampleStatus[latest_result['status']]

                                print(latest_status)

                                if latest_status == SampleStatus.PCRPOS:
                                    return render_template("pages/test-PCRPOS.html")
                                if latest_status == SampleStatus.PCRNEG:
                                    return render_template("pages/test-PCRNEG.html")
                                if latest_status == SampleStatus.LAMPPOS:
                                    return render_template("pages/test-LAMPPOS.html")
                                if latest_status == SampleStatus.LAMPNEG:
                                    return render_template("pages/test-LAMPNEG.html")
                                if latest_status == SampleStatus.LAMPINC:
                                    return render_template("pages/test-LAMPINC.html")
                                if latest_status == SampleStatus.UNDEF:
                                    return render_template("pages/test-UNDEF.html")
                                if latest_status == SampleStatus.WAIT:
                                    return render_template("pages/test-WAIT.html")
                                else:
                                    return render_template("pages/test-UNDEF.html")
                            else: # No results list
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
            bcode = form.bcode.data.upper()
            name = form.name.data
            address = form.address.data
            contact = form.contact.data
            psw = form.psw.data
            psw_repeat = form.psw_repeat.data

            sample = db['samples'].find_one({'_id': bcode})

            if sample is None:
                flash(_('Der Barcode ist unbekannt. Bitte erneut versuchen.'), 'error')
                return render_template('register.html', form=form)
            else:
                try:
                    instructions_file = sample.event_instructions
                    event_name = sample.event_name
                    session['instructions_file'] = instructions_file
                    session['event_name'] = event_name
                except:
                    pass

                session["barcode"] = bcode

                doc = encryption_helper.encode_subject_data(rsa_instance, bcode, name, address, contact, psw)

                db['samples'].update_one(
                    {'_id': bcode},
                    {
                        '$setOnInsert': {'_id': bcode, 'registrations': []},
                    },
                    upsert=True
                )
                db['samples'].update_one(
                    {'_id': bcode},
                    {
                        '$push': {'registrations': doc},
                    },
                    upsert=True
                )

                return redirect(url_for('site.instructions'))
        else:
            return render_template('register.html', form=form)

    else:  # GET
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
