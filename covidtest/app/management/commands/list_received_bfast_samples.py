from app.models import Sample
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    def handle(self, *args, **options):

        for s in Sample.objects.filter( barcode__regex = r"^B\d{5}$" ):
           if s.get_latest_external_status() is not None and s.get_latest_external_status().status != "PRINTED":
               print( s.barcode, s.access_code, sep="," )
