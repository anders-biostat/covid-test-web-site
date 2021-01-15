from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Bag, Event, Registration, RSAKey, Sample
from ..statuses import SampleStatus


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
        -----END PUBLIC KEY-----""",
        )

        bag = Bag.objects.create(
            name="Bag 1",
            comment="This is a test bag",
            rsa_key=key,
        )

        self.sample = Sample.objects.create(
            barcode="1234",
            access_code=self.regforminput["access_code"],
            rack="abc",
            password_hash=None,
            bag=bag,
        )

    regforminput = {
        "access_code": "123412341234",
        "name": "Mustermann, Maximilian",
        "address": "Musterstraße 1, Musterstadt",
        "contact": "+49 0123 123 123",
    }

    def query_access_code(self):
        return self.client.post(
            reverse("app:results_query"), {"access_code": self.regforminput["access_code"]}, follow=True
        )

    def register_access_code(self):
        session = self.client.session
        session["age"] = 20
        session["consent"] = "consent_adult"
        session.save()
        response = self.client.post(reverse("app:register"), self.regforminput)

    def test_result_negative_unregistered(self):
        self.sample.set_status(SampleStatus.LAMPNEG)
        response = self.query_access_code()
        self.assertRedirects(response, reverse("app:consent_age"))
        self.assertContains(response, "wurde noch nicht registriert")

    def test_result_negative(self):
        self.sample.set_status(SampleStatus.LAMPNEG)

        self.register_access_code()
        response = self.query_access_code()
        self.assertContains(response, "nicht </strong> nachgewiesen")

    def test_result_negative_after_PCR(self):
        self.sample.set_status(SampleStatus.LAMPPOS)
        self.sample.set_status(SampleStatus.PCRNEG)

        self.register_access_code()
        response = self.query_access_code()
        self.assertContains(response, "nicht </strong> nachgewiesen")
        self.assertTemplateUsed(response, "public/pages/test-PCRNEG.html")

    def test_result_positive(self):
        self.sample.set_status(SampleStatus.LAMPPOS)
        self.sample.set_status(SampleStatus.PCRPOS)

        self.register_access_code()
        response = self.query_access_code()
        self.assertTemplateUsed(response, "public/pages/test-PCRPOS.html")
