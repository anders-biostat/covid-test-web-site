#!/usr/bin/python3

import sys, collections
import yaml

Event = collections.namedtuple( "Event", [ "name", "instructions" ] )

Batch = collections.namedtuple("Batch", ["name", "batch_file"])

def load_codes():

	# read yaml
	with open( "../data/events.yaml" ) as f:
		yaml_content = list( yaml.safe_load_all( f.read() ) )

	# Check data
	expected_keys = ( 'name', 'instructions', 'batches' )
	errors = []
	for i in range(len(yaml_content)):
		for key in expected_keys:
			if key not in yaml_content[i].keys():
				errors.append( "Event %i is missing key '%s'" % (i+1, key ) )
		for key in yaml_content[i].keys():
			if key not in expected_keys:
				errors.append( "Event %i has unexpected key '%s'" % (i+1, key ) )
	if len(errors) > 0:
		for e in errors:
			sys.stderr.write( e + "\n" )
		raise ValueError( "YAML syntax error." )

	codes2events = {}

	for record in yaml_content:
		ev = Event( record["name"], record["instructions"] )
		for batch in record["batches"]:
			with( open( "../data/code_batches/" + batch ) ) as f:
				for line in f:
					code = line.rstrip()
					if code in codes2events:
						raise ValueError( "Duplicate code: " + code )
					codes2events[ code ] = ev

	return( codes2events )

def batch_finder(bcode):
	code2batch = {}
	btch=[]
	with open("../data/events.yaml") as f:
		yaml_content = list( yaml.safe_load_all( f.read() ) )

	for record in yaml_content:
		for batch in record["batches"]:
			with ( open("../data/code_batches/" + batch ) ) as f:
				for line in f:
					if bcode in line:
						btch.append(Batch( racord["name"], batch))
	code2batch[bcode] = btch

	if len(btch) > 1:
		print("Warning! there are %i batches assigned to the barcode" %i)
	elif len(btch) == 0:
		print("No batch is assigned to this barcode")
	return( code2batch )			


if __name__ == "__main__":

	try:
		codes2events = load_codes()
	except:
		sys.stderr.write( "Error reading codes files:\n" )
		sys.stderr.write( str(sys.exc_info()[1]) + "\n\n" )
		sys.exit(1)

	print( "Loaded %i codes assigned to %i events." %
		( len( codes2events ), len(set( codes2events.values() )) ) )
