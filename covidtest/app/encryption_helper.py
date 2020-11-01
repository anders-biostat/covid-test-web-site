import Crypto.PublicKey.RSA, Crypto.Cipher.PKCS1_OAEP
import hashlib, binascii


def rsa_instance(public_key_txt):
    # Read public key for encryption of contact information
    public_key = Crypto.PublicKey.RSA.import_key(public_key_txt)
    rsa_instance = Crypto.Cipher.PKCS1_OAEP.new(public_key)

    # Get fingerprint of public key
    md5_instance = hashlib.md5()
    md5_instance.update(public_key.publickey().exportKey("DER"))
    rsa_instance.public_key_fingerprint = md5_instance.hexdigest().encode("ascii")
    return rsa_instance


def binary_to_ascii(binary):
    return binascii.b2a_base64(binary, newline=False).decode('ascii')


def encrypt_string(string, aes_instance, fmt=str):
    bytes_string = string.encode('utf-8')
    if len(bytes_string) % 16 != 0:
        bytes_string += b'\000' * (16 - len(bytes_string) % 16)
    encrypted_bytes = aes_instance.encrypt(bytes_string)
    encrypted_string = binary_to_ascii(encrypted_bytes)
    if fmt == str:
        return encrypted_string
    if fmt == bytes:
        return encrypted_bytes
    else:
        return encrypted_string


def decrypt_string(string, aes_instance, fmt=str):
    decoded = binascii.a2b_base64(string)
    decrypted_bytes = aes_instance.decrypt(decoded)
    decrypted_string = decrypted_bytes.decode('ascii')
    if fmt == str:
        return decrypted_string
    if fmt == bytes:
        return decrypted_bytes
    else:
        return decrypted_string


def encode_subject_data(rsa_instance, name, address, contact, password):
    # Generate session key for use with AES and encrypt it with RSA
    session_key = Crypto.Random.get_random_bytes(16)
    encrypted_session_key = rsa_instance.encrypt(session_key)
    aes_instance = Crypto.Cipher.AES.new(session_key, Crypto.Cipher.AES.MODE_CBC)

    # encode user password with SHA3
    sha_instance = hashlib.sha3_384()
    sha_instance.update(password.encode("utf-8"))
    password_hash = sha_instance.digest()

    name_encrypted = encrypt_string(name, aes_instance)
    address_encrypted = encrypt_string(address, aes_instance)
    contact_encrypted = encrypt_string(contact, aes_instance)

    return {
        'name_encrypted': name_encrypted,
        'address_encrypted': address_encrypted,
        'contact_encrypted': contact_encrypted,
        'password_hash': binary_to_ascii(password_hash),
        'public_key_fingerprint': rsa_instance.public_key_fingerprint.decode("ascii"),
        'session_key_encrypted': binary_to_ascii(encrypted_session_key),
        'aes_instance_iv': binary_to_ascii(aes_instance.iv),
    }
