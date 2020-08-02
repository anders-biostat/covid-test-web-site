#!/usr/bin/python3

# Let's assume a user has entered this data on the result query web form
form_data = {
	"barcode": "ABCDEF",
	"password": "ErikasPW"
}

# Here is how to check whether the password is valid

import binascii, hashlib

hashes_found = set()

with open( "test.csv" ) as f:
	for line in f: 
		barcode, password_hash, remainder = line.split( ",", 2 )
		if barcode == form_data["barcode"].upper():
			hashes_found.add( password_hash )

if len( hashes_found ) == 0:
	print( "Barcode not found.")
elif len( hashes_found ) > 1:
	print( "Barcode has been found several times, with different passwords. Please contact the admins." )
else:
	assert len( hashes_found ) == 1

	sha_instance = hashlib.sha3_384()
	sha_instance.update( form_data["password"].encode( "utf-8" ) )
	encoded_hash_from_form = binascii.b2a_base64( sha_instance.digest(), newline=False )
	
	if encoded_hash_from_form == list(hashes_found)[0].encode( "ascii" ):
		print( "Password correct." )
	else:
		print( "Password wrong." )
