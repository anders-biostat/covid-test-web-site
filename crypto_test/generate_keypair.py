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

file_out = open( "private.pem", "wb" )
file_out.write( key.export_key( passphrase=passphrase ) )
file_out.close( )

file_out = open( "public.pem", "wb" )
file_out.write( key.publickey().export_key() )
file_out.close()

sys.stderr.write( "Key pair generated and saved in 'public.pem' and 'private.pem'.\n" )