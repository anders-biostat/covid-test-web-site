from app.models import Sample
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    def handle(self, *args, **options):

        for s in Sample.objects.filter( barcode__regex = r"^B\d{5}$" ):
           if s.get_status().status != "PRINTED":
               print( s.barcode, s.access_code, sep="," )
