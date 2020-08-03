#!/usr/bin/python3

import hashlib
import Crypto.PublicKey.RSA

with open( "public.pem", "rb" ) as f:
   public_key = Crypto.PublicKey.RSA.import_key( f.read() )

md5_instance = hashlib.md5()
md5_instance.update( public_key.publickey().exportKey("DER") )
public_key_fingerprint = md5_instance.hexdigest()

print( public_key_fingerprint.encode("ascii") )
