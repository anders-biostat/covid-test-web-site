import requests
import os
import getpass, binascii, hashlib

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP

#import load_codes

# Main function to decrypt the data
def decrypt(fields, file):

    fingerprint_from_file, rsa_instance = load_key(file)
    # Three fields (barcode, time stamp, fingerprint) are plain ASCII,
    # the remainder has to go through Base-64 decoding
    for i in range( len(fields) ):
    	if i not in ( 0, 1, 3 ):
    		fields[i] = binascii.a2b_base64( fields[i] )

    # unpack line
    sample_barcode, timestamp, pw_hash, fingerprint, session_key, aes_iv = fields[:6]
    subject_data = fields[6:]

    # Print open information
    print( "\n" + sample_barcode + ": " + timestamp )

    # Check whether we have the right key
    if fingerprint == fingerprint_from_file:

    	# Decode session key for line, use it to instantiate AES decoder
    	aes_instance = AES.new(
    		rsa_instance.decrypt( session_key ),
    		AES.MODE_CBC,
    		iv=aes_iv )

    	# Decrypt subject data
    	for i in range( len(subject_data) ):
    		subject_data[i] = aes_instance.decrypt( subject_data[i] )

    	for s in subject_data:
    		print( "  ", s.decode() )

# Function to load the key finger print
def load_key(filename):
    print("Loading key \n")
    try:
        with open( filename , "rb") as f:
            protected_private_key = f.read()
    except:
    	sys.stderr.write( "ERROR: Failed to read private key file 'private.pem'.\n\n")
    	sys.stderr.write( str( sys.exc_info()[1] ) + "\n" )
    	sys.exit( 1 )

    # Get key pass phrase
    passphrase = getpass.getpass( "Enter private-key passphrase: " )

    # instantiate RSA
    try:
    	private_key = RSA.import_key( protected_private_key, passphrase=passphrase )
    except:
    	sys.stderr.write( "ERROR: Failed to use private key. Maybe the passphrase was wrong?\n\n")
    rsa_instance = PKCS1_OAEP.new( private_key )

    # Get fingerprint
    md5_instance = hashlib.md5()
    md5_instance.update( private_key.publickey().exportKey("DER") )
    public_key_fingerprint = md5_instance.hexdigest()
    key = [public_key_fingerprint, rsa_instance]
    return key


# End of functions declaration

# Start of the main function

print("Decrypting contact data for positive cases \n \n")

# An boolean set by the user to get the information
retrieve_contact = "YES"


# An empty dictionary to store all the private.pem files
key_files = {}

# Looking for the private.pem files in the current directory
# Listing all the files in the current directory
for file in os.listdir("."):

    # Checking if the private.pem file exists
    if file.endswith(".pem") and file.startswith("private"):

        # Extracting the fingerpring of the file
        file_fingerprint = file[8:-4]
        # Adding the file as the key and its finger print as the value in the dictionary
        key_files[file] = file_fingerprint
if not key_files:
    print("There is no key files in your directory! \n")
    retrieve_contact = "NO"

while(retrieve_contact.upper() == "YES"):

    code = input("Please enter the barcode:").upper()

    # Print the batch file number and assigned event
    #batch_info = load_codes.batch_finder(code)
    #for record in batch_info[code]:
    #    print("Code %s of Event %s from batch file %s" %(code, record.name, record.batch_file))
    # An empty dictionary to store the key fingerprints of the given barcode
    key_dictionary = {}
    # Post request to get the information of the given barcode
    r = requests.post("https://papagei.bioquant.uni-heidelberg.de/corona/fcgi-get-line", data={"code": code})
    # Check if the response code is ok
    if r.status_code == 200:
        #Unpacking the response in a dictionary from the corresponding list
        result = r.text.splitlines()

        if not result:
            print("There is no record available with this barcode. Please check if you typed the barcode correctly.")

        else:
            # A list to store all the fingerprints corresponding to the given barcode
            key_fingerprint = []

            # Iterating over the stored data
            for i in range(len(result)):
                subject_data = result[i].split(',')
                barcode = subject_data[0]
                if barcode!=code:
                    print("Response invalid. Something went wrong!")
                    exit(1)
                else:
                    # Fingerprint of the encoding key for the line i
                    key = subject_data[3]
                    key_fingerprint.append(key[:6])
                    # Creating the dictionary
                    key_dictionary[key[:6]] = subject_data
            print("Number of keys to decrypt the contact details: %i \n" %len(key_fingerprint))

            # Iterating over the existing key files in the directory
            for private_key_file in key_files.keys():
                k = key_files[private_key_file]
                print("Key fingerprint starts with: " + k + "\n")
                if k in key_fingerprint:
                    # Decrypting the contact info
                    decrypt(key_dictionary[k], private_key_file)
                    print("\n")
                else:
                    print("The appropriate key is not available to decrypt the data \n")
            retrieve_contact = input("Do you have another positive case: (please answer with yes or no)")

    else:
        print("Request failed with the status code: ", r.status_code)
