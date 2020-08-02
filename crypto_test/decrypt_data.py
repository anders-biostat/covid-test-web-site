#!/usr/bin/python3

# Data decryption tool for LAMP data

PRIVATE_KEY_PEM_FILE = "private.pem"
DATA_FILE = "test.csv"

import sys, getpass, binascii

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP

# Load key file
try:
	with open( PRIVATE_KEY_PEM_FILE, "rb" ) as f:
		protected_private_key = f.read()
except:
	sys.stderr.write( "ERROR: Failed to read private key file 'private.pem'.\n\n")
	sys.stderr.write( str( sys.exc_info()[1] ) + "\n" )
	sys.exit( 1 )

# Get key passphrase, 
passphrase = getpass.getpass( "Enter private-key passphrase: " )

# instantiate RSA
try:
	private_key = RSA.import_key( protected_private_key, passphrase=passphrase )
except:
	sys.stderr.write( "ERROR: Failed to use private key. Maybe the passphrase was wrong?\n\n")
	sys.exit( 1 )

pkcs1_instance = PKCS1_OAEP.new( private_key )

with open( DATA_FILE ) as f:
	for line in f:

		# Get fields from line in CSV file
		fields = line.split( ",",  )

		# First two fields (barcode and time stamp) is plain ASCII, remainder has to go through Base-64 decoding 
		for i in range( 2, len(fields) ):
		   fields[i] = binascii.a2b_base64( fields[i] )

		# unpack line
		sample_barcode, timestamp, pw_hash, session_key, aes_iv = fields[:5] 
		subject_data = fields[5:]   

		# Decode session key for line, use it to instantiate AES decoder
		aes_instance = AES.new( 
			pkcs1_instance.decrypt( session_key ), 
			AES.MODE_CBC, 
			iv=aes_iv )  

		# Decrypt subject data
		for i in range( len(subject_data) ):
			subject_data[i] = aes_instance.decrypt( subject_data[i] )

		print( "\n" + sample_barcode + ": " + timestamp )
		for s in subject_data:
			print( "  ", s.decode() )
