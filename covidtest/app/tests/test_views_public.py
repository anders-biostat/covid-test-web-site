from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Sample, Registration, Event, RSAKey, Bag


class TestRegistration(TestCase):
    def setUp(self):
        key = RSAKey.objects.create(
            key_name="Gesundheitsamt Musterhausen",
            comment="Gesundheitsamt Musterhausen\nMusterstraße 1\n10001 Musterstadt",
            public_key="""-----BEGIN PUBLIC KEY-----
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
            name="Bag 1",
            comment="This is a test bag",
            rsa_key=key,
        )

        self.sample = Sample.objects.create(
            barcode='1234',
            access_code='123412341234',
            rack='abc',
            password_hash=None,
            bag=bag,
        )

    def test_registration_form_no_consent(self):
        form_input = {
            'access_code': '123412341234',
            'name': 'Mustermann, Maximilian',
            'address': 'Musterstraße 1, Musterstadt',
            'contact': '+49 0123 123 123'
        }

        response = self.client.post(reverse('app:register'), form_input)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('app:consent'))

    def test_consent_given(self):
        consent_before = self.client.session.get('consent')
        form_input = {
            'terms': 1,
        }
        response = self.client.post(reverse('app:consent'), form_input)
        consent_after = self.client.session.get('consent')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('app:register'))

        self.assertEqual(consent_before, None)
        self.assertEqual(consent_after, True)



    def test_consent_not_given(self):
        form_input = {
        }
        response = self.client.post(reverse('app:consent'), form_input)
        self.assertEqual(response.status_code, 200)

    def test_registration_with_consent(self):
        session = self.client.session
        session['consent'] = True
        session.save()

        sample = Sample.objects.filter(access_code='123412341234').first()
        self.assertEqual(sample.registrations.count(), 0)
        form_input = {
            'access_code': '123412341234',
            'name': 'Mustermann, Maximilian',
            'address': 'Musterstraße 1, Musterstadt',
            'contact': '+49 0123 123 123'
        }
        response = self.client.post(reverse('app:register'), form_input)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('app:instructions'))
        self.assertEqual(sample.registrations.count(), 1)
