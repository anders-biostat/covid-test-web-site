from app.models import *

class Command(BaseCommand):

    def handle(self, *args, **options):
        from app.models import *

        for s in Sample.objects.filter( barcode__regex = r"^B\d{5}$" ):
           if s.get_status().status != "PRINTED":
               print( s.barcode, s.access_code, sep="," )
