#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback, time, hashlib, binascii, signal, re
import urllib.parse, flup.server.fcgi
import Crypto.PublicKey.RSA, Crypto.Cipher.PKCS1_OAEP

import load_codes

# file names
SUBJECT_DATA_FILENAME = "../data/subjects.csv"
PUBLIC_KEY_FILENAME = "../data/public.pem"
HTML_DIRS = "../static/"
RESULTS_FILENAME = "../data/results.txt"
NGINX_CONF_FILENAME = "../etc/covid-test.nginx-site-config"


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
	lang = re.compile("(\\w*)/fcgi").search( environ.get('SCRIPT_NAME', 0) )[1]
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
		start_response('303 See Other', [('Location', 'password-not-matched.html')])
		return []

	elif barcode not in codes2events:
		return serve_file( environ, start_response,
			"barcode-unknown.html", { "@@BARCODE@@" : "<b>%s</b>" % (barcode) } )

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
			"<strong>%s</strong> \n <p><small>[Code '%s' of Event '%s']</small></p>\n" % (
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
		return serve_file( environ, start_response,
			"barcode-unknown.html", { "@@BARCODE@@" : "%s" % (barcode) } )

	# Find barcode registration
	hashes_found = set()
	with open( SUBJECT_DATA_FILENAME ) as f:
		for line in f:
			barcode, timestamp, password_hash, remainder = line.split( ",", 3 )
			if barcode == form_barcode.upper():
				hashes_found.add( password_hash )

	if len( hashes_found ) == 0:
		return serve_file( environ, start_response,
			"barcode-not-registered.html", { "@@BARCODE@@" : "%s" % (barcode) } )

	if len( hashes_found ) > 1:
		return serve_file( environ, start_response,
			"multiple-registeration.html", { "@@BARCODE@@" : "%s" % (barcode) } )

	assert len( hashes_found ) == 1

	# Hash entered password
	sha_instance = hashlib.sha3_384()
	sha_instance.update( form_password.encode( "utf-8" ) )
	encoded_hash_from_form = binascii.b2a_base64( sha_instance.digest(), newline=False )

	if encoded_hash_from_form != list(hashes_found)[0].encode( "ascii" ):
		start_response('303 See Other', [('Location', 'wrong-password.html')])
		return []

	# Check results
	with open( RESULTS_FILENAME ) as f:
		for line in f:
			if line.find(",") >= 0:
				barcode, remainder = line.rstrip().split( ",", 1 )
			else:
				barcode, remainder = line.rstrip(), ""
			if barcode == form_barcode:
				if remainder == "":
					start_response('303 See Other', [('Location', 'test-result-negative.html')])
					return []
				elif remainder.lower().startswith( "pos" ):
					start_response('303 See Other', [('Location', 'test-result-positive.html')])
					return []
				elif remainder.lower().startswith( "inc" ):
					start_response('303 See Other', [('Location', 'to-be-determined.html')])
					return []
				elif remainder.lower().startswith( "failed" ):
					start_response('303 See Other', [('Location', 'test-failed.html')])
					return []
				else:
					start_response('303 See Other', [('Location', 'internal-error.html')])
					return []

	# no result found
	start_response('303 See Other', [('Location', 'no-result.html')])
	return []

def app_get_line( environ, start_response ):
	try:
		request_body_size = int( environ.get('CONTENT_LENGTH', 0) )
	except(ValueError):
		request_body_size = 0

	request_body = environ['wsgi.input'].read(request_body_size)
	fields = urllib.parse.parse_qs( request_body.decode("ascii") )
	fields = { k : v[0] for (k,v) in fields.items() }
	barcode = fields["code"].upper()
	lines = []
	with open(SUBJECT_DATA_FILENAME) as f:
		for line in f:
			if line.startswith(barcode+","):
				lines.append(line)
	start_response('200 OK', [('Content-type','text/plain')])
	return lines



def app( environ, start_response ):
	try:
		if environ['SCRIPT_NAME'].endswith( "register" ):
			return app_register( environ, start_response )
		elif environ['SCRIPT_NAME'].endswith( "instructions" ):
			return app_instructions( environ, start_response )
		elif environ['SCRIPT_NAME'].endswith( "result-query" ):
			return app_result_query( environ, start_response )
		elif environ['SCRIPT_NAME'].endswith( "get-line" ):
			return app_get_line( environ, start_response )
		else:
			raise ValueError( "unknown script name")
	except:
		traceback.print_exc()



# BEGIN MAIN FUNCTION

# Search port number in nginx cofig file:
with open( NGINX_CONF_FILENAME ) as f:
	for l in f:
		m = re.search( r"fastcgi_pass\s+127.0.0.1\s*:\s*(\d+)", l )
		if m:
			port = int(m.group(1))
			break
if port is None:
	sys.stderr.write( "Cannot determine port number.\n" )
	sys.exit(1)
print( "Listening on port", port )

while True:
	load_data()
	a = flup.server.fcgi.WSGIServer( app, bindAddress = ( "127.0.0.1", port ) ).run()
	# a is True if WSGIServer returned due to a SIGHUP, and False,
	# if it was a SIGINT or SIGTERM
	if not a:
		break  # for a SIGHUP, reread config and restart, otherwise exit
