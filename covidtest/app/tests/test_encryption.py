from django.test import TestCase

import binascii
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from ..models import Sample, RSAKey, Bag
from ..encryption_helper import encrypt_subject_data, rsa_instance_from_key, decrypt_string


class EncryptionTestCase(TestCase):
    public_musterhausen = """-----BEGIN PUBLIC KEY-----
MIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAqLmkv8hfSOI2tWS8iTQ4
iseE0ijNyNq+38T7znLoK3SsxwKVujsIxFjGonp1BO8wxwdzQNVV7XeYS1W0i2ea
3h7uDJBWbDG31btcZHkcHew8POTBKDK24PcXNZqtNg3i72OxXR+dYYw0VXWAfLdw
alrWgmHW9n2bhP2CRbpKvKvwAfMd+Fg4K9RLNVzdAmqhLvbsv3jOlaFy6IU7HbKy
+a/Aiu2ql2LH4W7EEGuvLXpGJQvZTYoNq3XUJpu21mRSnsbto0534jzF7zxHUa+/
no/m4ZLQYSohOBvVYS4M/jLLp7ZET7SPMJ7zgJmrGHiPh/E+xdGIW+xqp7OV23xW
qXImn6gi/olvMGJ0IG3nPm0dl3juEIotAqF6F6CqSTXrAkxdLh7XAxighwEKje9L
pG074ITbdUvg3KeW5cz9tMRJO5Ve/ekplf+e39I6SBX9uwuC06ntWc2i3qh/ljpG
xkNg2AegGcT+ysU2uleSmkkSxs3VDYhRG8njYfzXchpVAgMBAAE=
-----END PUBLIC KEY-----"""

    private_musterhausen = """-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: DES-EDE3-CBC,191D65D4EB8A4FDE

xeUfwsSEznMn95fKGVbNZqt/Z+ha9OFeWe1m8dip97puMy0YwHvskBtz60o9QqO2
yHtS5MWnNep5KE3vlFd/qSpcYxPyVWRFa7l3gOjtKFEpOEgPp7Il6wRAelpxift4
B3w9rjPHV0YEkjPgubNwFHz9qq/0h21iAzfrAcb8orrkdsZTCC6Nff5mQjtYmQSE
jZk126tLJmwo5GPwG3RoZ8/kpK9UL4HcmXfZrF123uT1M7XGnX3jOU39quovGbmi
PfQ1UMkmmMp7UpcjVbdrVWr1WitHrmWpj4cyKHuW11a7UHfOTeJPDxAKLRL3Vkw9
t6ZJTJ5zhuYRRLspUKUyCFlzXWA2ky6G+iRNXvhnkmy0BLjuH1w0Jwp/23rpQjb8
DNAeNfGWwsrlRMH+w/RoAoJJPX5YxVSRDtWltZWXefeXdimCGWsibIfXnZJq0vhP
r1F/P6FMEilp3dE2Jj8xgiyFySLyW+ZY9mRljK3r9ZXcd8KJYG/wbk2hZFHAyPjW
3MndjdkD4ILdEQVduSZC38Jvpty1qjI99ow110u27tEqED0BUSetDey0bpRaYvXI
kBucqVjRK2E5QB46mhFvMK80M9uBiIwT2lX3qh4jhiWFQ6oqKhuafI7s63EdKU13
Dpt6d9OMYRSjt2EGxn2gEXlvuCSsjRPKZT2F7ZcuAtO8229bYm0fhraVLzxtOjMy
Bydre76Dzu2Sayhvl8/MyGJBqvO4MBTRc7CtxnPa75ZDRq+E8C/YeALk4LX1TvTF
RTcUmNhRVGTTg6QSC6YkNtHnqe1NT0M5dYzrOaB+HLw0jbry9iG/9C3hpI2mMoRH
22wb3MdTWqxUgkPoLt6myYyeR0LpmVBpYwDfibotSviZJIqO8Q7tXVfhJ5eay6jl
1GAU11NW81vIErkD2dAIVRU3EFQJ7Bx0a3ufAWMna1Fj5AKiJBUAXj+GBrfwe0R3
YUn9ORkITN3z0VGLDKxeJ0bmikz3RUJaTXVtZ58hJtPLLt/vPgaGICSkhSN1FInv
JH6jGkZrpmBfRQGcPye2d1cSlmCeDT9wHTWbqQ89yxuX62DhYll2q2fuI+5ujEvb
iU+T3l8Zp3k/dntgG9ZQcecDJ0SvWeL9XLcWbkVF9mz01CluKnYRQZFlDcY56dzh
zhHMJ6crJdo2isNKM5mVuR45ft8WBa08Q+hsUSMK7gew4D3/F2oBvnrks9SYAJd9
QzL0848q8Q5YgBWe+duq+DGLtwN5ZuvxF92JuTJseFbBe49872MR8+FhEbyH26a1
uaZlF6TM8ooES1zZfTBLksxBqJQtX1DvAR+6DftbjivrF0LC6DWN37Xyy6utqmPu
gjkbj8YIbkbNiDdaBTYpTDjAX2ck+tVwuGFVd9nAcRzJ7nLBsfxt47oPUx73bjXW
px68E5yZgaHTym6Me2HYn7JFtLcQD/FXNurD6xfswNyZ9sOMTI8OkJbFSFHf6J19
2JXYYwQeLziKMqnScgQ7913BpFpwshn4sXgLzBr/zzuxzUPTrMRDaOcWzs6nzea0
tEnCE4qaTaJBMkT0gkSlZHqvKpxdTNXM1ju86371TiHyUQJnjDQoDboqjy1/jsQ+
ZA4euJ+QSD2ceCetrzRSTriRlouUN/mg9HpftlxL79l24T0dS/EKDcxV7lWrxZ/O
3QxK/cKUqjqqzW3/wvw4QnI5CUBPCShfkVDR5ZyUpRydSQmvbmE2rfEwyYGHF3c/
BDT88lzqOUM4CRA6Kk7LYlTP+sQOLuoky4xvkSWIEUtuHjBbqf7r+iitr3Bc81iZ
YmccbFQI/C7c7EkO34nX2TjDfJidOGFJMyOnQfrFs6hRPox52qhN4jOExNvJ9wLw
qnOeqGAZ4JxEwGDXC21i/kpMgLtvMcvkF0aM3j92XR0h7rTRJN1YtpRPxrGG7v4p
bsWPS55B6rigik/lhSRMr6NRKL1rGHYI2C0l8v4CFCueN0sdzNHsl8HVAJsIqIFG
qh1hvCGWOEfSaMVs6YBqMxlLCkxJrkKolC8HDYazpDWAZpUsbtJJjT1Y5CUAcJsp
7MkMTbYO2cbb3CCtCL00pnklXFM0cKFPDMLQ0h+mR8+8mPBYaN6Iv/Z1hs+PXUmR
0c0EOv8FcU6MuATIpJ99IB/11E1PQGd7P92OT1NHhKDtIbgymt+qCWE5jXM0FSr7
VX1FMZ3S+2TAeIdg8scbyFJpJmxxvHMkl07KGWHrNwiuQnej8kWQ/ADKImkpWn8x
aWJYn1BiVGEY6hme3l9ocKNaeU7a/rT4p4FGQ4A9/7OJl7w3UYko+9aW+aT4rMhG
K+MIIE+GFzr1n4DY1a+RhndflMkBYpmv840ps3K4oIOf78evWI4hawwqeWA3yvHI
-----END RSA PRIVATE KEY-----"""

    def setUp(self):
        key = RSAKey.objects.create(
            key_name="Gesundheitsamt Musterhausen",
            comment="Gesundheitsamt Musterhausen\nMusterstraße 1\n10001 Musterstadt",
            public_key=self.public_musterhausen
        )

        bag = Bag.objects.create(
            name="12",
            comment="",
            rsa_key=key,
        )

        Sample.objects.create(
            barcode="123456789",
            access_code="123123123123",
            rack=None,
            password_hash=None,
            bag=bag,
        )

    def decrypt_str(aes_instance, string):
        item_encrypted = binascii.a2b_base64(string)
        item_decrypted = aes_instance.decrypt(item_encrypted)
        return item_decrypted.decode()

    def test_encrypt_sample_data(self):
        """Return None if no status set"""
        sample = Sample.objects.get(barcode="123456789")
        rsa_instance_alice = rsa_instance_from_key(sample.bag.rsa_key.public_key)
        doc = encrypt_subject_data(rsa_instance_alice, "Mustermann, Max", "Musterstraße 2, 10001 Musterstadt",
                                   "+49 1234 56789")

        private_key = RSA.import_key(self.private_musterhausen, passphrase="123")
        rsa_instance_bob = PKCS1_OAEP.new(private_key)
        aes_instance = AES.new(
            rsa_instance_bob.decrypt(binascii.a2b_base64(doc['session_key_encrypted'])),
            AES.MODE_CBC,
            iv=binascii.a2b_base64(doc['aes_instance_iv'])
        )

        name = aes_instance.decrypt(binascii.a2b_base64(doc['name_encrypted'])).decode()
        address = aes_instance.decrypt(binascii.a2b_base64(doc['address_encrypted'])).decode()
        contact = aes_instance.decrypt(binascii.a2b_base64(doc['contact_encrypted'])).decode()

        self.assertEqual(name.rstrip('\x00'), "Mustermann, Max")
        self.assertEqual(address.rstrip('\x00'), "Musterstraße 2, 10001 Musterstadt")
        self.assertEqual(contact.rstrip('\x00'), "+49 1234 56789")