#!/usr/bin/python3

import sys
from flup.server.fcgi import WSGIServer
from cgi import parse_qs, escape, FieldStorage
import cgitb

PORT = 31234

def app(environ, start_response):
    try:
        # Create instance of FieldStorage
        fields = parse_qs(environ['QUERY_STRING'])
        # Get data from fields
        barcode = fields['bcode'][0]
        print(barcode)
        if barcode == "XYZ":
            start_response('303 See other', [('Location','/covid-test/ok.html')])
        else:
            start_response('303 See other', [('Location','/covid-test/notok.html')])

        return []
        #  d = parse_qs(environ['QUERY_STRING'])
        #print(d)
        #start_response('200 OK', [('Content-Type', 'text/plain')])
        #return ['Hello' + d['name'][0] + '\n']
        #   start_response('307 abc.html', [])
    except:
        print( sys.exc_info() )

if __name__ == '__main__':
    WSGIServer( app, bindAddress = ( "127.0.0.1", PORT ) ).run()


