import mongoengine
import datetime
from .statuses import SampleStatus

mongoengine.connect('covidtest')

class Registration(mongoengine.EmbeddedDocument):
    barcode = mongoengine.StringField(null=True)
    time = mongoengine.DateTimeField(null=True)
    name_encrypted = mongoengine.StringField(null=True)
    address_encrypted = mongoengine.StringField(null=True)
    contact_encrypted = mongoengine.StringField(null=True)
    password_hash = mongoengine.StringField(null=True)
    public_key_fingerprint = mongoengine.StringField(null=True)
    session_key_encrypted = mongoengine.StringField(null=True)
    aes_instance_iv = mongoengine.StringField(null=True)


class Event(mongoengine.EmbeddedDocument):
    status = mongoengine.StringField(required=True)
    comment = mongoengine.StringField(null=True)
    updated_on = mongoengine.DateTimeField(default=datetime.datetime.now)
    updated_by = mongoengine.StringField(null=True)


class Sample(mongoengine.Document):
    barcode = mongoengine.StringField(primary_key=True)
    batch = mongoengine.StringField(null=True)
    rack = mongoengine.StringField(null=True)
    registrations = mongoengine.ListField(mongoengine.EmbeddedDocumentField(Registration))
    events = mongoengine.ListField(mongoengine.EmbeddedDocumentField(Event))
    meta = {'collection': 'Samples'}

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

