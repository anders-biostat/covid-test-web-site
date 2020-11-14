from django.contrib import admin

from .models import Bag, Event, Registration, RSAKey, Sample

admin.site.site_header = "COVID-19 LAB ADMIN"
admin.site.site_title = "COVID-19 LAB ADMIN"
admin.site.index_title = "Admin"


class SampleAdmin(admin.ModelAdmin):
    list_display = ("barcode", "access_code", "rack", "bag", "password_hash")


class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("sample", "time", "public_key_fingerprint")


class EventAdmin(admin.ModelAdmin):
    list_display = ("sample", "status", "comment", "updated_on", "updated_by")


class RSAKeyAdmin(admin.ModelAdmin):
    list_display = ("key_name", "comment")


class BagAdmin(admin.ModelAdmin):
    list_display = ("name", "rsa_key", "comment")


admin.site.register(Sample, SampleAdmin)
admin.site.register(Registration, RegistrationAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(RSAKey, RSAKeyAdmin)
admin.site.register(Bag, BagAdmin)
