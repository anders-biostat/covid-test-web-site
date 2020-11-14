from django.test import TestCase
from ..models import Sample, RSAKey, Bag, Event


class SampleTestCase(TestCase):
    def setUp(self):
        key = RSAKey.objects.create(
            key_name="Gesundheitsamt Musterhausen",
            comment="Gesundheitsamt Musterhausen\nMusterstraße 1\n10001 Musterstadt",
            public_key= """-----BEGIN PUBLIC KEY-----
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
        )

        bag = Bag.objects.create(
            name="12",
            comment="",
            rsa_key=key,
        )

        Sample.objects.create(
            barcode="123456789",
            access_code="123123123123",
            rack="1",
            password_hash=None,
            bag=bag,
        )

    def test_sample_status(self):
        """Return None if no status set"""
        sample = Sample.objects.filter(barcode="123456789").first()
        self.assertEqual(sample.get_status(), None)
        self.assertEqual(sample.get_statuses().count(), 0)
        pass
