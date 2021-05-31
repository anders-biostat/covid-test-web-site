from django.contrib import admin

from .models import (
    Bag,
    Event,
    Registration,
    RSAKey,
    Sample,
    Consent,
    News,
    BagRecipient,
)

admin.site.site_header = "COVID-19 LAB ADMIN"
admin.site.site_title = "COVID-19 LAB ADMIN"
admin.site.index_title = "Admin"


class SampleAdmin(admin.ModelAdmin):
    list_display = ("pk", "barcode", "access_code", "rack", "bag", "password_hash")
    search_fields = ("barcode", "access_code", "rack", "bag__name")


class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("sample", "time", "public_key_fingerprint")
    search_fields = ("sample__barcode",)


class EventAdmin(admin.ModelAdmin):
    list_display = ("sample", "status", "comment", "updated_on", "updated_by")
    search_fields = ("sample__barcode", "status")


class RSAKeyAdmin(admin.ModelAdmin):
    list_display = ("key_name", "comment")


class BagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "rsa_key", "comment")


class ConsentAdmin(admin.ModelAdmin):
    list_display = ("registration", "consent_type", "md5", "date")


class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "created_on", "updated_on")


#
class SampleRecipientAdmin(admin.ModelAdmin):
    list_display = (
        "recipient_name",
        "get_recipient_type_display",
        "name_contact_person",
        "email",
        "telephone",
    )


admin.site.register(Sample, SampleAdmin)
admin.site.register(Registration, RegistrationAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(RSAKey, RSAKeyAdmin)
admin.site.register(Bag, BagAdmin)
admin.site.register(Consent, ConsentAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(BagRecipient, SampleRecipientAdmin)
