from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from djongo import models
from django.core.validators import URLValidator


class KeyInformation(models.Model):
    public_key_fingerprint = models.TextField()
    session_key_encrypted = models.TextField()
    aes_instance_iv = models.TextField()
    class Meta:
        abstract = True


class Registration(models.Model):
    _id = models.ObjectIdField()
    barcode = models.TextField()
    time = models.DateTimeField()
    name_encrypted = models.TextField()
    address_encrypted = models.TextField()
    contact_encrypted = models.TextField()
    password_hash = models.TextField()
    key_information = models.EmbeddedField(
        model_container=KeyInformation
    )
    class Meta:
        abstract = True


class Sample(models.Model):
    _id = models.ObjectIdField()
    barcode = models.TextField()
    batch = models.TextField()
    rack = models.TextField()
    registrations = models.ArrayField(
        model_container=Registration
    )


class Result(models.Model):
    status = models.TextField()
    updated_on = models.DateTimeField()
    updated_by = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    class Meta:
        abstract = True