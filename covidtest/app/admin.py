from django.contrib import admin
from .models import Sample, Registration, Event, RSAKey

admin.site.register([Sample, Registration, Event, RSAKey])