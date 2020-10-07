#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback, time, hashlib, binascii, signal, re, os
import urllib.parse, flup.server.fcgi
import Crypto.PublicKey.RSA, Crypto.Cipher.PKCS1_OAEP
from urllib.parse import urljoin
import click, glob, polib
from envparse import env
from pymongo import MongoClient
import arrow

from flask import Flask, request, render_template, Blueprint, g, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel, _
from config import LANGUAGES

from forms import RegistrationForm, ResultsQueryForm
import scripts.load_codes as load_codes

# Reading the Environemt-Variables from .env file
env.read_envfile()

# Check if MongoDB

MONGODB = env("MONGODB", cast=bool, default=False)

if MONGODB:
    from pymongo import MongoClient
    client = MongoClient()

    DATABASE = env("DATABASE", cast=str, default="covidtest-test")
    db = client[DATABASE]

# file names
dir = os.path.dirname(__file__)

SUBJECT_DATA_FILENAME = os.path.join(dir, "../data/subjects.csv")
PUBLIC_KEY_FILENAME = os.path.join(dir, "../data/public.pem")
HTML_DIRS = os.path.join(dir, "../static/")
RESULTS_FILENAME = os.path.join(dir, "../data/results.txt")
NGINX_CONF_FILENAME = os.path.join(dir, "../etc/covid-test.nginx-site-config")

TEMPLATE_DIR = os.path.join(dir, "../static/i18n/")
STATIC_DIR = os.path.join(dir, "../static/assets/")
TRANSLATIONS_DIR = os.path.join(dir, "../translations/")

LANGUAGES = {
    'de': 'German',
    'en': 'English'
}

def load_data(reread_files=False):
    # This function loads all the data. It is called once at the beginning
    # and also, when SIGHUP is issued to the process in order to trigger
    # a reload.
    # It sets the following global variables
    global rsa_instance
    global codes2events

    # Read public key for encryption of contact information
    with open( PUBLIC_KEY_FILENAME, "rb" ) as f:
       public_key = Crypto.PublicKey.RSA.import_key( f.read() )
    rsa_instance = Crypto.Cipher.PKCS1_OAEP.new( public_key )

    # Get fingerprint of public key
    md5_instance = hashlib.md5()
    md5_instance.update( public_key.publickey().exportKey("DER") )
    rsa_instance.public_key_fingerprint = md5_instance.hexdigest().encode("ascii")

    codes2events = load_codes.load_codes()

    if (MONGODB and 'events' not in db.list_collection_names()) or reread_files:
        print("No events collection found. Reading events ...")
        for barcode, event in codes2events.items():
            event_name, event_instructions = event

            doc = {
                '_id': barcode,
                'barcode': barcode,
                'event_name': event_name,
                'event_instructions': event_instructions,
            }

            db['events'].update_one({'_id': barcode}, {'$set': doc}, upsert=True)


def encode_subject_data(barcode, name, address, contact, password, return_dict=False):

    # Generate session key for use with AES and encrypt it with RSA
    session_key = Crypto.Random.get_random_bytes( 16 )
    encrypted_session_key = rsa_instance.encrypt( session_key )
    aes_instance = Crypto.Cipher.AES.new( session_key, Crypto.Cipher.AES.MODE_CBC )

    # encode, pad, then encrypt subject data
    encrypted_subject_data = []
    for s in [ name, address, contact ]:
        s = s.encode( "utf-8" )
        if len(s) % 16 != 0:
            s += b'\000' * ( 16 - len(s) % 16 )
        encrypted_subject_data.append(aes_instance.encrypt(s))

    # encode user password with SHA3
    sha_instance = hashlib.sha3_384()
    sha_instance.update( password.encode( "utf-8" ) )
    password_hash = sha_instance.digest()

    # Make a line for the CSV file
    fields = [
       barcode.encode( "utf-8" ),
       time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime() ).encode( "utf-8" ),
       password_hash,
       rsa_instance.public_key_fingerprint,
       encrypted_session_key,
       aes_instance.iv ]
    fields.extend( encrypted_subject_data )

    # Base64-encode everything excepct for password, time stamp and public key fingerprint
    for i in range( len(fields) ):
        if i not in ( 0, 1, 3 ):
            fields[i] = binascii.b2a_base64( fields[i], newline=False )

    if return_dict is True:
        return {
            'barcode': barcode.encode( "utf-8" ),
            'time': arrow.now(),
            'password_hash': password_hash,
            'public_key_fingerprint': rsa_instance.public_key_fingerprint,
            'encrypted_session_key': encrypted_session_key,
            'aes_instance_iv': aes_instance.iv,
            'name_encrypted': encrypted_subject_data[0],
            'address_encrypted': encrypted_subject_data[1],
            'contact_encrypted': encrypted_subject_data[2],
        }

    # Make line for file and return it
    return b",".join( fields ).decode("ascii") + "\n"

load_data()


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
    return render_template('instructions.html', instructions_file=instructions_file, event_name=event_name, barcode=barcode)

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
            if form_barcode not in codes2events:
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
                        barcode, remainder = line.rstrip().split( ",", 1 )
                    else:
                        barcode, remainder = line.rstrip(), ""
                    if barcode == form_barcode:
                        if remainder == "":
                            return render_template("test-result-negative.html")
                        elif remainder.lower().startswith( "pos" ):
                            return render_template("test-result-positive.html")
                        elif remainder.lower().startswith( "inc" ):
                            return render_template("to-be-determined.html")
                        elif remainder.lower().startswith( "failed" ):
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
    if request.method == 'POST': # POST
        if form.validate_on_submit():
            bcode = form.bcode.data.upper()
            name = form.name.data
            address = form.address.data
            contact = form.contact.data
            psw = form.psw.data
            psw_repeat = form.psw_repeat.data

            if bcode not in codes2events:
                return render_template("pages/barcode-unknown.html", barcode=bcode)
            else:
                try:
                    instructions_file =  codes2events[bcode].instructions
                    event_name =  codes2events[bcode].name
                    session['instructions_file'] = instructions_file
                    session['event_name'] = event_name
                except:
                    pass

                session["barcode"] = bcode

                line = encode_subject_data(bcode, name, address, contact, psw)

                with open(SUBJECT_DATA_FILENAME, "a") as f:
                    f.write(line)

                if MONGODB:
                    doc = encode_subject_data(bcode, name, address, contact, psw, return_dict=True)
                    db['registrations'].update_one(
                        {'_id': bcode}, 
                        {
                            '$setOnInsert': {'_id': bcode, 'registrations': []},
                            '$push': {'registrations': doc},
                        },
                        upsert=True
                    )

                return redirect(url_for('site.instructions'))
        else: # Form invalid
            return render_template('register.html', form=form)
        
    else: # GET
        return render_template('register.html', form=form, barcode=barcode)

@bp.route('/sites/<string:page>', methods=['GET'])
def pages(page):
    return render_template("pages/" + page)


# Variant A: https://example.com/index for "de" else https://example.com/en/index
app.register_blueprint(bp, url_defaults={'lang': 'de'})
app.register_blueprint(bp, url_prefix='/<lang>')

@app.cli.group()
def read():
    """Reading data commands."""
    pass

@read.command()
def events():
    """Reading Events to Database"""
    load_data(reread_files=True)


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
        print("="*40)
        print("Translation Percentages: ")
        print("---")
        translation_directories = glob.glob(TRANSLATIONS_DIR + "/*/")
        for directory in translation_directories:
            try:
                po = polib.pofile(os.path.join(directory, "LC_MESSAGES/messages.po"))
                print("Directory: ", directory)
                print("Percentage translated: " + str(po.percent_translated()) + "%")
                print("---")
            except:
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
