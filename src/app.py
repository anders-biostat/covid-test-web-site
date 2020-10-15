#!/usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib, binascii, os
from urllib.parse import urljoin
import click, glob, polib
from envparse import env
from termcolor import colored
from pymongo import MongoClient

from flask import Flask, request, render_template, Blueprint, g, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel, _

from forms import RegistrationForm, ResultsQueryForm
import scripts.encryption_helper as encryption_helper

# Reading the Environemt-Variables from .env file
env.read_envfile()

client = MongoClient()
DATABASE = env("DATABASE", cast=str, default="covidtest-test")
db = client[DATABASE]

# Creating RSA Instance for encryption
rsa_instance = encryption_helper.rsa_instance()

# file names
dir = os.path.abspath('')

SUBJECT_DATA_FILENAME = os.path.join(dir, "../data/subjects.csv")
PUBLIC_KEY_FILENAME = os.path.join(dir, "../data/public.pem")
HTML_DIRS = os.path.join(dir, "../static/")
RESULTS_FILENAME = os.path.join(dir, "../data/results.txt")
NGINX_CONF_FILENAME = os.path.join(dir, "../etc/covid-test.nginx-site-config")

TEMPLATE_DIR = os.path.join(dir, "../static/i18n/")
STATIC_DIR = os.path.join(dir, "../static/assets/")
TRANSLATIONS_DIR = os.path.join(dir, "../translations/")

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


@bp.route('/favicon.ico', methods=['GET'])
def favicon():
    return ""


@bp.route('/instructions', methods=['GET'])
def instructions():
    if 'instructions_file' in session:
        instructions_file = "instructions/" + session.get('instructions_file')
        if not os.path.exists(urljoin(TEMPLATE_DIR, instructions_file)):
            instructions_file = None
    else:
        instructions_file = None

    if 'event_name' in session:
        event_name = session.get('event_name')
    else:
        event_name = None

    if 'barcode' in session:
        barcode = session.get("barcode")
    else:
        barcode = None
    return render_template('instructions.html', instructions_file=instructions_file, event_name=event_name,
                           barcode=barcode)


@bp.route('/consent', methods=['GET', 'POST'])
def consent():
    if request.method == 'POST':
        if request.form.get('terms') == '1':
            session['consent'] = True
            return redirect(url_for('site.register'))
        else:
            return render_template('consent.html')
    else:
        return render_template('consent.html')


@bp.route('/results', methods=['GET', 'POST'])
def results_query():
    form = ResultsQueryForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            form_barcode = form.bcode.data.upper()
            form_password = form.psw.data

            # Check if barcode exists
            sample = db['samples'].find_one({'_id': bcode})
            if sample is None:
                return render_template("pages/barcode-unknown.html", barcode=form_barcode)

            # Find barcode registration
            hashes_found = set()
            with open(SUBJECT_DATA_FILENAME) as f:
                for line in f:
                    barcode, timestamp, password_hash, remainder = line.split(",", 3)
                    if barcode == form_barcode:
                        hashes_found.add(password_hash)

            if len(hashes_found) == 0:
                return render_template("barcode-not-registered.html", barcode=form_barcode)

            if len(hashes_found) > 1:
                return render_template("multiple-registeration.html", barcode=form_barcode)

            assert len(hashes_found) == 1

            # Hash entered password
            sha_instance = hashlib.sha3_384()
            sha_instance.update(form_password.encode("utf-8"))
            encoded_hash_from_form = binascii.b2a_base64(sha_instance.digest(), newline=False)

            if encoded_hash_from_form != list(hashes_found)[0].encode("ascii"):
                return render_template("wrong-password.html")

            # Check results
            with open(RESULTS_FILENAME) as f:
                for line in f:
                    if line.find(",") >= 0:
                        barcode, remainder = line.rstrip().split(",", 1)
                    else:
                        barcode, remainder = line.rstrip(), ""
                    if barcode == form_barcode:
                        if remainder == "":
                            return render_template("test-result-negative.html")
                        elif remainder.lower().startswith("pos"):
                            return render_template("test-result-positive.html")
                        elif remainder.lower().startswith("inc"):
                            return render_template("to-be-determined.html")
                        elif remainder.lower().startswith("failed"):
                            return render_template("to-failed.html")
                        else:
                            return render_template("internal-error.html")
            return render_template("no-result.html")
    else:
        return render_template('result-query.html', form=form)


@bp.route('/information', methods=['GET'])
def information():
    return render_template('information.html')


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
                return render_template("pages/barcode-unknown.html", barcode=bcode)
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