import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .statuses import SampleStatus


class Timestamp(models.Model):
    """
    Abstract Model to give Models where it's used on extra
    Functionality.
    """

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def changed(self):
        return True if self.updated_on else False

    def save(self, *args, **kwargs):
        if self.pk:
            self.updated_on = timezone.now()
        return super(Timestamp, self).save(*args, **kwargs)


class RSAKey(models.Model):
    key_name = models.CharField(max_length=50)
    comment = models.TextField(null=True, blank=True)
    public_key = models.TextField(null=False, blank=False)

    def __str__(self):
        return "RSAKey: %s" % self.key_name


class Bag(models.Model):
    name = models.CharField(max_length=100)
    comment = models.TextField(null=True, blank=True)
    rsa_key = models.ForeignKey(RSAKey, on_delete=models.DO_NOTHING, related_name="bags")
    def __str__(self):
        return "Bag #%d ('%s')" % (self.pk, self.name)


class Sample(models.Model):
    barcode = models.CharField(max_length=50)
    access_code = models.CharField(max_length=50)
    rack = models.CharField(max_length=50, blank=True, null=True)
    password_hash = models.CharField(max_length=200, blank=True, null=True)
    bag = models.ForeignKey(Bag, on_delete=models.DO_NOTHING, related_name="samples")

    def set_status(self, status, comment=None, author=None):
        if type(status) == SampleStatus:
            status = status.value
        self.events.create(
            status=status,
            updated_by=author,
            comment=comment
        )
        return status

    def get_statuses(self):
        return self.events.order_by("updated_on")

    def get_latest_external_status(self):
        """External user facing status event"""
        return self.get_statuses().exclude(
            status=SampleStatus.INFO.value
        ).exclude(
            status=SampleStatus.PCRSENT.value
        ).last()

    def get_latest_internal_status(self):
        """Internal staff facing events"""
        return self.get_statuses().exclude(
            status=SampleStatus.INFO.value
        ).last()

    def __str__(self):
        return "%s" % self.barcode


class Registration(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name="registrations")
    time = models.DateTimeField(auto_now_add=True, blank=True)
    name_encrypted = models.CharField(max_length=200)
    address_encrypted = models.CharField(max_length=200)
    contact_encrypted = models.CharField(max_length=200)
    public_key_fingerprint = models.CharField(max_length=200)
    session_key_encrypted = models.CharField(max_length=1000)
    aes_instance_iv = models.CharField(max_length=200)


class Event(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=50)
    comment = models.TextField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now_add=True, blank=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)


class Consent(models.Model):
    consent_type = models.CharField(max_length=50)
    md5 = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True,)
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name="consents")


class News(Timestamp, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    comment = models.TextField(blank=True, null=True)
    relevant = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "News"
