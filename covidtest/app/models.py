from django.db import models
from .statuses import SampleStatus

class Key(models.Model):
    key_name = models.CharField(max_length=50)
    comment = models.TextField(null=True, blank=True)
    public_key = models.TextField(null=False, blank=False)

    def __str__(self):
        return "Key: %s" % self.key_name


class Sample(models.Model):
    barcode = models.CharField(max_length=50)
    batch = models.CharField(max_length=50)
    rack = models.CharField(max_length=50)
    key = models.ForeignKey(Key, on_delete=models.DO_NOTHING, related_name='samples')

    def set_status(self, status, author=None):
        if type(status) == SampleStatus:
            status = status.value
        event = Event(
            status=status,
            updated_by=author
        )
        status_updated = self.modify(push__events=event)
        return status_updated

    def get_statuses(self):
        events = self.events
        return [event for event in events if event.status != 'INFO']

    def get_status(self):
        statuses = self.get_statuses()
        if len(statuses) == 0:
            return None
        else:
            return statuses[-1]


class Registration(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='registrations')
    time = models.DateTimeField(auto_now_add=True, blank=True)
    name_encrypted = models.CharField(max_length=200)
    address_encrypted = models.CharField(max_length=200)
    contact_encrypted = models.CharField(max_length=200)
    password_hash = models.CharField(max_length=200)
    public_key_fingerprint = models.CharField(max_length=200)
    session_key_encrypted = models.CharField(max_length=1000)
    aes_instance_iv = models.CharField(max_length=200)

class Event(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=50)
    comment = models.TextField()
    updated_on = models.DateTimeField(auto_now_add=True, blank=True)