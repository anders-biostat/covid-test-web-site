import os
import subprocess

#Function to go to the given path and
#increment the highest already generated batch number
def new_extension(fname_path):
    filename, file_extension = os.path.splitext(fname_path)
    i = 1
    new_fname = "{}_{}{}".format(filename, i, file_extension)
    while os.path.exists(new_fname):
        i += 1
        new_fname = "{}_{}{}".format(filename, i, file_extension)
    return i

#Function to calculate the check digit according to Damm algorithm
def dammDigit(sequence):
    row = 0
    for digit in str(sequence):
        row = _matrix[row][int(digit)]
    for damm in range(0,10):
        if _matrix[row][damm] == 0:
            break
    return damm

#Damm table
_matrix = (
    (0, 3, 1, 7, 5, 9, 8, 6, 4, 2),
    (7, 0, 9, 2, 1, 5, 4, 8, 6, 3),
    (4, 2, 0, 6, 8, 7, 1, 3, 5, 9),
    (1, 7, 5, 0, 9, 8, 3, 4, 2, 6),
    (6, 1, 2, 3, 0, 4, 5, 9, 7, 8),
    (3, 6, 7, 4, 2, 0, 9, 5, 8, 1),
    (5, 8, 6, 9, 7, 2, 0, 1, 3, 4),
    (8, 9, 4, 5, 3, 6, 2, 0, 1, 7),
    (9, 4, 3, 8, 6, 1, 7, 2, 0, 5),
    (2, 5, 8, 1, 4, 3, 6, 7, 9, 0)
)

#Initial batch size (We can explicitly equate to 96)
batch_size = int(input("What is the size of the batch:"))
#An empty list to store the scanned barcodes and check for duplicates
barcode = []

#The path to save the generated batch file
#I think it is better to a path that cannot be modified by the user
#since we need to always save the generated batches to the same directory to
#keep the track of our current batches
batch_number = new_extension("Codes/micronic_batches/micronic_A.lst")

#Block to make the full printing printCommand
#It can be replaced by a template file later
printer_setting = "CT~~CD,~CC^~CT~ \n ^XA~TA000~JSN^LT0^MNN^MTD^PON^PMN^LH0,0^JMA\
^PR2,2~SD20^JUS^LRN^CI0^XZ \n \
^XA \n \
^MMT^PW609^LL0959^LS0"

title = "^FT77,64^A0N,51,38^FB480,1,0,C^FH\^FDUniversit\84t Heidelberg^FS\
^FT77,128^A0N,51,38^FB480,1,0,C^FH\^FDCOVID-19 Test via LAMP^FS\
^FT38,208^A0N,39,31^FH\^FDBitte scannen Sie diesen QR-Code:^FS"

qr_setting = "^FT165,563^BQN,2,6^FH\^FDHA,https://coronatest.zmbh.uni-heidelberg.de/register?code="

web_string = "^FT46,614^A0N,34,33^FH\^FDoder gehen Sie zu unserer Webseite^FS\
^FT46,656^A0N,34,33^FH\^FDcoronatest.zmbh.uni-heidelberg.de^FS\
^FT46,698^A0N,34,33^FH\^FDund geben Sie diesen Code ein: ^FS"

rect = "^FO155,733^GB289,74,4^FS\
^FT234,783^A0N,34,33^FH\^FD"

tube_code = "^FT46,898^A0N,34,33^FH\^FDCode auf R\94hrchen: "

end_line = "^FS^PQ1,1,0,Y^XZ"
#End of the print command block

#Start the barcode scanning process
while len(barcode) < batch_size:
    try:
        micro_bc = str(input("Please scan the barcode:"))

#Initial check to see if the scanned number is correct and assign the correct
#batch digit
        if (int(micro_bc[:5]) != 40439):
            print("There is a problem with your barcode. Please scan it again")

    #Check if the given tube has already been scanned
        else:
            if micro_bc in barcode:
                print("The barcode was scanned before")

    #Append the scanned barcode to our list
            barcode.append(micro_bc)

    #Initialize the batch digit
            batch_digit = str(1)

    #Initialize check digit based on Damm algorithm
            check_digit = dammDigit(micro_bc[5:]+batch_digit)

    #Constructing different codes available on the label
            code = micro_bc[5:] + batch_digit + str(check_digit)
            readable_code = code[:2]+" "+code[2:5]+" "+code[5:]

    #Generating the string containing the print commands and write it
    #to a temporary file
            print_string = (printer_setting + title + qr_setting + code + "^FS" +
                            web_string + rect + readable_code + "^FS" + tube_code +
                            micro_bc + end_line)
            with open("tmp_print_file.prn", "w+") as f:
                f.write(print_string)
            f.close()

    #Printing the label
            printCommand = "lpr -P Zebra_Technologies_ZTC_GK420t -o raw tmp_print_file.prn"
            printProcess = subprocess.Popen(printCommand.split(), stdout=subprocess.PIPE)
            output, error = printProcess.communicate()

#Exception handler for the ctrl+C interruption
    except KeyboardInterrupt:
        print("The size of your batch is: %i" %len(barcode))
        break

#Removing the temporary file for printing
removeCommand = "rm tmp_print_file.prn"
removeProcess = subprocess.Popen(removeCommand.split(), stdout=subprocess.PIPE)
output, error = removeProcess.communicate()

#Writing the scanned barcodes to a file
batch_file = open("Codes/micronic_batches/micronic_A_%i.lst" %batch_number, "w+")
for bc in barcode:
    batch_file.write(bc+"\n")
batch_file.close()
print(check_digit)
print("A batch file is created")
