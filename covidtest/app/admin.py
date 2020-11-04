from django.contrib import admin
from .models import Sample, Registration, Event, RSAKey, Bag

admin.site.site_header = "COVID-19 LAB ADMIN"
admin.site.site_title = "COVID-19 LAB ADMIN"
admin.site.index_title = "Admin"

admin.site.register([Sample, Registration, Event, RSAKey, Bag])