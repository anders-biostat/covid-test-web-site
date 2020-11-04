import os, sys
import requests

api_url = 'http://127.0.0.1:8000/api/'


print( """
Covid-19 LAMP Test Station
--------------------------

Paper slip printing for test kit assembly
""")

print( "Enter your username for the Covid-19 lab server: ", end="")
username = input()
print( "Enter your password: ", end="")
password = input()
auth = ( username, password )

r = requests.get( api_url + 'rsakeys/', auth=auth )
if r.status_code != 200:
    print( "\nError: Could not get key list from server." )
    print( r.content.decode("utf-8") + "\n")
    sys.exit(1)

print( "\nList of all available encryption keys:")
for item in r.json():
    print( "%2d: %s" % ( item['id'], item['key_name'] ), end="" )
    if item['comment'] != "":
        print("[%s]" %  item['comment'], end="")
    print()

print( "\nWhich of these keys should be used to encrypt registration data for samples in the new bag?" )
print( "(Note: This can be changes later.)" )
print( "Enter the number of a key: ", end="" )
key_id = input()

r = requests.get( api_url + 'rsakeys/' +  key_id + "/", auth=auth )
if r.status_code != 200:
    print( "\nError: Could not access the selected key." )
    print( r.content.decode("utf-8") + "\n")
    sys.exit(1)

r = requests.post( api_url + 'bags/', auth=auth,
    data = { "rsa_key": key_id, "name": "unnamed bag" } )
if r.status_code != 201:
    print( "\nError: Could not start new bag." )
    print( r.content.decode("utf-8") + "\n")
    sys.exit(1)
bag_id = r.json()["id"]

print( '\nPlease prepare a new large plastic bag for the test kits and label it as "Bag %d".' %  bag_id )
print( '                                                                        ^^^^^^^^^' )
print( 'Load thermal paper (width 79.2 mm) into the label printer.' )
print( '\nThen, you can start assembling test kits. Whenever you scan a tube barcode, a paper slip' )
print( 'with an access code will be printed. Fold it and put it together with the tube in a test-kit bag.' )
print( 'Place all test kits into the big bag that you have just labelled "Bag %d".\n' % bag_id  )

while True:
    print( "Scan barcode (or type 'quit'): ", end="" )
    tube_barcode = input()
    if tube_barcode.lower() == "quit":
        print( "Exiting.")
        sys.exit()

    r = requests.post( api_url + 'samples/', auth=auth, headers = { 'Accept': 'application/json' },
        data = { "barcode": tube_barcode, "bag": bag_id } )

    if r.status_code == 400 and "barcode" in r.json() and "duplicate" in r.json()["barcode"]:
        print( "This barcode has already been registered!" )
        print( "Do you want to reprint the paper slip for it? (y/n) ", end="" )
        yn = input()
        if yn.lower().strip() != "y":
            print( "Skipping barcode %s." % tube_barcode )
            continue
        else:
            print("Requesting sample with bar code X.")
            # Here we need an API to search for a barcode
            access_code = "INVALID"

    elif r.status_code != 201:
        print("\nError: Could not register tube.")
        print( r.status_code )
        print(r.content.decode("utf-8") + "\n")
        sys.exit(1)

    access_code = r.json()["access_code"]
    access_code = access_code[0:3] + " " + access_code[3:6] + " " + access_code[6:9] + " " + access_code[9:]
    print( 'Printing paper slip with access code "%s".' % access_code )



