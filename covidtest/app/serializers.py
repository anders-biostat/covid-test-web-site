from rest_framework import serializers
from .models import Key, Sample, Event, Registration


class KeySerializer(serializers.ModelSerializer):
    class Meta:
        model = Key
        fields = ['key_name', 'comment', 'public_key']


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['sample', 'status', 'comment', 'updated_on']


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ['sample', 'time', 'name_encrypted', 'address_encrypted', 'contact_encrypted', 'password_hash',
                  'public_key_fingerprint', 'session_key_encrypted', 'aes_instance_iv']


class SampleSerializer(serializers.ModelSerializer):
    key = KeySerializer()
    registrations = RegistrationSerializer(many=True, read_only=True)
    events = EventSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        fields = ['id', 'barcode', 'batch', 'rack', 'key', 'registrations', 'events']

class KeySamplesSerializers(serializers.ModelSerializer):
    samples = SampleSerializer(many=True, read_only=True)
    class Meta:
        model = Key
        fields = ['id', 'key_name', 'samples']