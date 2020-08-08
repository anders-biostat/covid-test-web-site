#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback, time, hashlib, binascii, signal, re
import urllib.parse, flup.server.fcgi
import Crypto.PublicKey.RSA, Crypto.Cipher.PKCS1_OAEP

import load_codes

#SOCKET = "../etc/fcgi.sock"
PORT = 31234

SUBJECT_DATA_FILENAME = "../data/subjects.csv"
PUBLIC_KEY_FILENAME = "../data/public.pem"
HTML_DIRS = "../static/"
RESULTS_FILENAME = "../data/results.txt"


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


def serve_file( environ, start_response, filename, replacements ):

	start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
	lang = re.compile("(\w*)/fcgi").search( "/corona-test/de/fcgi-instructions" )[1]
	lines = []
	with open( HTML_DIRS + "/" + lang + "/" + filename, encoding="utf-8" ) as f:
		for line in f:
			for r in replacements:
				line = line.replace( r, replacements[r] )
			lines.append( line.encode( "utf-8" ) )
	return lines


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
		   b"<html><body><h3>Passwords did not match.</h3>",
		   b"Please go back and try again.</body></html>",
		   "<html><body><h3>Passwörter stimmen nicht überein.</h3>".encode("utf-8"),
		   "Bitte gehen Sie zurück und versuchen Sie es noch einmal.</body></html>".encode("utf-8") ]

	elif barcode not in codes2events:

		start_response('200 OK', [('Content-Type', 'text/html')])
		return[ s.encode("utf-8") for s in [
		   "<html><body><h3>Barcode unknown</h3>",
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

	fields = urllib.parse.parse_qs( environ['QUERY_STRING'] )
	barcode = fields['code'][0]

	return serve_file( environ, start_response, 
		"instructions.html", { "@@INSTRUCTIONS@@" :
			"%s \n <p><small>[Code '%s' of Event '%s']</small></p>\n" % ( 
				codes2events[ barcode ].instructions, 
				barcode, 
				codes2events[barcode].name ) } )


def app_result_query( environ, start_response ):

	# Read POST data
	request_body_size = int( environ.get('CONTENT_LENGTH', 0) )
	request_body = environ['wsgi.input'].read(request_body_size)
	fields = urllib.parse.parse_qs( request_body.decode("ascii") )
	fields = { k : v[0] for (k,v) in fields.items() }

	form_barcode = fields['bcode'].upper()
	form_password = fields['psw']

	# Check if barcode exists
	if form_barcode not in codes2events:
		start_response('200 OK', [('Content-Type', 'text/html')])
		return [
			"<h2>Unknown barcode.</h2>",
			"This barcode does not exist. Maybe you have mistyped it?",
			"<h2>Unbekannter Barcode</h2>",
			"Dieser Barcode existiert nicht. Vielleicht haben Sie sich vertippt?"
		]
   
	# Find barcode registration
	hashes_found = set()
	with open( SUBJECT_DATA_FILENAME ) as f:
		for line in f: 
			barcode, timestamp, password_hash, remainder = line.split( ",", 3 )
			if barcode == form_barcode.upper():
				hashes_found.add( password_hash )

	if len( hashes_found ) == 0:
		start_response('200 OK', [('Content-Type', 'text/html')])
		return [
			"<h2>Unregistered barcode.</h2>",
			"This barcode has not yet been registered. You have to fill out the ",
			'<a href="consent-de.html">registration form</a> before you can check the result.',
			"<h2>Unregistrierter Barcode.</h2>",
			"Für diesen Barcode wurden noch keine Kontakt-Daten eingetragen. Sie müssen erst ",
			'<a href="constent-de.html">das Registrierungs-Formular</a> ausfüllen, bevor Sie ',
			'das Ergebnis abfragen können.' ]

	if len( hashes_found ) > 1:
		start_response('200 OK', [('Content-Type', 'text/html')])
		return [
			"<h2>Multiply registered barcode.</h2>",
			"For this barcode, the registration form has been filled out multiple times, with ",
			"different passwords. Please contact us (s.anders@zmbh.uni-heidelberg.de) to sort this out."
			"<h2>Mehrfach registrierter Barcode.</h2>",
			"Für diesen Barcode wurde das Registrier-Formular mehrmals ausgefüllt, mit verschiedenen ",
			"Passwörtern. Bitte wenden Sie sich an uns (s.anders@zmbh.uni-heidelberg.de), um das ",
			"zu klären." ]

	assert len( hashes_found ) == 1

	# Hash entered password
	sha_instance = hashlib.sha3_384()
	sha_instance.update( form_password.encode( "utf-8" ) )
	encoded_hash_from_form = binascii.b2a_base64( sha_instance.digest(), newline=False )
	
	if encoded_hash_from_form != list(hashes_found)[0].encode( "ascii" ):
		start_response('200 OK', [('Content-Type', 'text/html')])
		return [
			"<h2>Wrong password.</h2>",
			"The password you entered is not the same as the one that you have set you registered this barcode. ",
			"Please go back und try again. ",
			"<h2>Passwort falsch</h2>",
			"Das Passwort stimmt nicht mit dem überein, dass Sie beim Registrieren der Barcodes ",
			"gewählt haben. Bitte gehen Sie zurück zur vorigen Seite und versuchen Sie es noch einmal." ]

	# Check results
	with open( RESULTS_FILENAME ) as f:
		for line in f:
			if line.find(",") >= 0:
				barcode, remainder = line.rstrip().split( ",", 1 )
			else:
				barcode, remainder = line.rstrip(), ""
			if barcode == form_barcode:
				if remainder == "":
					start_response('303 See Other', [('Location', 'test-result-negative-de.html')])
					return []
				elif remainder.lower().startswith( "pos" ):
					start_response('303 See Other', [('Location', 'test-result-positive-de.html')])
					return []
				else:
					start_response('200 OK', [('Content-Type', 'text/html')])
					return [
						"<h2>Internal error.</h2>",
						"The encoding of your result is erroneous. ",
						"Please contact us to inquire (s.anders@zmbh.uni-heidelberg.de).",
						"<h2>Interner Fehler.</h2>",
						"Das Ergebnis ihres Tests ist fehlerhaft gespeichert. ",
						"Bitte kontaktieren Sie uns (s.anders@zmbh.uni-heidelberg.de)." ]

	# no result found
	start_response('200 OK', [('Content-Type', 'text/html')])
	return [
		"<h2>Result not ready yet.</h2>",
		"The result for this sample is not yet available. Please try again later or tomorrow. ",
		"(If several days have already passed since you handed in your sample, it might have gotten ",
		"lost. Please contact us (robinburk1411@googlemail.com) to inquire.)",
		"<h2>Ergebnis liegt noch nicht vor</h2>",
		"Für diese Probe liegt noch kein Ergebnis vor. Bitte versuchen Sie es später noch mal. ",
		"(Falls es bereits einige Tage her ist, dass Sie die Probe abgegeben haben, ist sie vielleicht ",
		"verloren gegangen. Fragen Sie bitte bei uns (robinburk1411@googlemail.com) nach." ]




def app( environ, start_response ):
	try:
		if environ['SCRIPT_NAME'].endswith( "register" ):
			return app_register( environ, start_response ) 
		elif environ['SCRIPT_NAME'].endswith( "instructions" ):
			return app_instructions( environ, start_response ) 
		elif environ['SCRIPT_NAME'].endswith( "result-query" ):
			return app_result_query( environ, start_response ) 
		else:
			raise ValueError( "unknown script name")
	except:
		traceback.print_exc()



# BEGIN MAIN FUNCTION

while True:
	load_data()
	a = flup.server.fcgi.WSGIServer( app, bindAddress = ( "127.0.0.1", PORT ) ).run()
	# a is True if WSGIServer returned due to a SIGHUP, and False, 
	# if it was a SIGINT or SIGTERM
	if not a:
		break  # for a SIGHUP, reread config and restart, otherwise exit

