import sys
from django.core.management.base import BaseCommand
from app.models import Sample
from app.statuses import SampleStatus

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('status', help="status word to set",
             choices=[a.name for a in SampleStatus])
        parser.add_argument('barcode_list', type=str, help="text file with barcodes, one barcode per line (or '-' for stdin)" )
        parser.add_argument('--comment', type=str, default="", help="comment to be stored in Event records", dest='comment')
        parser.add_argument('--rack', type=str, default="", help="set rack", dest='rack')

    def handle(self, *args, **options):
        if options['barcode_list'] == "-":
            fin = sys.stdin
        else:
            fin = open( options['barcode_list'] )
        bc_ok = []
        bc_missing = []
        bc_duplicated = []
        for bc in fin:
            bc = bc.strip()
            sq = Sample.objects.filter(barcode=bc)
            if len(sq) == 0:
                bc_missing.append( bc )
            elif len(sq) > 1:
                bc_duplicated.append( bc )
            else:
                s = sq.first()
                if options['rack'] != '':
                    s.rack = options['rack']
                    s.save()
                    s.events.create(
                        status=SampleStatus.INFO.name,
                        comment='Rack set to "%s".\n(Comment put by set_status script.)' % options['rack'] )
                s.events.create(
                    status=options['status'],
                    comment=options['comment'] )
                bc_ok.append( bc )
        if options['barcode_list'] != "-":
            fin.close
        if len(bc_ok) > 0:
            print("Status %s set for following barcodes:" % options['status'])
            print("   ", ", ".join(bc_ok))
        else:
            print("Status *not* set for any barcode!")
        if len(bc_missing) > 0:
            print("Status *not* set for following barcodes, which are missing in the database:")
            print("   ", ", ".join(bc_missing))
        if len(bc_duplicated) > 0:
            print("Status *not* set for following barcodes, which each appear multiple times in the database:")
            print("   ", ", ".join(bc_duplicated))



