#!/usr/bin/python3

import getpass
import os
import re
import subprocess
import sys

import requests

# from cli.tools.label_template import label_template

# api_url = 'http://127.0.0.1:8000/api/'
#api_url = "http://129.206.245.42:8000/api/"
api_url = "https://covidtest-hd.de/api/"

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
    process = subprocess.Popen(["lpstat", "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        print("Server replied with status code %d and this message:" % response.status_code)
        print(response.content.decode("utf-8") + "\n")
        sys.exit(1)


def startup():
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

    print("Enter your username for the Covid-19 lab server: ", end="")
    username = input()
    password = getpass.getpass("Enter your password: ")
    auth = (username, password)

    r = requests.get(api_url + "rsakeys/", auth=auth)
    check_response_status(r, 200, "Could not get key list from server.")
    key_list = r.json()

    print("\nDo you want (1) start a new bag of test kits or (2) continue with an existing bag?")
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

        print("\nWhich of these keys should be used to encrypt registration data for samples in the new bag?")
        print("(Note: This can be changed later.)")
        print("Enter the number of a key: ", end="")
        key_id = input()

        r = requests.get(api_url + "rsakeys/" + key_id + "/", auth=auth)
        check_response_status(r, 200, "Could not access the selected key.")

        r = requests.post(api_url + "bags/", auth=auth, data={"rsa_key": key_id, "name": "unnamed bag"})
        check_response_status(r, 201, "Could not start new bag.")
        bag_id = r.json()["id"]

        print('\nPlease prepare a new large plastic bag for the test kits and label it as "Bag %s".' % bag_id)
        print("Then press Enter. ", end="")
        input()

    return auth, bag_id, key_id, printer


def main_loop(auth, bag_id, key_id, printer):
    print("\nLoad thermal paper (width 79.2 mm) into the label printer. Then, you can start")
    print("assembling test kits. Whenever you scan a tube barcode, a paper slip with an access")
    print("code will be printed. Fold it and put it together with the tube in a test-kit bag.")
    print('\nPlace all test kits into the big bag that has been labelled as "Bag %s".' % bag_id)

    while True:
        print("\nScan barcode (or type 'quit'): ", end="")
        tube_barcode = input()

        if tube_barcode.lower() == "quit":
            print("Exiting.")
            sys.exit()

        if tube_barcode.lower() == "":
            continue

        r = requests.post(api_url + "samples/", auth=auth, data={"barcode": tube_barcode, "bag": bag_id})

        if r.status_code == 400 and "barcode" in r.json() and "duplicate" in r.json()["barcode"]:
            print("This barcode has already been registered!")
            print("Do you want to reprint the paper slip for it? (y/n) ", end="")
            yn = input()

            if yn.lower().strip() == "y":
                r = requests.get(api_url + "samples/?barcode=" + tube_barcode, auth=auth)
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
        print_paper_slip(tube_barcode, access_code, bag_id, printer)


label_template = """
CT~~CD,~CC^~CT~
^XA~TA000~JSN^LT0^MNN^MMC^MTD^PON^PMN^LH0,0^JMA^PR6,2~SD20^JUS^LRN^CI0^XZ
^XA
^PW609
^LL1800
^FO50,50^GFA,3784,3784,22,,Y0KFE,W03NF8,V03PF8,U01IFCJ01IF8,U0IFN0IF,T07FEP0FFC,S01FFJ04182J0FF8,S0FF30792699300101FE,R03F868112EB97081403F8,R0FE0B8A12BA554C0400FE,Q01F808D2139E7ICE4003F8,Q07E201E6131E38CC86180FE,P01F85822F13AEB94CA21803F,P03E07E61692AC156C2A01F0FC,P0FC02FC139608126C4800503E,O01F03903613EA2452C5062B81F8,O07F85009C0IE58B7F0050E307C,O0F9C20I1FIE58B7FE063D2B3F,N01F0C28A1FFIE58B6IF8E3358F8,N07C384CC6FE36258B6C7E40A0567C,N0F8304E9EE02604006C0E71CC223E,M01F0120DBF81A66D936C81FC0CAF8F,M03CC4A03FB02077DBB6E40BF0CAC47C,M079B6BC7E102C77DBAE6408FC032F3E,M0F07F9DF820089F3EA95800BF165D1F,L01E1J3702I08A3C79C8008FC8950F8,L03C40227C020020A3D70C80083E02A67C,L079C061B012002061870480081F95493C,L0F070E3C0120020419304800807DECA1E,K01E3786D8012002A618354800803E294CF,K03C34CFF0012I0EEBDF64801A00F3A9478,K03C2F46C00520024EBD704805A0078D043C,K07995C7800D20024EBD724805A113E32BBE,K0F6484F108D2029EFFDF74405A311F6129E,J01FD329F108D206A0D3E706605A355F8578F,J03CC1A3D568D24EFFBFFDFF705A3D53C9EC78,J03D40679910D3CE80E003003FDA3391EF833C,J079314E1B90D3F8806007001FDA3390F0253C,J0F0481C919AD2F0KFDFE0FDAB312F84D1E,J0F2263C911AD2E092489240065AB11278BF0F,I01EF0378950AD2C2CD7565B2425AA5523C20EF,I01C984F8956AD29EB0491048799AA5523E21678,I03CC60E89FFAD33280E89F4A0CDABFF22F60F38,I079619C8957AD262MFE065ABD522709D3C,I07130B48956AD2D2FFCBDF7E1A5AA5522397F1E,I0F00C788957AD29A8C8381101B5AB55223C411E,I0E70278895FAD2FA96024128375ABF7A23EC4CF,001E48AFC8AIED2EA96164928175A8EEA23E0DEF,001C781E88AEE6D2FA8C7BDF181D5ACEE623F3FE78,003C5C1C88CC66D2BA9E4E97381D5ACC662371BE78,003807BI8F57ED2FA964F974C1D5AFD5E2338E838,003900BI8C442D2DEA34B97C6735A8442233DD93C,0072827188CA82D28E89CA9732635AC2A2231CB39C,0075707188FEF6D336D5CED72A6D9AFEFE231E4C9E,00F30CA188DEF6D35284CE770050DAIFE230E33DE,00E3C6E108IF6D202A2CDB7CC085AIFE230F4E6E,00E27FC1C8IF6D2CAD5CC378A335AIFE2387585F,01C007C1C8IFED3DED5CE779A771AIFE2307331F,01CC3F81C8IFED356D5F00F9A651AIFE23839CF78,01C38781488002D356D5F80F9A651AC002258393B78,03978381C8IFED356D5E91FBA659AIFE2781DC038,03819701C8C182D356D5E183BA659AC1822781D8B38,0280150148IFED356D5F24FBA659AFFBE2481C67BC,0708270148C002F356DDE447B2659EC00E2581E3C1C,07243781DCIFEF356DDE427B2659EIFE7783E669C,072E5F81DC9DAB5356D5C993BE659E99327783EE09C,073BCC81C485ABD356E3CA93E64596892A5383F4F9E,06I0C8142A5CBC356E3D24BC64596A54A13037784E,0EI0D8342A1C18B56C9B42F924DA2C5CE9B83720CE,0E601D8343C3C78B76DCE437A84DE2C7C68BC379C1E,0E87194561C383077692JF004D63C3870FC33A7FE,0EA1194B6989832776A3F83F464D41838707A33BC6E,0IF984B5495AB5776C1C081824D5I93347D33B02F,0E0298554491281376C3EFF6404DD5810A57I38007,0C0038494L037687EDA7A04DCL032FB81E7,1C013049I76EFDF768FAFF7D04DFI6CC9F1F99017,1C003051755FBB57769F600FE04D77FEFDFF0E9A7E7,1IF3061757FBB57769AC006E84D55FAB577069DC07,1C007059755FBB5776BF8003704DD5FAB577369D067,1C027041755DBB57FEF7I01D07FD5FAB577369D927,1C40705975DDBB56DED6J0D27355FAB577329CEE7,1DB2705975DDBB578EF603C05A63D5FABI7329C5B7,197F705975DDBB5706B41FF04A61D5AABI7329C9D7,18C0706575DDBB5602B43FEC6A40D5EABI7489D8F7,1882707F75FDBB5602B47D7E6A00D5EABI7CC9CD27,1800704175F5EB567AB4ID66A1ED5E2AI7849C607,18FE705975F7EF564AB4700F6A1255E6CF57209C007,190370417567CF5E4AB477EE6A1257E6CD97009C3C7,180770657562C7CE7AB477EE6A1E7362CD9FC89C3F7,1A84704F7363C78E02B2319CEA00634A858F949C1F7,1C98704B634BB78602B31B98EA00635BB50DB49CDB7,1C10705B635BF386DACF1FF9F61261DEF705B49CFF7,1E42705B415IF26DE849FF3223749JF67B49CFC7,1CE2705B49JF36DEC6CC3EF677CD7F7F67B498087,1D38705B4DA4B4F2DEC63E7872774F4935F7B4B8087,1C963BFF5F689272FE85IFC627D5E9112F6FFB9F87,1C67BA035EC8893AFEDF9BE7FA7D5DJ13700B9B87,0CC0FBFF5C9I89EFEB61FC34A7D7911093FA5B8F87,0C807849791084CEFE863DE14A7D7211089D24B838E,0C40B8017110844EFE97CD614A7D6231088D00B038E,0E18D94972108446FEB70D60CA7D6421088DA5B030E,0E6F1IF7BIF7F6FEA76D744A7D7IF3FFCIF0FFE,0E5C5DFF7F75BDEEFEB8FD744A7D46F79ACCFF71B6E,0E201CDF63318C62FEB9FD7C2A7D463008C4FA7146E,07107E516I3CC62FEB16F7C3A7D462244C596E7B9C,07077E6967B81EF7FEB1E7FC187D6F7C67EDACE39DC,07382E755AB03D57FEA5C9FE987D462C7E35FCE0E5C,0728667352B03D57FEA5D0FE087567AE7E94BCC06BC,03B987095AB04D57FEA1E2D7087575B17E95B1C2738,039A67015AB0D957FEC3C0F3CC7559BCDE9441C6838,03E203815AED9FDFFEC393B464755E6FEE94818F078,01D87F835AFF9E7FFEC30CD7287566EFC694838107,01C227835AFE1997F8C37E3F8875422D8295839387,01C691C35ABF1C0FFEC3E5FA1A7F4D6D869587368F,00EAD8C35ABFF937FEA3BFFC1BFFDF6C869487218E,00E4D8E35AF0FC8E80316FF4F007FFAFC6940E25EE,00F6B8635AE07C76IFC083LF0BIE940E33FE,007008735AE03D8EDEFF079E3F5A7F0736941C37DC,0070C4335AE13C6692A601E0355A43C66E941C3C3C,0039ADBB5AE1FD9E92AC0808155A42FC8E94380838,00385C9F5AF0CEDE92A81C34155A42BF1A953A1038,001DB8DF52B8DE7692B91FCCDD5A42AFFAD4F33C7,001C374F52B8E27692B11F145D5A42AD0ED4FCC67,I0E0B6752BD4FD692B117EC7D5A42AC06D4E187E,I0E020752AEFD5692B10A087D5A42AE0ED4C10EE,I07007B52AFDD5692A109087D5A42AEFED49109C,I07083B52AC3D5692A908087D5B42B7FED4B303C,I038A0952B83D5692A908587D5B40A75ED4C2038,I01C52952B03D56928B08587F5B42D45AD4C9C78,I01D8E952B0375692D304387E5B40A05AD4D9E7,J0EDB952B8335792D304307F5B43C01AD5234E,J0F0D952B0EF57969204507F5BC20C3AD4A41E,J071E952BFA7D79FA204A07B5BC2FC2AD4941C,J0382952BC2CD7D4E2070055DF43BC2AD48438,J01C055AA83FIDC4202706BDD42186AD49C78,J01E1766E83F5D58C202E06BDC331FFAD498F,K0E1F64FC395D7B8603806DFC351F9ED4B0E,K071D6006315D3342010027BC159906D481C,K03996733B35D30480100I3C159F71F483C,K01D16FC7FB5C304K0316C1495EFF4878,L0E16EB17F5D32546C0FBFEC16D56F348F,L0716A9FI5D2E00E7F65DCC375D6B349E,L0316EB79F5D611BC4231F00B1FD6A75BC,L03976949F5DE0F20411J0BF9D6AF4F8,L01F5IFE07DE040CE11800DBC0FF8FCF,M0F6I0300EEI07C0F8007F3F01B8CE,M076I010F3DJF7LFCFK0DC,M01gNF8,N0LF7IF73DEFBDOFDF,N073J07IFBBDEF39DIFE00809E,N0392I047BFC8429293FFC2J0FC,N01KFC0KFDKFE03KF,O0F8003C03FBFF007IFJ0F83E,O07C0334783LFBF80618E07C,O01F06922C01LF02451F20F8,P0F87EF9CC803FFC085C9C663E,P03E4FE588CK094E9BFD0FC,P01F035189A17451962C1FE3F,Q07C0C4670I4D84A3E1F6FC,Q01F083927C454B4A1A195F,R07C01CEFEI4B6A66E0FC,R01F817CCJ4B223C63F,S07F2F4F0454A23A81FC,S01FFC67955491980FF,T03FC07155313F07F8,U07FC008C88067FC,V0FFEI0181FFE,W0OFE,X0MFE,g0JF,,^FS

^FX Top section name and address.
^CF0,50

^FO250,75 ^FH^CI28 ^FDCOVID–19 Test       ^FS
^CF0,35
^FO250,135    ^FH^CI28    ^FDUniversität Heidelberg^FS
^FO250,175^FDZMBH ^FS
^FO50,250^GB540,2,3^FS

^FX Information text section
^CF0,30
^FO50,310^FDBitte registrieren Sie Ihr Test-Kit hier: ^FS
^FO50,350^FDPlease register your test kit here:^FS
^CFA,15



^FX Information table (access-code, url)


^FO50,420^GB540,160,3^FS
^FO250,420^GB1,160,3^FS
^CF0,32
^FO310,450^FDcovidtest-hd.de^FS
^FO50,500^GB540,1,3^FS
^CF0,30
^FO70,452^FDWebseite^FS
^CF0,30
^FO70,530^FDZugangscode^FS
^CF0,38
^FO300,527^FD{{ access_code }}^FS
^FO50,580^GB540,1,3^FS
^CF0,22
^FO70,600^FDProben Röhrchen^FS
^CF0,20
^FO300,600^FDBC: {{ barcode }} BID: {{ bag_id }}^FS

^FX QR-Code Section


^CF0,30
^FO50,680^FD... oder scannen Sie diesen QR-Code:^FS
^FO50,720^FD... or scan this QR-Code:^FS

^BY5,4,270
^FT180,1080^BQN,2,7^FH\^FDHA,https://covidtest-hd.de/?code={{ access_code_url }}^FS


^FX Additional information line

^FO50, 1200^FD Name:^FS
^FO50,1260^GB700,3,3^FS
^FO50, 1320^FD Datum:^FS
^FO50,1380^GB700,3,3^FS

^FO50,1420^GFA,512,512,8,,:::::::::::L07FFE,L0JF8,K01JFC,K03JFE,K07KF,K0LF,007PFE,01RF8,:03RFC,03PFE1C,03JFE007FFE1C,03JFC003IF3C,03JF03C0JFC,03IFE0FF07IFC,03IFE3FFC7IFC,03IFC7FFE3IFC,03IF87FFE1IFC,03IF8JF1IFC,:03IF9JF9IFC,03IF1JF8IFC,:03IF9JF9IFC,03IF8JF1IFC,::03IFC7FFE3IFC,03IFC3FFC3IFC,03IFE1FF87IFC,03JF03C0JFC,03JF8001JFC,03JFE007JFC,03KFC3KFC,03RFC,:::01RF8,00RF,,:::::::::::^FS

^FO120,1442^FD Bitte Zettel fotografieren oder aufheben ^FS

^FS^PQ1,1,0,Y^XZ
"""

auth, bag_id, key_id, printer = startup()
main_loop(auth, bag_id, key_id, printer)
