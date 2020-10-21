import arrow
from bson.codec_options import CodecOptions
import pytz

timezone = pytz.timezone('Europe/Berlin')

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

def update_status(db, barcode, status, rack=None):
    status = status.upper().strip()
    sample = db['samples'].find_one({'_id': barcode})
    if sample is None:
        return None

    update_items = {
        '$setOnInsert': {'_id': barcode, 'results': []},
    }

    if rack is not None:
        update_items['$set'] = {
            'rack': rack,
        }

    db['samples'].update_one(
        {'_id': barcode},
        update_items,
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

    samples = db['samples'].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=timezone))
    return samples.find_one({'_id': barcode})
