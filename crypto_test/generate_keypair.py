#!/usr/bin/python3

import Crypto.PublicKey.RSA

key = Crypto.PublicKey.RSA.generate( 3072 )

file_out = open( "private.pem", "wb" )
file_out.write( key.export_key( passphrase="secret" ) )
file_out.close( )

file_out = open( "public.pem", "wb" )
file_out.write( key.publickey().export_key() )
file_out.close()