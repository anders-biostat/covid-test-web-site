import os, sys, getpass, re
import requests
import subprocess

#from cli.tools.label_template import label_template

api_url = 'http://127.0.0.1:8000/api/'


def render_label_template(template, context):
    tokens = re.findall(r'\{\{\W*(.*?)\W*\}\}', template)
    for token in tokens:
        try:
            substitute = context[token]
        except KeyError:
            substitute = ""
        regex = r'\{\{\W*%s\W*\}\}' % token
        template = re.sub(regex, substitute, template)
    return template


def receive_availible_printer():
    process = subprocess.Popen(['lpstat', '-p'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    lpstat = stdout.decode()
    availible_printers = re.findall(r'printer (\w+).*', lpstat)
    return availible_printers


def print_paper_slip(barcode, access_code, bag_id, printer):
    label = render_label_template(label_template, {'barcode': barcode, 'access_code': access_code, 'bag_id': bag_id,
                                           'access_code_url': access_code.replace(' ', '')})
    lp = subprocess.Popen(["lpr", "-P", printer, "-o", "raw"], stdin=subprocess.PIPE)
    lp.stdin.write(label.encode('ascii'))
    lp.stdin.close()
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

    r = requests.get(api_url + 'rsakeys/', auth=auth)
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
        r = requests.get(api_url + 'bags/' + bag_id + "/", auth=auth)
        check_response_status(r, 200, "Could not find bag ID.")
        print("\nContinuing with bag %s (bag name: %s)." % (bag_id, r.json()["name"]))
        print("Press Enter to confirm that you will fill Bag %s. " % bag_id, end="")
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

    return auth, bag_id, key_id, printer


def main_loop(auth, bag_id, key_id, printer):
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
        print_paper_slip(tube_barcode, access_code, bag_id, printer)

label_template = """
^XA
^FO50,50^GFA,4925,4925,25,,gH0LF,g03NFC,Y07FENFE,X03KFD7KFE,W03IFCL01IFC,W0IF8O0IF8,V07FF8Q0FBF,U01FF8J040808J0FFC,U0FF981F04E1C981I01FF,T03FE341664E9C9D103C07FC,T0FF0F42465A94B5102400FF,S03FC08E28653F6A511A4003FC,S07F204788671E3E31128080FF,R01FC701D98665EBC311061403FC,R07F058213C66AD5D511421C00FE,R0FC0FE305A64AD585905A08FC3F8,Q03F006FF0CE240C0I901I0B40FC,Q076075887863D20025B890214603F,P01FC0F603B00FDE766DFC30715C41F8,P037F0A010E0FFEC5C59FF8050F8A07E,P07E3861D88IFEC5C59FAF8632CAE3F,O01F82958B0FF7FEC5C59BFAF8728CA1F8,O03F0F28BC33F82EA5C5998EE405802C7C,O07C0608ECF3802E0I41981E78F31423F,O0F80448CBF6022EC5D599B037E071571F8,N01F617803FBC082EJD99A80F7858DE8FC,N03E593683B98092EJDB9C819DE32F2C7E,N07D8FCB8FE14090AD7F5BDF800FF8265D1F,N0F8BBF3BF81I013F367A7BI01FC38B50F8,M01E098447E01I011E363C29I086F212907C,M03E200CDFC01I041E96BC39I081F825263E,M07CE01837001I052F151C49I0805E28451F,M0F12038FC009I040C949C8900480373A890F8,L01F37C19F8009J04C141C09004800F8592C7C,L03E3A67FA0049I016F3579490049006E524A7C,L07C2F27EC0059I048E94B8890049001F3C823E,L0F88691D800592004CE94B8890249084F89149F,L0F3CAE3E2105920048E94B88902490847C2254F8,K01E66DA5C210592087EFD6F9C8C2490843E62947C,K03FD3166C2105921810D15790DC2490A4BB05A43C,K07D4198F5A5059239NFCF2490B5AF81BE3E,K078C272E5AD059279NFCDA490F527CFE59F,K0F261274673059E620040018003FC90CE63E409CF8,J01F110E7A67325BFC1NFC1FC90CE61F012478,J01E04C1F243125978144E881D140E4968E24F866C7C,J03C4271E24212593036E4IC9B00649684247C9FB3C,J07DE11342425259209887512E6C82496B4A43E3029E,J0791057C25A525947BAA55DCAACF1C96B4A43E5049F,J0F1CC0F625AF2598EB00C00180098C96FFE42F309CF,J0F3879D627FF259189NFC8C496FFA4278276F8,I01E4489E425AD259309FF7IF7F496496B5A427C5F478,I03E3303C425AD2596C91981C0CFCB2496B5A423CB743C,I03C04C6C425AD2596EA1881408603B496B5A421E6063C,I078E227C025FDA597EA6C826089067496BFF423F61B9E,I07910ADE02BDEA5972804B226890274977BD422F0375E,I0F1F05F402B9EE5956A18FBEF860BD4977BDC23F9FD4F,I0F1701AC0318C6595CA38CFCB8609949731CC212CEFCF,I0E10934C035AD6595EA2CCF4B9B4BD496B5AC213C2A078,001E60738C035AD6597EA46CDCBB1D3F496B4AC23163A078,001C60178C03I025967A46CD4BA5CE3496I04238E6673C,003CB0650C02AD2E5943ABBCF4BCACE34974B54238F3853C,003D4E0F0C03BDA6599D929CF4BCA4DDC97IF423871393E,0038A38A0C03BDA659A5B29CE6B8C494C97IF423878C71E,0078F05E0823IF65910A44CFFBB3014497IF4238791CDE,00709FF40C23IF65962BEECC1BE2C22497IFC2383D70EF,00F087FC0E63IF659679AACE7BEAC774D7IF42383DC33F,00F319FC0E63IFE59E59ABDE7BEACD54D7IFC2381E4C3F,00A687D81E63IFE59E59ABF007EACD54D7IFC2281E63E78,00E4F0E01A62I0259A59ABF80EEACD54D6I042280E4E378,01E5F0701E63IFE59A59ABE89EEACD54D7IFC2380F58078,01C876F01E63010659AD9ABE1C1EACD54D602042380F6323C,01471EB01A63IFE59AD9ABF142EACD54D7IFC24C0F8EFBC,03C060F01A62I0259AD9BBFI2EECD54D6I0424C0F93EBC,03CF0C701A63IFE79ADIBE413EECD54F7IFC73C0F8EA9C,039102D01EF3F77A79ADIBE491EECD54F6E6F4F7C0F98C9E,029F9BD01E32525259ADBEFC988FBCD54F6E6E4F7C0FDE19E,078AF9901E12524249BDBC78948F9CD5536A6B49380BD1F9E,07880898129282CAC9BDB839224F0CD5536B6949380DDF0DE,07001198169A8B8A89BD993B632E44D553717949BC0DE80CE,051003A8360B0F8385BD939E41BEE4D57171F1D0BC15E3E3F,072FC3283B0F070785BDB2CEFDBC94D561E0F0F0FA14E41BF,0F0061285B07070703BDB44JFD10D561E0E0F0FD14E9FEF,0FF86328B266535I3BDBC3E007A0CD560E0E0607D14EE06F,0F0FE528BA96424B4BBD983CFD0604DD4ACA6A657A94F6007,0E0087295A62523239BD907FFBF904DD524849617954B0047,0E18272A9AM01BDB0FE593C84DD480206043974F03E7,0E00CE2C9B9LDFBDB1FCFF9F44DD7331J9B8B47601780EI0E2D1BFJ577BBDB3F700FF04DD7FKBFF874743E780FF0CE2A1BFJ573BBDB6EC003BA4DD5EIAEAF787473E0781F0F2A2D9BFJ573BBDA758001BD4DD5EIAEEF79B47200781C804E2D9BFJ573BBDAEFJ0D44DD5EIAEEF6814723E781C008E291BFJ573BFFBAEJ0764FF5EIAEE769947B22781C300E299BFJ573B6796CJ036CE75EIAEE7699473DE781C588E299AFJ573BC3B6C03E032CE3DEIAEE7699470B7381C9ECE299AFJ573B81B481DD81A4C1DEIAEE769947135381CFF0A2A5AFJ573B80B483BCE1A480DEIAEE76A5473CF381C405E2E7AFJ573B00B486DBF1A580DEIAEE76E747B16381C209A2DB2FJ573B1CB48F7EF1A5805EIAEE76DB471F2381C001E2A5AF5D5D73B36B48D80B9B5365EA8AAE768147I0381CFF9E299AF5IDF7B22B48F2679B5225AB9B9EB69947010381C80DE281BB58D8F4B36A48F7E79B5325BB9B9F96814707C781C81CA2E5B958D8FCF36A4C77F71B53653B0B1B16E547073381D410E2CFB9D8D8D8700B64708F3B59071B0B4B0EEF4703F781F7E5A2CBB1DA5258700A6639CE3B58071B6A6F0ECB471BFB81E409E2DBB0D3I78722BFE1FFC7FD0061A6BEF0EDB471FF781F200A2DBB0D77F7B367B1D1FFCD853760AFBF646DB4717E781C208E2DBA0D7IFB37FB6B8IDEB5F744BIFE66DB4719C780E788E2DBA6KFB37FB8CEC1EBCDF54CAF4F7E6DB47018780E9E0E2DBA6ED924FB7FBAE3EFCBEDF54FB6469F6DB47118780E498F2FFA7DB1127B7FB09IFE085F54F64424F6FFEF3787,0E19EF601AFB2I13B7FB3FBBF1BE5D55EC442276802F3787,0E24FF7FFAF661089F7FBED1F61FB5D55C884033EDFCE3F87,0E401F289BE46108CF7FA0C3FF0D35D579084I1E934E078F,0E20052C5BCC6108477FA2CFDF0535DD71084119EA00E078F,0F2037201B884308477FAAFCDF4535DD73084108E804E050F,070E3FA89B884108637FAAE0CB2335DD62084108ED7DE272F,0713C3IFBJFEIF7FIA7CBA335DD7MFEIFC3FEE,072713BFFBFBDB7FEF7FAB5FCB81B5DD435FE35FEFFDC364E,07180399FB98E30C637FAF5FEBC0B5DD4318811C6FC9C28DE,078E0BCD9B186708636FA606FBD0F5DD431891986893CBA1E,0380FFCE9B1CF1FC636FA62E7BF075DD6719889CE9338F39E,038703CE5BFFE03IF6FA4BCEFF275DD7IF0DEBEB73856DC,03884DEF3A5AC0694B6FACBDAFF235DD431B1FEB6EF785CBC,03C21CE73A5AC0794B6FACB92EB435DD73FB8FEB6DF780D3C,01CE74A09A5AC0994B6EA8BE06BC35DD5EDC5FEB698705E3C,01C718E05A5AC1B94B6EB8340E8F15DD48DD33EB6A0F09078,01F8E0501A5AD3395B6EB0391DA315DD4DBIFEB6C0E1E078,01F70B703A5BBF1EEF6EB030D4B895DD7373F9EB6C0E3E078,00E80DF83A5BFC383B7EB023A1BC35FD635B70EB681E0307,00F0C3F83A5AFC39876E186F53F225CD435B706B681C5F0F,00F3B2BC3A5AFE1C27FFA87E6DC865FFC4BB60EB683CDD0F,00725B1C3A5AIFB93IFC37FBE077FFED9BA0EB683CD75E,0079B70E3A5BC1FC0760063C7FB3C007FDDBF0EB6858C35E,0029B70E3A5B80F8337IF0881MF05FB9EB6878CEDC,003C05073A5B8079836FBFE078FCFEFE7F83E7EB68F0CFBC,001C10873A5B843C4F6CA4C81880DE926BE1CDEB68F0F9FC,001E7893BA5B827F336CA58006605E926B7399EB69E03078,001E55939A5B81DDCF6CA50080A06E926B5F63EB68E16078,I0F3B99FA5AD11EFB6CA511E3217E926B5BCF6B6BDA60F,I0F669DFA5AE5F43B6CA611FC637E926B5BFB6B6D9CF8F,I0786F4FA5AEBC67B64A621F8A3F4926A5B41EB6FA32CE,I078176FA5AF297CB6CA621BF23F4926A5B01EB6F040FE,I03C1407A5ABDFF6B64A620B461F4926A5B81EB6E041FC,I03C144BA5ABDFD4B64A4209061F4926A5B9FEB6E083BC,I01E147BA5ABFAD4B64A5209841FC926A5DFFEB6D88078,J0E3429A52B06D4B64A5208041DC926A59FFEB6B88078,J0F1249A52E07D4B64B52086C1FC926A72CBEB4E280F,J070929A52E07D4B64BA20C4C1FC926A61136B4E6F0E,J06B0E1A52C16F4B6CBA6041C1FC926A50176B4ECF9E,J03DB79A52F0674BECB26042C1FC936BE1176B4B9FBC,J01CI9A52C1EB4BEDB6604281FC93EB43176B49303C,J01E2C9AD2FFCFCBEFE4604501D493EB3F056B49B078,K0F0E9A52FB6ECAE76C606901F697EBFF0D6B48B0F,K07825AD2A05DCAED18603281AB956BCE0D6B48F1F,K03815AD2A07FCEE708402781AF9C2B86196B48E1E,K03C17B3AB07D4CBE30C02701B7982AA7FF6B49C3C,K01A1FA23F0714C9EE0C03C0193F82AC7E3EB49878,L0E1DA2018754C9CC84019019F780AC660EB480F8,L071DA308F734C9C19401I0CE780AC7CC3B480F,L0399B3E3FF34C1811400800C6E80AE77B9F481E,L01C1B338EFB4C981283861CC7C81AED4FFB482C,M0E1B3AF4FD4C9F8C86F0F67FD81AAF49624878,M0F1B7A5FBD4C9B401C4F917F081AB7496748F,M039B3A4B3F4C90437841187E009A7F496F49E,M03DBB2492F4DD03E08608CJ09BEF494B4BC,M01FAJFE0FDF81818FFC4DFF99F03FF8F4FC,N0FB8I0600FF8I04C03CI0DF87C0719CF8,N03BJ031FBTFEFC002E0CE,N01AL021EO083FFE703F80FDC,O0gRF8,O079DIC67IFEE79E7DF7KF331889F,O03C8J07IFEF7DE79E7BFDFB02094BE,O01EC080047CFFA08249047F7E102001FC,P0LFC0TF01LF8,P07KFC01FD7FC001FFAF800LF,P01EI03C0C3FD7JFEAF806003E07C,Q0F807363E01FEAFAABFC01D1FF81F8,Q03C0EBB85001LF806C681083F,Q03F0FEFCE33003FFC03198AE338FC,R0FC9FF2C65808I0659D9FCE43B8,R07E0349CA6C35638648580778FE,R01D814601E0156E4B29543FD3F8,S07E0C1FCC294464929324DA7E,S01F800E73FC4464D2DEAF03F8,T07F00B1F384425C846EF85E,T01FC1DF3C8D424C946C13F8,U07F97D1A0D424AD7681FE,U01FFE18B2542686200FF8,V03FE09E256B85F60FFC,W07FFI08C4C80CFFC,X0IFK0601FDF,Y0JFC01CFF7F8,g0FFBMF8,gG07MF,gI07FFD,,^FS

^FX Top section name and address.
^CF0,55

^FO280,90^FDCOVID-19 Test       ^FS
^CF0,35
^FO280,155    ^FH^CI28    ^FDUniversität Heidelberg^FS
^FO280,195^FDZentrum für Molekulare Biologie ^FS
^FO50,280^GB700,2,3^FS

^FX Information text section
^CFA,30
^FO50,310^FDBitte registrieren Sie den Zugangscode ^FS
^FO50,350^FDunter folgender Adresse:^FS
^FO50,410^FDPlease register the access-code^FS
^FO50,450^FDat the following URL:^FS
^CFA,15

^FX Information table (access-code, url)
^FO50,520^GB700,200,3^FS
^FO300,520^GB1,200,3^FS
^CF0,40
^FO325,555^FDhttps://covidtest-hd.de^FS
^FO50,620^GB700,1,3^FS
^CF0,40
^FO70,555^FDURL^FS
^CF0,40
^FO70,655^FDZugangscode^FS
^CF0,48
^FO360,650^FD{{ zugangscode }}^FS

^FX QR-Code Section
^CFA,30
^FO50,800^FDOder scannen Sie^FS
^FO50,850^FDdiesen QR-Code, um^FS
^FO50,900^FDden Zugangscode zu^FS
^FO50,950^FDaktivieren.^FS
^BY5,4,270
^FT450,1100^BQN,10,8^FH\^FDHA,https://covidtest-hd.de/?code={{ access_code_url }}^FS

^FX Additional information line 
^CFE,10
^FO50,1150^FDBC: {{ barcode }} BG: {{ bag_id }}^FS
^XZ
"""

auth, bag_id, key_id, printer = startup()
main_loop(auth, bag_id, key_id, printer)