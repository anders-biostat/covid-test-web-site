import sys, binascii, hashlib
import Crypto.PublicKey.RSA, Crypto.Random, Crypto.Cipher.AES, Crypto.Cipher.PKCS1_OAEP


# Read public key for encryption of contact information
with open( "public.pem", "rb" ) as f:
   public_key = Crypto.PublicKey.RSA.import_key( f.read() )

# Data colected from web form:
sample_data = {
	"barcode":  "ABCDEF",
	"subject":  "Erika Musterfrau, Teststr. 17, Testingen, 0176-123456789",
	"password": "ErikasPW" 
}

# generate session key and encrypt it with RSA, then use it with AES
session_key = Crypto.Random.get_random_bytes( 16 )    # <- check: do we have enough entropy?
pkcs1_instance = Crypto.Cipher.PKCS1_OAEP.new( public_key )
encrypted_session_key = pkcs1_instance.encrypt( session_key )
aes_instance = Crypto.Cipher.AES.new( session_key, Crypto.Cipher.AES.MODE_CBC )  

# encocde, pad, then encrypt subject data
a = sample_data["subject"].encode( "utf-8" )
a += b'\000' * ( len(a) % 16 )
encrypted_subject_data = aes_instance.encrypt( a )

# encode user password with SHA3
sha_instance = hashlib.sha256()
sha_instance.update( sample_data["password"].encode( "utf-8" ) )

line = b",".join(( 
	sample_data["barcode"].encode("utf-8"),
    binascii.b2a_base64( sha_instance.digest(), newline=False ),
	binascii.b2a_base64( encrypted_subject_data, newline=False ),
	binascii.b2a_base64( encrypted_session_key, newline=False ),
	binascii.b2a_base64( aes_instance.iv, newline=False )
))

sys.stdout.buffer.write( line )
print()

###########

