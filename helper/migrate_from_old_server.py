import os
import requests

api_url = 'http://127.0.0.1:8000/api/'
auth = ( 'test', 'tomate123' )


def upload_item( table, name, data ):
	print( "Uploading object %s to table %s:" % ( table, name ), end=" ")
	r = requests.post( api_url + table + '/', auth = auth, data = data ) 

	if r.status_code == 201:
		id = r.json()['id']
		print( "Ok (Table ID: %d)" % id )
		return( id )
	else:
		print( "Error -- Status ", r.status_code )
		print( r.content )
		sys.exit(1)

def upload_item( table, name, id ):
	# ...
	return data

def update_item( table, name, data ):
	# ...
	return id

def upload_public_key():

	with open( "data/public.pem" ) as f:
	   public_key = ''.join( f.readlines() )

	key_id = upload_item( "rsakeys", "public key", 
		 {  'key_name': 'key from old sever', 
			'comment': 'This is the key last used on papagei.', 
			'public_key': public_key } )

	return key_id 


def upload_bags( key_id ):

	code_batches = {}
	for filename in os.listdir( "data/code_batches" ):
		bagname = filename.replace( ".txt", "" ).replace( ".lst", "" )
		with open( "data/code_batches/" + filename ) as f:
			code_batches[ bagname ] = [ a.strip() for a in f.readlines() ]

	bag_ids = {}
	for b in code_batches:
		bag_ids[ b ] = upload_item( "bags", b, {
			'name': b, 
			'comment': 'transferred from papagei', 
			'rsa_key': key_id } )

	return code_batches, bag_ids


def upload_samples( code_batches, bag_ids ):

	sample_ids = {}
	for bag in code_batches:
		for sample_barcode in code_batches[ bag ]:
			sample_ids[ sample_barcode ] = \
				upload_item( "samples", sample_barcode, {
		    		"barcode": sample_barcode,
	        		"access_code": sample_barcode,
	        		"bag": bag_ids[ bag ] } )

	return sample_ids


def upload_registrations():

	with open( "data/subjects.csv" ) as f:
		for line in f:

			barcode, time, password_hash, public_key_fingerprint, \
				encrypted_session_key, aes_instance_iv, encrypted_name, \
				encrypted_address, encrypted_contact = line.split(",")
			
			reg_id = upload_item( "registrations", sample_barcode, {
				"sample": sample_ids[ barcode ],
		    	"name_encrypted": name_encrypted,
		    	"address_encrypted": address_encrypted,
		    	"contact_encrypted": contact_encrypted,
		    	"public_key_fingerprint": public_key_fingerprint,
		    	"session_key_encrypted": encrypted_session_key,
		    	"aes_instance_iv": aes_instance_iv } )

			upload_item( "events", "registration event for " + sample_barcode, {
    			"status": "INFO",
    			"comment": "contact data registered (on old 'papagei' server)" } )


def upload_passwords():

	passwords = defaultdict( set )

	with open( "data/subjects.csv" ) as f:
		for line in f:

			barcode, time, password_hash, public_key_fingerprint, \
				encrypted_session_key, aes_instance_iv, encrypted_name, \
				encrypted_address, encrypted_contact = line.split(",")

			passwords[ barcode ].add( passwords )

	for barcode in passwords:

		if len( passwords[ barcode ] ) >= 1:
			sample_data = download_item( "samples", barcode, sample_ids[ barcode ] )
			if len( passwords[ barcode ] ) == 1:
				sample_data[ "password_hash" ] = list( passwords[ barcode ] )[0]
			else:
				sample_data[ "password_hash" ] = "__no_access__"
				update_item( sample_data )


def upload_results():

	# Go through data/results.txt
	# Map statuses acording to following table [TO DO]
	# upload

key_id = upload_public_key()
code_batches, bag_ids = upload_bags( key_id )
sample_ids = upload_samples( code_batches, bag_ids )
upload_registrations()
upload_samples()
upload_passwords()
upload_results()
