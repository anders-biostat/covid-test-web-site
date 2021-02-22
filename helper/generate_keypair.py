#!/usr/bin/python3

import getpass
import hashlib
import sys

import Crypto.PublicKey.RSA

passphrase = getpass.getpass("Enter a passphrase to protect the secret key: ")
passphrase_repeat = getpass.getpass("Enter the passphrase again: ")

if passphrase != passphrase_repeat:
    sys.stderr.write("The passphrases differ. Aborting.")
    sys.exit(1)

if passphrase == "":
    passphrase = None
    print("You have entered an empty passphrase. You private key will not get encrypted.")

print("Generating key pair.")
key = Crypto.PublicKey.RSA.generate(4096)

# Get fingerprint
md5_instance = hashlib.md5()
md5_instance.update(key.publickey().exportKey("DER"))
public_key_fingerprint = md5_instance.hexdigest()

print("RSAKey pair generated. RSAKey fingerprint: %s." % public_key_fingerprint)

filename = "private_%s.pem" % public_key_fingerprint[:6]
with open(filename, "wb") as f:
    f.write(key.export_key(passphrase=passphrase))
    print("Saved keypair as %s. Keep this file secret." % filename)

filename = "public_%s.pem" % public_key_fingerprint[:6]
with open(filename, "wb") as f:
    f.write(key.publickey().export_key())
    print("Saved public key as %s. Use this file for encryption on web server." % filename)
