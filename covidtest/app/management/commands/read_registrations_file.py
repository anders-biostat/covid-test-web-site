import datetime
import json

from app.models import Bag, RSAKey, Sample
from app.statuses import SampleStatus
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import make_aware

comment = 'Imported from "papagei" via "read_registrations_file"'


class Command(BaseCommand):
    help = "Reads results file"

    def add_arguments(self, parser):
        parser.add_argument("file", nargs="+", type=str)

    def handle(self, *args, **options):
        file = options["file"][0]
        with open(file, "r") as f:
            j = json.loads(f.read())
            key = RSAKey.objects.get(key_name="default.pem")

            for batch in j["batches"]:
                batch_name = batch["name"]
                bag, created = Bag.objects.get_or_create(
                    name=batch_name,
                    rsa_key=key,
                )

                for barcode in batch["codes"]:
                    sample = Sample.objects.filter(
                        barcode=barcode,
                        access_code=barcode,
                    ).first()

                    if not sample:
                        sample = Sample.objects.create(
                            barcode=barcode,
                            access_code=barcode,
                            rack="",
                            password_hash="",
                            bag=bag,
                        )
                        sample.events.create(status=SampleStatus.INFO.value, comment=comment)

            not_in_db = []
            already_registered = []
            added_registration = []
            for registration in j["registrations"]:
                sample = Sample.objects.filter(barcode=registration["barcode"]).first()
                if sample is None:
                    not_in_db.append(registration["barcode"])
                else:
                    is_already_registered = sample.registrations.filter(
                        session_key_encrypted=registration["session_key_encrypted"]
                    ).first()
                    if is_already_registered:
                        already_registered.append(registration["barcode"])
                    else:
                        registration_object = sample.registrations.create(
                            name_encrypted=registration["name_encrypted"],
                            address_encrypted=registration["address_encrypted"],
                            contact_encrypted=registration["contact_encrypted"],
                            public_key_fingerprint=registration["public_key_fingerprint"],
                            session_key_encrypted=registration["session_key_encrypted"],
                            aes_instance_iv=registration["aes_instance_iv"],
                        )
                        registration_object.time = make_aware(
                            datetime.datetime.strptime(registration["time"], "%Y-%m-%d %H:%M:%S")
                        )
                        registration_object.save()
                        sample.password_hash = registration["password_hash"]
                        sample.save()
                        added_registration.append(registration["barcode"])

            print("Samples for registration not in DB: ", not_in_db)
            print("Already registered: ", already_registered)
            print("Added registration: ", already_registered)
            print()

            print("Adding results:")

            updated_status = []
            for sample in Sample.objects.all():
                if sample.get_latest_external_status() is None:
                    sample.events.create(status="PRINTED", comment=comment)
                    updated_status.append(sample.barcode)
            print('Updated status "printed: " ', updated_status)

            not_in_db = []
            added_result = []
            for result in j["results"]:
                sample = Sample.objects.filter(barcode=result["barcode"]).first()
                if sample is None:
                    not_in_db.append(result["barcode"])
                else:
                    last_event = sample.events.last()
                    if not last_event:
                        print("Last event not found", result["barcode"])
                    else:
                        event, created = sample.events.get_or_create(status=result["result"], comment=comment)
                        if created:
                            added_result.append(result["barcode"])
            print("Result added ... ", added_result)
            print("Sample not found for result ", not_in_db)
