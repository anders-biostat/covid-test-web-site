from django.contrib import admin
from .models import Sample, Registration, Event, Key

admin.site.register([Sample, Registration, Event, Key])