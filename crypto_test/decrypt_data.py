#!/usr/bin/python3

# Data decryption tool for LAMP data

PRIVATE_KEY_PEM_FILE = "private.pem"
DATA_FILE = "test.csv"


import sys, getpass, binascii
import Crypto.PublicKey.RSA, Crypto.Random, Crypto.Cipher.AES, Crypto.Cipher.PKCS1_OAEP

# Get private RSA key and initiate PKCS1 decoder

# Load key file
try:
	with open( PRIVATE_KEY_PEM_FILE, "rb" ) as f:
		protected_private_key = f.read()
except:
	sys.stderr.write( "ERROR: Failed to read private key file 'private.pem'.\n\n")
	sys.stderr.write( str( sys.exc_info()[1] ) + "\n" )
	sys.exit( 1 )

# Get key passphrase
passphrase = getpass.getpass( "Enter private-key passphrase: " )
private_key = Crypto.PublicKey.RSA.import_key( protected_private_key, passphrase=passphrase )
pkcs1_instance = Crypto.Cipher.PKCS1_OAEP.new( private_key )


# TO DO: Find a way


with open( DATA_FILE ) as f:
	for line in f:

		# Get fields from line in CSV file
		fields = line.split( "," )

		# Barcode already is in first field, in plain ASCII, remainder has to go through Base-64 decoding 
		sample_barcode = fields[0]
		hashed_user_password, encrypted_subject_data, encrypted_session_key, aes_iv = \
		   ( binascii.a2b_base64(x) for x in fields[1:] )

		# Decode session key for line, use it to instantiate AES decoder
		aes_instance = Crypto.Cipher.AES.new( 
			pkcs1_instance.decrypt( encrypted_session_key ), 
			Crypto.Cipher.AES.MODE_CBC, 
			iv=aes_iv )   

		print( sample_barcode + ":", aes_instance.decrypt( encrypted_subject_data ).decode() )
