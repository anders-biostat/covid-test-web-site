from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Bag, Event, Registration, RSAKey, Sample, Consent


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
            access_code=self.form_input["access_code"],
            rack="abc",
            password_hash=None,
            bag=bag,
        )

    @classmethod
    def setUpTestData(cls):
        cls.form_input = {
            "access_code": "123412341234",
            "name": "Mustermann, Maximilian",
            "address": "Musterstraße 1, Musterstadt",
            "contact": "+49 0123 123 123",
        }

    def test_registration_form_no_consent(self):
        response = self.client.post(reverse("app:register"), self.form_input)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("app:consent"), target_status_code=302)

    def test_redirects_to_age_if_no_age(self):
        response = self.client.get(reverse("app:consent"))
        self.assertRedirects(response, reverse("app:consent_age"))

    def test_age_is_set(self):
        age = 12
        response = self.client.post(reverse("app:consent_age"), dict(age=age))
        self.assertEqual(self.client.session["age"], age)

    def test_age_invalid(self):
        age = 1
        response = self.client.post(reverse("app:consent_age"), dict(age=age))
        self.assertEqual(self.client.session.get("age"), None)
        self.assertEqual(len(response.context["messages"]), 1)

    def test_success_adult_register(self):
        session = self.client.session
        session["age"] = 20
        session.save()
        response = self.client.get(reverse("app:consent"))
        response = self.post_consent("consent_adult", self.get_form_version(response))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("app:register"))

    def ensure_template_is_correct(self, response, consent_type, template_name):
        ctx = response.context
        self.assertEqual(ctx["form"]["consent_type"].value(), consent_type)
        self.assertEqual(ctx["template_name"], template_name)

    def post_consent(self, consent_type, version):
        return self.client.post(
            reverse("app:consent"),
            dict(terms=True, consent_type=consent_type, version=version),
        )

    def test_success_teenager_register(self):
        session = self.client.session
        session["age"] = 14
        session.save()
        response = self.client.get(reverse("app:consent"))
        self.ensure_template_is_correct(response, "consent_parent", "public/information-parents.html")
        response = self.post_consent("consent_parent", self.get_form_version(response))
        self.ensure_template_is_correct(response, "consent_teenager", "public/information-teenager.html")
        response = self.post_consent("consent_teenager", self.get_form_version(response))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("app:register"))

    def test_success_child_register(self):
        session = self.client.session
        session["age"] = 7
        session.save()
        response = self.client.get(reverse("app:consent"))
        self.ensure_template_is_correct(response, "consent_parent", "public/information-parents.html")
        response = self.post_consent("consent_parent", self.get_form_version(response))
        self.ensure_template_is_correct(response, "consent_child", "public/information-child.html")
        response = self.post_consent("consent_child", self.get_form_version(response))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("app:register"))

    def test_consent_not_given(self):
        session = self.client.session
        session["age"] = 7
        session.save()
        ## no consent, show message, same parent form
        response = self.client.post(reverse("app:consent"), dict(consent_type="consent_parent"))
        ctx = response.context
        self.assertEqual(len(ctx["messages"]), 1)
        self.assertEqual(ctx["form"]["consent_type"].value(), "consent_parent")
        self.assertEqual(ctx["template_name"], "public/information-parents.html")

    def test_registration_with_consent(self):
        session = self.client.session
        session["age"] = 20
        session["consent"] = ["consent_adult"]
        session["consent_md5"] = {"consent_adult": "consent_adult_md5"}
        session.save()

        sample = Sample.objects.filter(access_code=self.form_input["access_code"]).first()
        self.assertEqual(sample.registrations.count(), 0)
        response = self.client.post(reverse("app:register"), self.form_input)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("app:instructions"))
        self.assertEqual(sample.registrations.count(), 1)

    def get_form_version(self, response):
        return response.context["form"]["version"].value()

    def test_md5_consent_sum_is_saved(self):
        session = self.client.session
        session["age"] = 7
        session["consent"] = ["consent_parent", "consent_child"]
        session["consent_md5"] = {
            "consent_child": "consent_child_md5",
            "consent_parent": "consent_parent_md5",
        }
        session.save()
        response = self.client.post(reverse("app:register"), self.form_input)
        consents = Consent.objects.all()
        self.assertEqual(consents[0].consent_type, "consent_parent")
        self.assertEqual(consents[0].md5, "consent_parent_md5")
        self.assertEqual(consents[1].consent_type, "consent_child")
        self.assertEqual(consents[1].md5, "consent_child_md5")
