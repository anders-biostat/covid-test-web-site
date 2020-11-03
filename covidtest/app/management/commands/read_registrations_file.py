import datetime
from django.core.management.base import BaseCommand, CommandError
from app.models import Sample, RSAKey, Bag


class Command(BaseCommand):
    help = 'Reads results file'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='+', type=str)

    def handle(self, *args, **options):
        file = options['file'][0]
        with open(file, 'r') as f:
            for line in f.readlines():
                barcode, time, password_hash, fingerprint, session_key, aes_iv, name, address, contact = line.split(',')

                key = RSAKey.objects.get(key_name='default.pem')
                bag, created = Bag.objects.get_or_create(
                    name='papagei',
                    rsa_key=key,
                )

                sample, created = Sample.objects.get_or_create(
                    barcode=barcode,
                    access_code=barcode,
                    rack='',
                    password_hash=password_hash,
                    bag=bag,
                )

                registration = sample.registrations.filter(session_key_encrypted=session_key).first()

                if registration:
                    print("Already in DB: ", barcode)
                else:
                    registration = sample.registrations.create(
                        name_encrypted=name,
                        address_encrypted=address,
                        contact_encrypted=contact,
                        public_key_fingerprint=fingerprint,
                        session_key_encrypted=session_key,
                        aes_instance_iv=aes_iv,
                    )
                    print("Added: ", barcode)
                registration.time=datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                registration.save()


