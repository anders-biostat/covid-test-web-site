from django.test import TestCase
from django.test import Client 
from django.contrib.auth.models import User
from django.urls import get_resolver



class CallLabURLs(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin",
            password="admin",
            email="test@this.com")

    def CallAllLabPages(self):
        c = Client()
        c.force_login(self.user)
        response = c.get('/lab')
        self.assertEqual(response.status_code, 200)
        
       