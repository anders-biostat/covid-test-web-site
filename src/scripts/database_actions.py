import arrow
from bson.codec_options import CodecOptions
import pytz
from .statuses import SampleStatus

timezone = pytz.timezone('Europe/Berlin')

def update_status(db, barcode, status, rack=None):
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
            if 'status' in last_result and last_result['status'] == status.value:
                update = False

    status_doc = {
        'status': status.value,
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


def rack_results(db, rack, lamp_positive, lamp_inconclusive):
    wrong_status_sequence = []

    rack = rack.upper().strip()
    rack_samples = db['samples'].find({'rack': rack})

    if rack_samples.count() == 0:
        return None


    if rack_samples is not None:
        for sample in rack_samples:
            sample_status_new = SampleStatus.LAMPPOS.value
            if sample['_id'] in lamp_inconclusive:
                sample_status_new = SampleStatus.LAMPINC.value
            if sample['_id'] in lamp_positive:
                sample_status_new = SampleStatus.LAMPPOS.value

            update_items = {
                '$setOnInsert': {'_id': sample['_id'], 'results': []},
                '$set': {'rack': rack},
            }

            db['samples'].update_one(
                {'_id': sample['_id']},
                update_items,
                upsert=True
            )

            update = True
            results = sample['results']
            if len(results) > 0:
                last_result = results[-1]
                if last_result['status'] != SampleStatus.WAIT.value:
                    wrong_status_sequence.append(sample['_id'])
                if 'status' in last_result and last_result['status'] == sample_status_new:
                    update = False

            status_doc = {
                'status': sample_status_new,
                'updated_time': arrow.now().datetime,
                'updated_at': 'rack_results',
            }

            if update:
                db['samples'].update_one(
                    {'_id': sample['_id']},
                    {
                        '$push': {'results': status_doc},
                    },
                    upsert=True
                )

            return wrong_status_sequence