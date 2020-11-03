from django.contrib import admin
from .models import Sample, Registration, Event, RSAKey, Bag

admin.site.register([Sample, Registration, Event, RSAKey, Bag])