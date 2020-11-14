import binascii
import getpass
import hashlib
import os
import sys

import requests
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA


def decrypt_str(aes_instance, string):
    item_encrypted = binascii.a2b_base64(string)
    item_decrypted = aes_instance.decrypt(item_encrypted)
    return item_decrypted.decode()


# Main function to decrypt the data
def decrypt_and_print(registration_data, file, barcode):
    fingerprint_from_file, rsa_instance = load_key(file)
    # Three fields (barcode, time stamp, fingerprint) are plain ASCII,
    # the remainder has to go through Base-64 decodasding

    # Check whether we have the right key
    if registration_data["key_information"]["public_key_fingerprint"] == fingerprint_from_file:
        session_key_encrypted = binascii.a2b_base64(registration_data["key_information"]["session_key_encrypted"])
        aes_instance_iv = binascii.a2b_base64(registration_data["key_information"]["aes_instance_iv"])

        # Decode session key for line, use it to instantiate AES decoder
        aes_instance = AES.new(
            rsa_instance.decrypt(session_key_encrypted),
            AES.MODE_CBC,
            iv=aes_instance_iv,
        )

        # Decrypt subject data
        name = decrypt_str(aes_instance, registration_data["name_encrypted"])
        address = decrypt_str(aes_instance, registration_data["address_encrypted"])
        contact = decrypt_str(aes_instance, registration_data["contact_encrypted"])

        print("=" * 80)
        print("Barcode:\t", barcode)
        print("Name:\t\t", name)
        print("Contact:\t", contact)
        print("Address:\t", address)
        print("=" * 80)
    else:
        print("Wrong key")


# Function to load the key finger print
def load_key(filename):
    try:
        with open(filename, "rb") as f:
            protected_private_key = f.read()
    except IOError:
        sys.stderr.write("ERROR: Failed to read private key file 'private.pem (IO-Error)'.\n\n")
        sys.stderr.write(str(sys.exc_info()[1]) + "\n")
        sys.exit(1)
    except FileNotFoundError:
        sys.stderr.write("ERROR: Failed to read private key file 'private.pem (file does not exist)'.\n\n")
        sys.stderr.write(str(sys.exc_info()[1]) + "\n")
        sys.exit(1)

    # Get key pass phrase
    passphrase = getpass.getpass("Enter private-key passphrase: ")

    # instantiate RSA
    try:
        private_key = RSA.import_key(protected_private_key, passphrase=passphrase)
    except ValueError or TypeError or IndexError:
        sys.stderr.write("ERROR: Failed to use private key. Maybe the passphrase was wrong?\n\n")
    rsa_instance = PKCS1_OAEP.new(private_key)

    # Get fingerprint
    md5_instance = hashlib.md5()
    md5_instance.update(private_key.publickey().exportKey("DER"))
    public_key_fingerprint = md5_instance.hexdigest()
    key = [public_key_fingerprint, rsa_instance]
    return key


# End of functions declaration

# Start of the main function

print("Decrypting contact data for positive cases \n\n")

# An boolean set by the user to get the information
retrieve_contact = "YES"

# An empty dictionary to store all the private.pem files
key_files = {}

# Looking for the private.pem files in the current directory
# Listing all the files in the current directory
for file in os.listdir("../src/scripts"):
    # Checking if the private.pem file exists
    if file.endswith(".pem") and file.startswith("private"):
        # Extracting the fingerpring of the file
        file_fingerprint = file[8:-4]
        # Adding the file as the key and its finger print as the value in the dictionary
        key_files[file_fingerprint] = file
if not key_files:
    print("There is no key files in your directory! \n")
    retrieve_contact = "NO"

print(key_files)

while retrieve_contact.upper() == "YES":
    code = input("Please enter the barcode: ").strip().upper()

    # Print the batch file number and assigned event
    # batch_info = load_codes.batch_finder(code)
    # for record in batch_info[code]:
    #    print("Code %s of Event %s from batch file %s" %(code, record.name, record.batch_file))
    # An empty dictionary to store the key fingerprints of the given barcode
    key_dictionary = {}
    # Post request to get the information of the given barcode
    r = requests.get("https://covidtest-hd.de/extern/query/" + str(code))
    # Check if the response code is ok
    if r.status_code == 200:
        # Unpacking the response in a dictionary from the corresponding list
        result = r.json()

        if not result or result == {}:
            print("There is no record available with this barcode. Please check if you typed the barcode correctly.")
        elif "registrations" not in result or result["registrations"] == []:
            print("No registrations for barcode found")
        else:
            # Iterating over the stored data
            for i in range(len(result["registrations"])):
                registration_data = result["registrations"][i]

                # Fingerprint of the encoding key for the line i
                key_short_fingerprint = registration_data["key_information"]["public_key_fingerprint"][:6]

                if key_short_fingerprint not in key_files:
                    print("No key found for registration: ", key_short_fingerprint)
                else:
                    key_file = key_files[key_short_fingerprint]
                    decrypt_and_print(registration_data, key_file, code)

            retrieve_contact = input("Do you have another positive case (please answer with yes or no): ")

    else:
        print("Request failed with the status code: ", r.status_code)
