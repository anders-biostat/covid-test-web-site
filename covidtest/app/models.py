import uuid

from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.utils import timezone

from .statuses import SampleStatus


class Timestamp(models.Model):
    """
    Abstract Model to give Models where it's used on extra
    Functionality.
    """

    created_on = models.DateTimeField(auto_now_add=True, null=True)
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


class BagRecipient(Timestamp, models.Model):
    class RecipientTypes(models.TextChoices):
        INSTITUTION = "offers tests regularly to their staff", "Institution"
        TEACHING_EVENT = (
            "one-off or recurring event where students are tested",
            "Teaching Event",
        )
        ONE_OFF_EVENT = "invoice goes to the organizer of the event", "One-Off Event"
        INTERNAL = "bag goes to internal", "Internal"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient_name = models.CharField(max_length=255)
    recipient_type = models.CharField(
        max_length=255, choices=RecipientTypes.choices, blank=True, null=True
    )
    name_contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    telephone = models.CharField(max_length=255, null=True, blank=True)
    billing_address = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"NAME: {self.recipient_name} ,TYPE: {self.get_recipient_type_display()}"


class Bag(Timestamp, models.Model):
    name = models.CharField(max_length=100)
    comment = models.TextField(null=True, blank=True)
    rsa_key = models.ForeignKey(
        RSAKey, on_delete=models.DO_NOTHING, related_name="bags"
    )
    recipient = models.ForeignKey(
        BagRecipient,
        on_delete=models.DO_NOTHING,
        related_name="bag_of_recipient",
        null=True,
        blank=True,
    )
    handed_out_on = models.DateTimeField(null=True, blank=True)
    handed_out_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, null=True, blank=True
    )

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
        self.events.create(status=status, updated_by=author, comment=comment)
        return status

    def get_statuses(self):
        return self.events.order_by("updated_on")

    def get_latest_external_status(self):
        """External user facing status event"""
        return (
            self.get_statuses()
            .exclude(status="SampleStatus.INFO")
            .last()
        )

    def get_latest_internal_status(self):
        """Internal staff facing events"""
        return self.get_statuses().exclude(status="SampleStatus.INFO").last()

    def __str__(self):
        return "%s" % self.barcode


class Registration(models.Model):
    sample = models.ForeignKey(
        Sample, on_delete=models.CASCADE, related_name="registrations"
    )
    time = models.DateTimeField(auto_now_add=True if not settings.PRIVACY_MODE else False, blank=True, null=True)
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
    updated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )


class Consent(models.Model):
    consent_type = models.CharField(max_length=50)
    md5 = models.CharField(max_length=200)
    date = models.DateTimeField(
        auto_now_add=True,
    )
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="consents"
    )


class News(Timestamp, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    comment = models.TextField(blank=True, null=True)
    relevant = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "News"
