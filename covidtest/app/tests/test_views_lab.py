from django.test import TestCase

from django.test import Client 
from django.contrib.auth.models import User

class CallLabURLs(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin",
            password="admin",
            email="test@this.com")
        self.ListOfUrls = ['/lab','/lab/checkin','/lab/rack', '/lab/dashboard']

    # no login should lead to redirect
    def test_callLabPages(self):
        c = Client()
        for url in self.ListOfUrls:
            print(url)
            response = c.get(url)
            self.assertEqual(response.status_code, 302)
        
    def test_callLabPages_login(self):
        c = Client()
        c.force_login(self.user)
        for url in self.ListOfUrls:
            response = c.get(url)
            self.assertEqual(response.status_code, 200)
        c.logout()
