#!/usr/bin/python3

import arrow
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

STATUS_DICT = {
    'PRINTED': 'PRINTED',
    'WAIT': 'WAIT',
    'LAMPPOS': 'LAMPPOS',
    'LAMPINC': 'LAMPINC',
    'NEG': 'NEG',
    'PCRPOS': 'PCRPOS',
    'PCRNEG': 'PCRNEG',
    'UNDEF': 'UNDEF',
    '': 'WAIT',
}


def read_results(filepath):
    with open(filepath) as f:
        for line in tqdm(f):
            if line.strip() != '':  # Blank lines
                result = line.replace(";", ",").split(",")
                if len(result) >= 1:
                    barcode = result[0]
                    status = ""
                if len(result) >= 2:
                    barcode = result[0]
                    status = result[1]

                barcode = barcode.strip().upper()
                status = status.strip().upper()

                if status in STATUS_DICT.keys():
                    db['samples'].update_one(
                        {'_id': barcode},
                        {
                            '$setOnInsert': {'_id': barcode, 'results': []},
                        },
                        upsert=True
                    )

                    # Check for last status
                    update = True
                    sample = db['samples'].find_one({'_id': barcode})
                    if sample is not None and 'results' in sample:
                        results = sample['results']
                        if len(results) > 0:
                            last_result = results[-1]
                            if 'status' in last_result and last_result['status'] == STATUS_DICT[status]:
                                update = False

                    status_doc = {
                        'status': STATUS_DICT[status],
                        'updated_time': arrow.now().datetime,
                    }

                    if update:
                        db['samples'].update_one(
                            {'_id': barcode},
                            {
                                '$push': {'results': status_doc},
                            },
                            upsert=True
                        )
                else:
                    raise ValueError("Status code not known:", status)


if __name__ == "__main__":
    try:
        read_results("../../data/result_test.csv")
    except:
        sys.stderr.write("Error reading codes files:\n")
        sys.stderr.write(str(sys.exc_info()[1]) + "\n\n")
        sys.exit(1)
