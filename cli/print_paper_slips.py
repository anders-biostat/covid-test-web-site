#!/usr/bin/python3

import getpass
import os
import re
import subprocess
import sys
import csv
import random
import string
import requests

# from cli.tools.label_template import label_template

# api_url = "http://127.0.0.1:8000/api/"
# api_url = "http://129.206.245.42:8000/api/"
api_url = "https://covidtest-hd.de/api/"

matrix = (
    (0, 3, 1, 7, 5, 9, 8, 6, 4, 2),
    (7, 0, 9, 2, 1, 5, 4, 8, 6, 3),
    (4, 2, 0, 6, 8, 7, 1, 3, 5, 9),
    (1, 7, 5, 0, 9, 8, 3, 4, 2, 6),
    (6, 1, 2, 3, 0, 4, 5, 9, 7, 8),
    (3, 6, 7, 4, 2, 0, 9, 5, 8, 1),
    (5, 8, 6, 9, 7, 2, 0, 1, 3, 4),
    (8, 9, 4, 5, 3, 6, 2, 0, 1, 7),
    (9, 4, 3, 8, 6, 1, 7, 2, 0, 5),
    (2, 5, 8, 1, 4, 3, 6, 7, 9, 0),
)


def damm_check_digit(number):
    number = str(number)
    interim = 0
    for digit in number:
        interim = matrix[interim][int(digit)]
    return interim


def render_label_template(template, context):
    tokens = re.findall(r"\{\{\W*(.*?)\W*\}\}", template)
    for token in tokens:
        try:
            substitute = str(context[token])
        except KeyError:
            substitute = ""
        regex = r"\{\{\W*%s\W*\}\}" % token
        template = re.sub(regex, substitute, template)
    return template


def receive_availible_printer():
    process = subprocess.Popen(
        ["lpstat", "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    lpstat = stdout.decode()
    availible_printers = re.findall(r"printer (\w+).*", lpstat)
    return availible_printers


def print_paper_slip(barcode, access_code, bag_id, printer):
    label = render_label_template(
        label_template,
        {
            "barcode": barcode,
            "access_code": access_code,
            "bag_id": bag_id,
            "access_code_url": access_code.replace(" ", ""),
        },
    )
    lp = subprocess.Popen(["lpr", "-P", printer, "-o raw"], stdin=subprocess.PIPE)
    lp.stdin.write(label.encode("utf-8"))
    lp.stdin.close()
    pass


def check_response_status(response, expected_status, error_message):
    if response.status_code != expected_status:
        print("\nError: " + error_message)
        print(
            "Server replied with status code %d and this message:"
            % response.status_code
        )
        print(response.content.decode("utf-8") + "\n")
        sys.exit(1)


def startup(online=True):
    print(
        """
Covid-19 LAMP Test Station
--------------------------

Paper slip printing for test kit assembly
    """
    )

    print("\nList of all available printers:")
    availible_printers = receive_availible_printer()
    for index, printer in enumerate(availible_printers):
        print("%2d: %s" % (index + 1, printer))

    print("\nWhich of these printers should be used to print the labels?")
    while True:
        print("Enter the number of a printer: ", end="")
        printer_id_input = int(input())
        if printer_id_input <= len(availible_printers) and printer_id_input > 0:
            break
    printer = availible_printers[printer_id_input - 1]
    print("You selected the printer: ", printer, "\n\n")

    if online:
        print("Enter your username for the Covid-19 lab server: ", end="")
        username = input()
        password = getpass.getpass("Enter your password: ")
        auth = (username, password)

        r = requests.get(api_url + "rsakeys/", auth=auth)
        check_response_status(r, 200, "Could not get key list from server.")
        key_list = r.json()

        print(
            "\nDo you want (1) start a new bag of test kits or (2) continue with an existing bag?"
        )
        while True:
            print("Type 1 or 2: ", end="")
            r = input().strip()
            if r in ["1", "2"]:
                break

        if r == "2":
            # Continue existing bag
            print("Please enter the bag ID (a number): ", end="")
            bag_id = input()
            r = requests.get(api_url + "bags/" + bag_id + "/", auth=auth)
            check_response_status(r, 200, "Could not find bag ID.")
            print("\nContinuing with bag %s (bag name: %s)." % (bag_id, r.json()["name"]))
            print("Press Enter to confirm that you will fill Bag %s. " % bag_id, end="")
            input()
            key_id = r.json()["rsa_key"]

        else:
            # Start new bag

            print("\nList of all available encryption keys:")
            for item in key_list:
                print("%2d: %s" % (item["id"], item["key_name"]), end="")
                if item["comment"] != "":
                    print("[%s]" % item["comment"], end="")
                print()

            print(
                "\nWhich of these keys should be used to encrypt registration data for samples in the new bag?"
            )
            print("(Note: This can be changed later.)")
            print("Enter the number of a key: ", end="")
            key_id = input()

            r = requests.get(api_url + "rsakeys/" + key_id + "/", auth=auth)
            check_response_status(r, 200, "Could not access the selected key.")

            r = requests.post(
                api_url + "bags/",
                auth=auth,
                data={"rsa_key": key_id, "name": "unnamed bag"},
            )
            check_response_status(r, 201, "Could not start new bag.")
            bag_id = r.json()["id"]

            print(
                '\nPlease prepare a new large plastic bag for the test kits and label it as "Bag %s".'
                % bag_id
            )
            print("Then press Enter. ", end="")
            input()

        return auth, bag_id, key_id, printer
    return (printer,)


def main_loop(config):
    online = True
    if len(config) == 1:
        online = False

    # config: (auth, bag_id, key_id, printer) if online else (printer,)
    print(
        "\nLoad thermal paper (width 79.2 mm) into the label printer. Then, you can start"
    )
    print(
        "assembling test kits. Whenever you scan a tube barcode, a paper slip with an access"
    )
    print(
        "code will be printed. Fold it and put it together with the tube in a test-kit bag."
    )
    if online:
        print(
            '\nPlace all test kits into the big bag that has been labelled as "Bag %s".'
            % config[1]
        )

    while True:
        barcode_valid = False
        print("\nScan barcode (or type 'quit'): ", end="")
        tube_barcode = input()

        if tube_barcode.lower() == "quit":
            print("Exiting.")
            sys.exit()

        if tube_barcode.lower() == "":
            continue

        correct_barcode_format = re.match(
            r"^([A-Z][0-9]{5})$|^([0-9]{10})$", tube_barcode
        )
        if correct_barcode_format:
            barcode_valid = True
        else:
            print(
                f"Wrong format! Are you sure you want to save the barcode? -> {tube_barcode}"
            )
            barcode_ok = input("Type 1 for YES and 2 for NO: ")
            if barcode_ok == "1":
                barcode_valid = True

        if barcode_valid and online:
            r = requests.post(
                api_url + "samples/",
                auth=config[0],
                data={"barcode": tube_barcode, "bag": config[1]},
            )
        else:
            pass

        if (
                online and
                r.status_code == 400
                and "barcode" in r.json()
                and "duplicate" in r.json()["barcode"]
        ):
            print("This barcode has already been registered!")
            print("Do you want to reprint the paper slip for it? (y/n) ", end="")
            yn = input()

            if yn.lower().strip() == "y":
                r = requests.get(
                    api_url + "samples/?barcode=" + tube_barcode, auth=config[0]
                )
                check_response_status(r, 200, "Could not access existing sample tube.")
                access_code = r.json()[0]["access_code"]
            else:
                print("Skipping barcode %s." % tube_barcode)
                continue

        elif online:
            check_response_status(r, 201, "Could not register tube.")
            access_code = r.json()["access_code"]
        else:
            access_code = "".join(random.choice(string.digits) for _ in range(10))
            access_code = "A" + access_code + str(damm_check_digit(access_code))
            with open(r"access_codes.csv", "a") as csvfile:
                fieldnames = ['barcode', 'accesscode']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writerow({'barcode': tube_barcode, 'accesscode': access_code})

        access_code = (
                access_code[0:3]
                + " "
                + access_code[3:6]
                + " "
                + access_code[6:9]
                + " "
                + access_code[9:]
        )
        print('Printing paper slip with access code "%s".' % access_code)
        #print_paper_slip(tube_barcode, access_code, "", config[3] if online else config[0])

label_template = """
CT~~CD,~CC^~CT~
^XA


~TA000~JSN^LT0^MNN^MMC^MTD^PON^PMN^LH0,0^JMA^PR6,2~SD20^JUS^LRN^CI0^XZ
^XA
^PW609
^LL2000

^FX Top section name and address.
^CF0,30

^FO50,175 ^FH^CI28 ^FDCOVID-19 LAMP-Test for Gargle Samples^FS
^CF0,35
^FO50,215    ^FH^CI28    ^FDHeidelberg University^FS

^FX Information text section
^CF0,30
^CFA,15





^FX Information table (access-code, url)


^FO50,300^GB540,160,3^FS
^FO250,300^GB1,160,3^FS
^CF0,32
^FO310,330^FDcovidtest-hd.de^FS
^FO50,380^GB540,1,3^FS
^CF0,30
^FO70,332^FDWebsite^FS
^CF0,30
^FO70,410^FDTube-Code^FS
^CF0,38
^FO270,407^FD{{ barcode }}^FS

^CF0,40
^FO38,520^FD EN:^FS

^CF0,32
^FO40,580^FD ►^FS
^FO70,580^FD Please validate that the code printed on^FS
^FO70,620^FD the side of your tube is correct^FS

^FO40,660^FD ►^FS
^FO70,660^FD Store this paper to retrieve your result^FS
^FO70,700^FD on our website (covidtest-hd.de)^FS

^FO40,740^FD ►^FS
^FO70,740^FD Retrieve your access code by carefully^FS
^FO70,780^FD unwrapping the bottom part of this paper^FS

^FO40,820^FD ►^FS
^FO70,820^FD As a reminder: Write down the name^FS
^FO70,860^FD and date of the test on the back^FS



^CF0,40
^FO38,920^FD DE:^FS

^CF0,32
^FO40,980^FD ►^FS
^FO70,980^FD Bitte den Code auf dem Teströhrchen^FS
^FO70,1020^FD überprüfen ^FS

^FO40,1060^FD ►^FS
^FO70,1060^FD Bitte aufbewahren, um das Resultat auf^FS
^FO70,1100^FD unserer Webseite abzurufen^FS

^FO40,1140^FD ►^FS
^FO70,1140^FD Entfalten Sie bitte vorsichtig den unteren^FS
^FO70,1180^FD Abschnitt für den Zugangscode^FS

^FO40,1220^FD ►^FS
^FO70,1220^FD Zur Erinnerung: Namen und Datum des^FS
^FO70,1260^FD Tests auf der Rückseite notieren^FS

^FX Arrow
^FO50,1320^GFA,320,320,4,001F,:::::::::::::::::::::::::::::::::::::::::::::::::::3KF8,::1KF,:0JFE,:07IFC,:03IF8,:01IF,:00FFE,:007FC,:003F8,:001F,:I0E,:I04,:,::^FS

^CF0,42
^FO90,1320^FD Bitte vorsichtig entfalten^FS
^FO93,1370^FD Please unwrap carefully^FS

^FX Arrow
^FO550,1320^GFA,320,320,4,001F,:::::::::::::::::::::::::::::::::::::::::::::::::::3KF8,::1KF,:0JFE,:07IFC,:03IF8,:01IF,:00FFE,:007FC,:003F8,:001F,:I0E,:I04,:,::^FS

^FX Obfucsation

^CF0,38
^FO0,1420^FD 21762547136996687678243853554622 ^FS
^FO10,1435^FD 40544538960691802457079432240231 ^FS
^FO0,1450^FD 96921176752017760350248947117358 ^FS
^FO10,1465^FD 22495325395827841231720164797028 ^FS
^FO0,1480^FD 14994976063650872634791751311113 ^FS
^FO10,1495^FD 89144658376932291712874922475885 ^FS
^FO0,1510^FD 99520274140349530546540514999056 ^FS
^FO10,1525^FD 75130970264816728123196210537387 ^FS
^FO0,1540^FD 13964186543719207169386968299559 ^FS
^FO10,1555^FD 22510836988114223290782446823980 ^FS
^FO0,1570^FD 89186398516161435342905584249071 ^FS
^FO10,1585^FD 07064410691651133797152011892162 ^FS
^FO0,1600^FD 62927925642621976514346671532105 ^FS
^FO10,1615^FD 85777250698419484833190252530109 ^FS
^FO0,1630^FD 60530203724556661028315375993838 ^FS
^FO10,1645^FD 32700765837054493358634388506285 ^FS
^FO0,1660^FD 72115135850124528233470333586601 ^FS
^FO10,1675^FD 53380272778434434031723386589730 ^FS
^FO0,1690^FD 97993114228690146310273907405890 ^FS
^FO10,1705^FD 52772071933244502330799277648330 ^FS
^FO0,1720^FD 86566641662012324344161900890882 ^FS
^FO10,1735^FD 09375473240469164694623162580549 ^FS
^FO0,1750^FD 81005215016342054475036406682117 ^FS
^FO10,1765^FD 07621987391579627685398864283671 ^FS
^FO0,1780^FD 88324415009826404373701637065921 ^FS
^FO10,1795^FD 88065447552108166952994638606170 ^FS
^FO0,1810^FD 33991999481613862847980895353564 ^FS
^FO10,1825^FD 43046090259853266406912766049336 ^FS

^CF0,32
^FO200,1890^FD Access-Code:  ^FS
^CF0,38
^FO180,1940^FD {{ access_code }} ^FS
^FS^PQ1,1,0,Y^XZ
"""

config = startup(online=False)
main_loop(config)
