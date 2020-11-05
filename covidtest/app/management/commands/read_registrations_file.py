import datetime, json
from django.core.management.base import BaseCommand, CommandError
from app.models import Sample, RSAKey, Bag
from app.statuses import SampleStatus


class Command(BaseCommand):
    help = 'Reads results file'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='+', type=str)

    def handle(self, *args, **options):
        file = options['file'][0]
        with open(file, 'r') as f:
            j = json.loads(f.read())
            key = RSAKey.objects.get(key_name='default.pem')

            for batch in j['batches']:
                batch_name = batch['name']
                bag, created = Bag.objects.get_or_create(
                    name=batch_name,
                    rsa_key=key,
                )

                for barcode in batch['codes']:
                    sample, created = Sample.objects.get_or_create(
                        barcode=barcode,
                        access_code=barcode,
                        rack='',
                        password_hash='',
                        bag=bag,
                    )
                    if created:
                        sample.events.create(
                            status=SampleStatus.INFO.value,
                            comment='Imported from commandline'
                        )

            for registration in j['registrations']:
                sample = Sample.objects.filter(barcode=registration['barcode']).first()
                if sample is None:
                    print("Sample for registration not in DB: ", registration['barcode'])
                    pass
                else:
                    is_already_registered = sample.registrations.filter(
                        session_key_encrypted=registration['session_key_encrypted']).first()
                    if is_already_registered:
                        print("Already in DB: ", registration['barcode'])
                        pass
                    else:
                        registration_object = sample.registrations.create(
                            name_encrypted=registration['name_encrypted'],
                            address_encrypted=registration['address_encrypted'],
                            contact_encrypted=registration['contact_encrypted'],
                            public_key_fingerprint=registration['public_key_fingerprint'],
                            session_key_encrypted=registration['session_key_encrypted'],
                            aes_instance_iv=registration['aes_instance_iv'],
                        )
                        registration_object.time = datetime.datetime.strptime(registration['time'], '%Y-%m-%d %H:%M:%S')
                        registration_object.save()
                        sample.password_hash = registration['password_hash']
                        sample.save()
                        print("Added: ", registration['barcode'])
