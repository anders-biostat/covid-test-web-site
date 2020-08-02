import sys, binascii, hashlib, time
import Crypto.PublicKey.RSA, Crypto.Random, Crypto.Cipher.AES, Crypto.Cipher.PKCS1_OAEP

# This file writes out a CSV line to store the folloing example user data,
# that may have been entered in the web form:

sample_data = {
	"barcode":  "ABCDEF",
	"name":     "Erika Musterfrau",
	"address":  "Teststr. 17, Testingen",
	"contact":  "0176-123456789",
	"password": "ErikasPW" 
}


# Read public key for encryption of contact information
with open( "public.pem", "rb" ) as f:
   public_key = Crypto.PublicKey.RSA.import_key( f.read() )

# Generate session key and encrypt it with RSA, then use it with AES
session_key = Crypto.Random.get_random_bytes( 16 )    # <- check: do we have enough entropy?
pkcs1_instance = Crypto.Cipher.PKCS1_OAEP.new( public_key )
encrypted_session_key = pkcs1_instance.encrypt( session_key )
aes_instance = Crypto.Cipher.AES.new( session_key, Crypto.Cipher.AES.MODE_CBC )  

# encode, pad, then encrypt subject data 
encrypted_subject_data = []
for s in [ sample_data["name"], sample_data["address"], sample_data["contact"] ]:
   s = s.encode( "utf-8" )
   if len(s) % 16 != 0:
      s += b'\000' * ( 16 - len(s) % 16 )
   encrypted_subject_data.append( aes_instance.encrypt( s ) )

# encode user password with SHA3
sha_instance = hashlib.sha3_384()
sha_instance.update( sample_data["password"].encode( "utf-8" ) )
password_hash = sha_instance.digest()

# Make a line for the CSV file
fields = [ 
   sample_data["barcode"].encode( "utf-8" ), 
   time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime() ).encode( "utf-8" ),
   password_hash,
   encrypted_session_key,
   aes_instance.iv ]
fields.extend( encrypted_subject_data )

# Base64-endode everything exepct for password and time stamp
for i in range( 2, len(fields) ):
	fields[i] = binascii.b2a_base64( fields[i], newline=False )

# Make line for file
line = b",".join( fields )

sys.stdout.buffer.write( line )
print()

###########

