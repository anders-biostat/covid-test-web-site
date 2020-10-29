from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from djongo import models
from django.core.validators import URLValidator


class Sample(models.Model):
    class Meta:
        abstract=True
    _id = models.ObjectIdField()
    barcode = models.CharField(max_length=50)
    batch = models.CharField(max_length=50)
    rack = models.CharField(max_length=50)


class Result(models.Model):
    status = models.CharField(max_length=50)
    updated_on = models.DateTimeField()
    updated_by = models.ForeignKey('auth.User', on_delete=models.PROTECT)

class Registration(models.Model):
    _id = models.ObjectIdField()
    sample = models.ArrayField(
        model_container=Sample
    )
    barcode = models.CharField(max_length=50)
    time = models.DateTimeField(max_length=50)
    name_encrypted = models.CharField(max_length=50)
    address_encrypted = models.CharField(max_length=50)
    contact_encrypted = models.CharField(max_length=50)
    password_hash = models.CharField(max_length=50)


class KeyInformation(models.Model):
    registration = models.EmbeddedField(
        model_container=Registration
    )
    public_key_fingerprint = models.CharField(max_length=50)
    session_key_encrypted = models.CharField(max_length=50)
    aes_instance_iv = models.CharField(max_length=50)