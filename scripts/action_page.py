#!/usr/bin/python3

import sys
import time
from flup.server.fcgi import WSGIServer
from cgi import parse_qs, escape, FieldStorage
import cgitb
from csv import DictWriter
from Crypto.Hash import SHA256

PORT = 31234

def append_dict_as_row(file_name, dict_of_elem, field_names):
    # Open file in append mode
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        dict_writer = DictWriter(write_obj, fieldnames=field_names)
        # Add dictionary as wor in the csv
        dict_writer.writerow(dict_of_elem)

def app(environ, start_response):
    try:
        # Create instance of FieldStorage
        fields = parse_qs(environ['QUERY_STRING'])
        # Get data from fields
        barcode = fields['bcode'][0]
        name = fields['name'][0]
        address = fields['address'][0]
        password = fields['psw'][0]
        repeat = fields['psw-repeat'][0]

        if password == repeat:
            tsu = time.gmtime()
            tsr = time.strftime('%x %X', tsu)
            columns = ['Barcode','Full Name','Address','Authentication','Time']
            data_dict = {'Barcode': barcode,'Full Name': name,'Address': address,'Authentication': password,'Time': tsr}
            append_dict_as_row('info.csv', data_dict, columns)
            start_response('303 See other', [('Location','/covid-test/instruction.html')])
        
        else:
            start_response('303 See other', [('Location','/covid-test/notok.html')])

        return ()
        #  d = parse_qs(environ['QUERY_STRING'])
        #print(d)
        #start_response('200 OK', [('Content-Type', 'text/plain')])
        #return ['Hello' + d['name'][0] + '\n']
        #   start_response('307 abc.html', [])
    except:
        print( sys.exc_info() )

if __name__ == '__main__':
    WSGIServer( app, bindAddress = ( "127.0.0.1", PORT ) ).run()


