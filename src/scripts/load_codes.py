#!/usr/bin/python3


import collections
import sys
import yaml
from tqdm import tqdm
from pymongo import MongoClient
from envparse import env

# Reading the Environemt-Variables from .env file
env.read_envfile()


client = MongoClient()
DATABASE = env("DATABASE", cast=str, default="covidtest-test")
db = client[DATABASE]

def read_batch(filepath, batch, record):
    with(open(filepath)) as f:
        print('Reading batch:', batch)
        for line in tqdm(f):
            barcode = line.strip()
            sample = {
                'barcode': barcode.strip(),
                'batch_filename': batch.strip(),
                'batch': batch.strip().replace("batch_", "").replace(".lst", ""),
                'event_name': record["name"].strip(),
                'event_instructions': record["instructions"].strip(),
            }
            db['samples'].update_one({'_id': barcode}, {'$set': sample}, upsert=True)


def load_codes():
    # read yaml
    with open( "../../data/events.yaml" ) as f:
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

    for record in yaml_content[:1]:
        for batch in record["batches"][:1]:
            batch_record = db['batches'].find_one({'_id': batch})
            if batch_record is None:
                read_batch("../../data/code_batches/" + batch, batch, record)
                db['batches'].update_one({'_id': batch}, {'$set': {'read': True}}, upsert=True)
            else:
                if 'read' in batch_record and batch_record['read'] == True:
                    pass
                else:
                    read_batch("../../data/code_batches/" + batch, batch, record)
                    db['batches'].update_one({'_id': batch}, {'$set': {'read': True}}, upsert=True)


if __name__ == "__main__":

    try:
        load_codes()
    except:
        sys.stderr.write( "Error reading codes files:\n" )
        sys.stderr.write( str(sys.exc_info()[1]) + "\n\n" )
        sys.exit(1)
