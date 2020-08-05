#!/usr/bin/python3

import sys, getpass
import Crypto.PublicKey.RSA

passphrase = getpass.getpass( "Enter passphrase to protect secret key: " )
passphrase_repeat = getpass.getpass( "Enter passphrase again: " )

if passphrase != passphrase_repeat:
	sys.stderr.write( "Passphrases differ. Aborting." )
	sys.exit( 1 )

sys.stderr.write( "Generating key pair.\n" )
key = Crypto.PublicKey.RSA.generate( 3072 )

with open( "private.pem", "wb" ) as f:
   f.write( key.export_key( passphrase=passphrase ) )

with open( "public.pem", "wb" ) as f:
	f.write( key.publickey().export_key() )

sys.stderr.write( "Key pair generated and saved in 'public.pem' and 'private.pem'.\n" )