#!/usr/bin/python3

import sys
from flup.server.fcgi import WSGIServer
from cgi import parse_qs, escape

PORT = 31234

def app(environ, start_response):
    try:
       d = parse_qs(environ['QUERY_STRING'])
       print(d)
       #start_response('200 OK', [('Content-Type', 'text/plain')])
       #return ['Hello' + d['name'][0] + '\n']
       start_response('307 abc.html', [])
    except:
       print( sys.exc_info() )

if __name__ == '__main__':
    WSGIServer( app, bindAddress = ( "127.0.0.1", PORT ) ).run()

