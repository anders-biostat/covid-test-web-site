#!/usr/bin/python3

# Data decryption tool for LAMP-test regstration data

import sys, getpass, binascii, hashlib

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP

#check if the path is provided
if len(sys.argv) != 2:
	sys.stderr.write( "Usage: python key_fingerprint.py <pem-file>\n\n")
	sys.exit( 1 )
try:
    open( sys.argv[1] ).close()
except:
    sys.stderr.write( "ERROR: Failed to open data file.\n\n")
    sys.stderr.write( str( sys.exc_info()[1] ) + "\n" )
    sys.exit( 1 )

with open( sys.argv[1] ) as f:
    line = f.readline()
    if "PRIVATE" in line:
        f.close()
        PRIVATE_KEY_PEM_FILE = sys.argv[1]
        # Get key passphrase,
        passphrase = getpass.getpass( "Enter private-key passphrase: " )

        # Load key file
        try:
        	with open( PRIVATE_KEY_PEM_FILE, "rb" ) as f:
        		protected_private_key = f.read()
        except:
        	sys.stderr.write( "ERROR: Failed to read private key file 'private.pem'.\n\n")
        	sys.stderr.write( str( sys.exc_info()[1] ) + "\n" )
        	sys.exit(1)

        private_key = RSA.import_key(protected_private_key, passphrase=passphrase )
        rsa_instance = PKCS1_OAEP.new( private_key )

        # Get fingerprint
        md5_instance = hashlib.md5()
        md5_instance.update( private_key.publickey().exportKey("DER") )
        private_key_fingerprint = md5_instance.hexdigest()

        print( "privater Schlüssel geladen:", private_key_fingerprint )

    elif "PUBLIC" in line:
        f.close()
        PUBLIC_KEY_PEM_FILE = sys.argv[1]

        # Load key file
        try:
            with open( PUBLIC_KEY_PEM_FILE, "rb" ) as f:
                public_key_file = f.read()
        except:
            sys.stderr.write( "ERROR: Failed to read public key file 'public.pem'.\n\n")
            sys.stderr.write( str( sys.exc_info()[1] ) + "\n" )
            sys.exit(1)

        public_key = RSA.import_key(public_key_file)
        rsa_public_instance = PKCS1_OAEP.new( public_key )

        #Get key_fingerprint
        md5_instance_public = hashlib.md5()
        md5_instance_public.update( public_key.publickey().exportKey("DER") )
        public_key_fingerprint = md5_instance_public.hexdigest()

        print( "public Schlüssel geladen:", public_key_fingerprint )
