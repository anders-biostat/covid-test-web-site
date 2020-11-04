import os, sys, getpass
import requests

api_url = 'http://127.0.0.1:8000/api/'

def print_paper_slip( barcode, access_code, bag_id ):
    pass

def check_response_status(response, expected_status, error_message):
    if response.status_code != expected_status:
        print("\nError: " + error_message)
        print("Server replied with status code %d and this message:" % response.status_code)
        print(response.content.decode("utf-8") + "\n")
        sys.exit(1)

def startup():

    print("""
Covid-19 LAMP Test Station
--------------------------

Paper slip printing for test kit assembly
    """)

    print("Enter your username for the Covid-19 lab server: ", end="")
    username = input()
    password = getpass.getpass("Enter your password: ")
    auth = (username, password)

    r = requests.get(api_url + 'rsakeys/', auth=auth)
    check_response_status(r, 200, "Could not get key list from server.")
    key_list = r.json()

    print("\nDo you want (1) start a new bag of test kits or (2) continue with an existing bag?")
    while True:
        print("Type 1 or 2: ", end="")
        r = input().strip()
        if r in [ "1", "2" ]:
            break

    if r == "2":
        # Continue existing bag
        print("Please enter the bag ID (a number): ", end="")
        bag_id = input()
        r = requests.get(api_url + 'bags/' + bag_id + "/", auth=auth)
        check_response_status(r, 200, "Could not find bag ID.")
        print("\nContinuing with bag %s (bag name: %s)." % ( bag_id, r.json()["name"]) )
        print("Press Enter to confirm that you will fill Bag %s. " %bag_id, end="" )
        input()
        key_id = r.json()["rsa_key"]

    else:
        # Start new bag

        print("\nList of all available encryption keys:")
        for item in key_list:
            print("%2d: %s" % (item['id'], item['key_name']), end="")
            if item['comment'] != "":
                print("[%s]" % item['comment'], end="")
            print()

        print("\nWhich of these keys should be used to encrypt registration data for samples in the new bag?")
        print("(Note: This can be changed later.)")
        print("Enter the number of a key: ", end="")
        key_id = input()

        r = requests.get(api_url + 'rsakeys/' + key_id + "/", auth=auth)
        check_response_status(r, 200, "Could not access the selected key.")

        r = requests.post(api_url + 'bags/', auth=auth,
                          data={"rsa_key": key_id, "name": "unnamed bag"})
        check_response_status(r, 201, "Could not start new bag.")
        bag_id = r.json()["id"]

        print('\nPlease prepare a new large plastic bag for the test kits and label it as "Bag %s".' % bag_id)
        print('Then press Enter. ', end="")
        input()

    return auth, bag_id, key_id


def main_loop( auth, bag_id, key_id ):

    print('\nLoad thermal paper (width 79.2 mm) into the label printer. Then, you can start')
    print('assembling test kits. Whenever you scan a tube barcode, a paper slip with an access')
    print('code will be printed. Fold it and put it together with the tube in a test-kit bag.')
    print('\nPlace all test kits into the big bag that has been labelled as "Bag %s".' % bag_id)

    while True:
        print("\nScan barcode (or type 'quit'): ", end="")
        tube_barcode = input()

        if tube_barcode.lower() == "quit":
            print("Exiting.")
            sys.exit()

        if tube_barcode.lower() == "":
            continue

        r = requests.post(api_url + 'samples/', auth=auth,
                          data={"barcode": tube_barcode, "bag": bag_id})

        if r.status_code == 400 and "barcode" in r.json() and "duplicate" in r.json()["barcode"]:
            print("This barcode has already been registered!")
            print("Do you want to reprint the paper slip for it? (y/n) ", end="")
            yn = input()

            if yn.lower().strip() == "y":
                r = requests.get(api_url + 'samples/?barcode=' + tube_barcode, auth=auth)
                check_response_status(r, 200, "Could not access existing sample tube.")
                access_code = r.json()[0]["access_code"]
            else:
                print("Skipping barcode %s." % tube_barcode)
                continue

        else:
            check_response_status(r, 201, "Could not register tube.")
            access_code = r.json()["access_code"]

        access_code = access_code[0:3] + " " + access_code[3:6] + " " + access_code[6:9] + " " + access_code[9:]
        print('Printing paper slip with access code "%s".' % access_code)
        print_paper_slip(tube_barcode, access_code, bag_id)


auth, bag_id, key_id = startup()
main_loop(auth, bag_id, key_id)