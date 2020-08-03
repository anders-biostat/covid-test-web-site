#!/usr/bin/python3

# Data decryption tool for LAMP-test regstration data

PRIVATE_KEY_PEM_FILE = "private.pem"

import sys, getpass, binascii, hashlib

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP


# Check that data file can be opened:
if len(sys.argv) != 2:
	sys.stderr.write( "Usage: python decrypt_data.py <csv-file>\n\n")
	sys.exit( 1 )

try:
	open( sys.argv[1] ).close()
except:
	sys.stderr.write( "ERROR: Failed to open data file.\n\n")
	sys.stderr.write( str( sys.exc_info()[1] ) + "\n" )
	sys.exit( 1 )

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
rsa_instance = PKCS1_OAEP.new( private_key )

# Get fingerprint
md5_instance = hashlib.md5()
md5_instance.update( private_key.publickey().exportKey("DER") )
public_key_fingerprint = md5_instance.hexdigest()

print( "privater Schlüssel geladen:", public_key_fingerprint )

with open( sys.argv[1] ) as f:
	for line in f:

		# Get fields from line in CSV file
		fields = line.split( ",",  )

		# Three fields (barcode, time stamp, fingerprint) are plain ASCII, 
		# the remainder has to go through Base-64 decoding 
		for i in range( len(fields) ):
			if i not in ( 0, 1, 3 ):
				fields[i] = binascii.a2b_base64( fields[i] )

		# unpack line
		sample_barcode, timestamp, pw_hash, fingerprint, session_key, aes_iv = fields[:6] 
		subject_data = fields[6:]   

		# Print open information
		print( "\n" + sample_barcode + ": " + timestamp )

		#Check whether we have the right key
		if fingerprint == public_key_fingerprint:

			# Decode session key for line, use it to instantiate AES decoder
			aes_instance = AES.new( 
				rsa_instance.decrypt( session_key ), 
				AES.MODE_CBC, 
				iv=aes_iv )  

			# Decrypt subject data
			for i in range( len(subject_data) ):
				subject_data[i] = aes_instance.decrypt( subject_data[i] )

			for s in subject_data:
				print( "  ", s.decode() )

		else:

			print("  kann nicht entschlüsselt werden" )
			print("  (benötigter Schlüssel:", fingerprint, ")" )
