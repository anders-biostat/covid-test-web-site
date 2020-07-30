#!/usr/bin/python3

import sys, traceback, time, hashlib
import cgi, flup.server.fcgi 

PORT = 31234

SUBJECT_DATA_FILENAME = "../data/subjects.csv"

def app(environ, start_response):
    try:
        fields = cgi.parse_qs(environ['QUERY_STRING'])
        if fields['psw'][0] == fields['psw-repeat'][0]:
            pw_hash = hashlib.sha3_256()
            pw_hash.update( fields['psw'][0].encode() )
            with open( SUBJECT_DATA_FILENAME, "a" ) as f:
                f.write( ",".join(( 
                    time.strftime('%Y-%m-%d,%H:%M:%S', time.localtime() ),
                    fields['bcode'][0],
                    fields['name'][0],
                    fields['address'][0],
                    pw_hash.hexdigest()
                )) + "\n" ) 
            start_response('303 See other', [('Location','/covid-test/instruction-de.html')])

        else:
            start_response('303 See other', [('Location','/covid-test/from-de.html')])

        return []
    except:
        traceback.print_exc()

if __name__ == '__main__':
    flup.server.fcgi.WSGIServer( app, bindAddress = ( "127.0.0.1", PORT ) ).run()


