import sys, csv
from django.core.management.base import BaseCommand
from app.models import Sample
from app.statuses import SampleStatus

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help="csv file with headers 'well', 'rack', 'barcode', 'call' (or '-' for "
                                                     "stdin)" )
        parser.add_argument('--comment', type=str, default="", help="comment to be stored in Event records", dest='comment')

    def handle(self, *args, **options):
        if options['csv_file'] == "-":
            fin = sys.stdin
        else:
            fin = open( options['csv_file'], encoding='utf-8-sig' )
        bc_ok = []
        bc_missing = []
        bc_duplicated = []
        wrong_status = []
        status_recorder = {}
        for r in csv.DictReader(fin):
            if r['call'] == '':
                continue
            if r['call'] not in [x.name for x in SampleStatus]:
                print('Unknown status %s set for barcode %s, skipping.' % (r['call'], r['barcode']))
                wrong_status.append( r['barcode'] )
                continue
            sq = Sample.objects.filter(barcode=r['barcode'])
            if len(sq) == 0:
                bc_missing.append( r['barcode'] )
            elif len(sq) > 1:
                bc_duplicated.append( r['barcode'] )
            else:
                s = sq.first()
                s.events.create(
                    status=r['call'],
                    comment="Rack %s, Well %s\n%s" % (r['rack'], r['well'], options['comment']))
                status_recorder[r['barcode']] = r['call']
                bc_ok.append( r['barcode'] )
        if options['csv_file'] != "-":
            fin.close()
        if len(bc_ok) > 0:
            print("THE FOLLOWING STATUS HAVE BEEN SET:")
            for bc, stat in status_recorder.items():
                print("Barcode %s  ==>  %s:" % (bc, stat))
        else:
            print("Status *not* set for any barcode!")
        if len(bc_missing) > 0:
            print("Status *not* set for following barcodes, which are missing in the database:")
            print("   ", ", ".join(bc_missing))
        if len(bc_duplicated) > 0:
            print("Status *not* set for following barcodes, which each appear multiple times in the database:")
            print("   ", ", ".join(bc_duplicated))



