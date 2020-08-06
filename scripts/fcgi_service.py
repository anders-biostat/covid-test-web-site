#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback, time, hashlib, binascii, signal
import urllib.parse, flup.server.fcgi, cgi
import Crypto.PublicKey.RSA, Crypto.Cipher.PKCS1_OAEP

import load_codes

#SOCKET = "../etc/fcgi.sock"
PORT = 31235

SUBJECT_DATA_FILENAME = "../data/subjects.csv"
PUBLIC_KEY_FILENAME = "../data/public.pem"
INSTRUCTIONS_HTML_FILENAME = "../static/instruction-de.html"
RESULTS_DATA_FILENAME = "../data/result_test.csv"


def load_data():
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


def encode_subject_data( barcode, name, address, contact, password ):

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
       encrypted_subject_data.append( aes_instance.encrypt( s ) )

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

    # Make line for file and return it
    return b",".join( fields ).decode("ascii") + "\n"


def app_register( environ, start_response ):

    # Read POST data
    request_body_size = int( environ.get('CONTENT_LENGTH', 0) )
    request_body = environ['wsgi.input'].read(request_body_size)
    fields = urllib.parse.parse_qs( request_body.decode("ascii") )
    fields = { k : v[0] for (k,v) in fields.items() }
    barcode = fields['bcode'].upper()

    if fields['psw'] != fields['psw-repeat']:
        start_response('200 OK', [('Content-Type', 'text/html')])
        return[
           b"<html><head><meta charset=UTF-8></head><body><h3>Passwords did not match.</h3>",
           b"Please go back and try again.</body></html>",
           "<html><body><h3>Passwörter stimmen nicht überein.</h3>".encode("utf-8"),
           "Bitte gehen Sie zurück und versuchen Sie es noch einmal.</body></html>".encode("utf-8") ]

    elif barcode not in codes2events:

        start_response('200 OK', [('Content-Type', 'text/html')])
        return[ s.encode("utf-8") for s in [
           "<html><head><meta charset=utf-8></head><body><h3>Barcode unknown</h3>",
           "The barcode you entered (%s) is unknown. " % barcode,
           "Maybe you have types it wrongly? Please go back and try again.</body></html>",
           "<html><body><h3>Barcode unbekannt.</h3>",
           "Der Barcode, den Sie eingegeben haben (%s), ist unbekannt. " % barcode,
           "Vielleicht haben Sie sich vertippt. ",
           "Bitte gehen Sie zurück und versuchen Sie es noch einmal.</body></html>" ] ]

    else:

        line = encode_subject_data( barcode, fields['name'], fields['address'],
            fields['contact'], fields['psw'] )

        with open( SUBJECT_DATA_FILENAME, "a" ) as f:
            f.write( line )

        start_response( '303 See other', [('Location', 'fcgi-instructions?code=' + \
            barcode )] )
        return []


def app_instructions( environ, start_response ):

    fields = cgi.parse_qs( environ['QUERY_STRING'] )
    barcode = fields['code'][0]

    start_response('200 OK', [('Content-Type', 'text/html')])

    lines = []
    with open( INSTRUCTIONS_HTML_FILENAME, "rb" ) as f:
        for line in f:
            if line.find( b"@@REPLACE_WITH_INSTRUCTIONS" ) >= 0:
               lines.append( codes2events[ barcode ].instructions.encode("utf-8") )
               lines.append( ( "<p><small>[Code '%s' of Event '%s']</small></p>" %
                  ( barcode, codes2events[barcode].name ) ).encode("utf-8") )
            else:
                lines.append( line )
    return lines

# a funtion to authenticate the passwords
def app_authenticate( environ, start_response ):

    request_body_size = int( environ.get('CONTENT_LENGTH', 0) )
    request_body = environ['wsgi.input'].read(request_body_size)
    fields = urllib.parse.parse_qs( request_body.decode("ascii") )
    fields = { k : v[0] for (k,v) in fields.items() }
    barcode_form = fields['bcode'].upper()
    password = fields['psw']

    # Encode the give password
    sha_instance = hashlib.sha3_384()
    sha_instance.update( password.encode( "utf-8" ) )
    password_hash_user = sha_instance.digest()
    password_hash_user = binascii.b2a_base64( password_hash_user, newline=False )

    # Making an empty list to check how many times a given barcode has been submitted
    hashes_found = []
    with open(SUBJECT_DATA_FILENAME, "r") as f:
        for line in f:
            barcode, timestamp, password_hash, remainder = line.split( ",", 3 )
            if barcode == barcode_form:
                hashes_found.append( password_hash )

    # The barcode is not among the submitted ones or it is wrong
    if len(hashes_found) == 0:

        start_response('200 OK', [('Content-Type', 'text/html')])
        return[ s.encode("utf-8") for s in [
           "<html><head><meta charset=UTF-8></head><body><h3>Barcode unknown</h3>",
           "The barcode you entered (%s) is unknown. " % barcode_form,
           "Maybe you have types it wrongly? Please go back and try again.</body></html>",
           "<html><body><h3>Barcode unbekannt.</h3>",
           "Der Barcode, den Sie eingegeben haben (%s), ist unbekannt. " % barcode_form,
           "Vielleicht haben Sie sich vertippt. ",
           "Bitte gehen Sie zurück und versuchen Sie es noch einmal.</body></html>" ] ]

    # The barcode has been found with multiple passwords
    if len(hashes_found) > 1:

        start_response('200 OK', [('Content-Type', 'text/html')])
        return[ s.encode("utf-8") for s in [
           "<html><head><meta charset=UTF-8></head><body><h3>Multiple passwords</h3>",
           "The barcode you entered (%s) has been found with different passwords." % barcode_form,
           "Please contact us.</body></html>",
           "<html><body><h3>Mehrere Passwörter</h3>",
           "Der Barcode (% s), den Sie eingegeben haben wurde mit unterschiedlichen Passwörtern gefunden." % barcode_form,
           "Bitte kontaktieren Sie uns. </body></html>" ] ]

    # Authenticate the submitted password
    else:
        assert len( hashes_found ) == 1

    # Passwrod is correct and the function for checking the result will be called
        if password_hash_user == list(hashes_found)[0].encode( "utf-8" ):
            result = check_result(barcode_form)
            
            # Negative resutl
            if result == "negative":
                start_response('303 See other', [('Location','/corona-test/test-result-negative-de.html')])
            # Positive result
            elif result == "Barcode not found in the result file":
                    start_response('303 See other', [('Location','/corona-test/no-result-de.html')])
            # No result
            else:
                start_response('303 See other', [('Location','/corona-test/test-result-positive-de.html')])
            
            return[]
    # Password is incorrect
        else:
            start_response('200 OK', [('Content-Type', 'text/html')])
            return[
               b"<html><head><meta charset=UTF-8></head><body><h3>Passwords did not match.</h3>",
               b"Please go back and try again.</body></html>",
               "<html><body><h3>Passwörter stimmen nicht überein.</h3>".encode("utf-8"),
               "Bitte gehen Sie zurück und versuchen Sie es noch einmal.</body></html>".encode("utf-8") ]



# Function to check the result
def check_result( barcode ):
# Reading the results file
    with open(RESULTS_DATA_FILENAME, "r") as f:
        for line in f:
            if ',' in line:
                code, result = line.split(",", 1)
                if code == barcode:
                    return result
            elif barcode in line:
                result = "negative"
                return result
    result = "Barcode not found in the result file"
    return result




def app( environ, start_response ):
    if environ['SCRIPT_NAME'].endswith( "register" ):
        return app_register( environ, start_response )
    elif environ['SCRIPT_NAME'].endswith( "instructions" ):
        return app_instructions( environ, start_response )
    elif environ['SCRIPT_NAME'].endswith( "authenticate" ):
        return app_authenticate( environ, start_response )
    else:
        raise ValueError( "unknown script name")


# BEGIN MAIN FUNCTION

while True:
    load_data()
    a = flup.server.fcgi.WSGIServer( app, bindAddress = ( "127.0.0.1", PORT ), debug=True ).run()
    # a is True if WSGIServer returned due to a SIGHUP, and False,
    # if it was a SIGINT or SIGTERM
    if not a:
        break  # for a SIGHUP, reread config and restart, otherwise exit
