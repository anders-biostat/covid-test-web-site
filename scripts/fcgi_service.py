#!/usr/bin/python3

import sys, traceback, time, hashlib, binascii, signal
import cgi, flup.server.fcgi 
import Crypto.PublicKey.RSA, Crypto.Cipher.PKCS1_OAEP

#SOCKET = "../etc/fcgi.sock"
PORT = 31234

SUBJECT_DATA_FILENAME = "../data/subjects.csv"
PUBLIC_KEY_FILENAME = "../data/public.pem"
INSTRUCTIONS_HTML_FILENAME = "../static/instruction-de.html"


def load_data():
    # This function loads all the data. It is called once at the beginning
    # and also, when SIGHUP is issued to the process in order to trigger
    # a reload.
    # It sets the following global variables
    global rsa_instance

    # Read public key for encryption of contact information
    with open( PUBLIC_KEY_FILENAME, "rb" ) as f:
       public_key = Crypto.PublicKey.RSA.import_key( f.read() )
    rsa_instance = Crypto.Cipher.PKCS1_OAEP.new( public_key )

    # Get fingerprint of public key
    md5_instance = hashlib.md5()
    md5_instance.update( public_key.publickey().exportKey("DER") )
    rsa_instance.public_key_fingerprint = md5_instance.hexdigest().encode("ascii")


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

    fields = cgi.parse_qs(environ['QUERY_STRING'])

    if fields['psw'][0] != fields['psw-repeat'][0]:
        start_response('200 OK', [('Content-Type', 'text/html')])
        return[ 
           b"<html><body><h3>Passwords did not match.</h3>",
           b"Please go back and try again.</body></html>",
           "<html><body><h3>Passwörter stimmen nicht überein.</h3>".encode("utf-8"),
           "Bitte gehen Sie zurück und versuchen Sie es noch einmal.</body></html>".encode("utf-8") ]

    else:

        # MISSING HERE: Check that Barcode is sane

        line = encode_subject_data( fields['bcode'][0], fields['name'][0], fields['address'][0],
            fields['contact'][0], fields['psw'][0] )
        
        with open( SUBJECT_DATA_FILENAME, "a" ) as f:
            f.write( line ) 

        start_response( '303 See other', [('Location', '/covid-test/fcgi-instructions?code=' + \
            fields['bcode'][0] )] )
        return []
        

def app_instructions( environ, start_response ):

    fields = cgi.parse_qs(environ['QUERY_STRING'])

    start_response('200 OK', [('Content-Type', 'text/html')])

    lines = []
    with open( INSTRUCTIONS_HTML_FILENAME, "rb" ) as f:
        for line in f:
            if line.find( b"@@REPLACE_WITH_INSTRUCTIONS" ) >= 0:
               lines.append( b"<p>INSTRUCTIONS GO HERE for CODE %s</p>" % 
                  fields['code'][0].encode("utf-8") )
            else:
                lines.append( line )
    return lines


def app( environ, start_response ):
    if environ['SCRIPT_NAME'].endswith( "register" ):
        return app_register( environ, start_response ) 
    elif environ['SCRIPT_NAME'].endswith( "instructions" ):
        return app_instructions( environ, start_response ) 
    else:
        raise ValueError( "unknown script name")


# BEGIN MAIN FUNCTION

while True:
    load_data()
    try:
        a = flup.server.fcgi.WSGIServer( app, bindAddress = ( "127.0.0.1", PORT ), debug=True ).run()
    except:
        print( "ERROR" )
    # a is True if WSGIServer returned due to a SIGHUP, and False, 
    # if it was a SIGINT or SIGTERM
    if not a:
        break  # for a SIGHUP, reread config and restart, otherwise exit

