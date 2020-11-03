from rest_framework import serializers
from .models import RSAKey, Sample, Event, Registration, Bag


class RSAKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = RSAKey
        fields = ['key_name', 'comment', 'public_key']


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['sample', 'status', 'comment', 'updated_on']


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ['sample', 'time', 'name_encrypted', 'address_encrypted', 'contact_encrypted', 
                  'public_key_fingerprint', 'session_key_encrypted', 'aes_instance_iv']


class SampleSerializer(serializers.ModelSerializer):
    registrations = RegistrationSerializer(many=True, read_only=True)
    events = EventSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        fields = ['id', 'barcode', 'access_code', 'bag', 'rack', 'password_hash', 'registrations', 'events']

class BagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bag
        fields = ['name', 'comment', 'rsa_key']



#class KeySamplesSerializers(serializers.ModelSerializer):
#    samples = SampleSerializer(many=True, read_only=True)
#    class Meta:
#        model = RSAKey
#        fields = ['id', 'key_name', 'samples']