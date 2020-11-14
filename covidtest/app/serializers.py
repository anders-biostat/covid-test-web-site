import random
import string

from rest_framework import serializers, validators

from .models import Bag, Event, Registration, RSAKey, Sample

"""Damm algorithm decimal check digit

For reference see https://en.wikipedia.org/wiki/Damm_algorithm
"""
matrix = (
    (0, 3, 1, 7, 5, 9, 8, 6, 4, 2),
    (7, 0, 9, 2, 1, 5, 4, 8, 6, 3),
    (4, 2, 0, 6, 8, 7, 1, 3, 5, 9),
    (1, 7, 5, 0, 9, 8, 3, 4, 2, 6),
    (6, 1, 2, 3, 0, 4, 5, 9, 7, 8),
    (3, 6, 7, 4, 2, 0, 9, 5, 8, 1),
    (5, 8, 6, 9, 7, 2, 0, 1, 3, 4),
    (8, 9, 4, 5, 3, 6, 2, 0, 1, 7),
    (9, 4, 3, 8, 6, 1, 7, 2, 0, 5),
    (2, 5, 8, 1, 4, 3, 6, 7, 9, 0),
)


def damm_check_digit(number):
    number = str(number)
    interim = 0
    for digit in number:
        interim = matrix[interim][int(digit)]
    return interim


def generate_access_code(size=12):
    exists = True
    while exists:
        access_code = "".join(random.choice(string.digits) for _ in range(size - 1))
        access_code = access_code + str(damm_check_digit(access_code))

        if Sample.objects.filter(access_code=access_code).count() == 0:
            exists = False
    return access_code


class RSAKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = RSAKey
        fields = ["id", "key_name", "comment", "public_key"]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "sample", "status", "comment", "updated_on", "updated_by"]


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = [
            "id",
            "sample",
            "time",
            "name_encrypted",
            "address_encrypted",
            "contact_encrypted",
            "public_key_fingerprint",
            "session_key_encrypted",
            "aes_instance_iv",
        ]


class SampleSerializer(serializers.ModelSerializer):
    registrations = RegistrationSerializer(many=True, read_only=True)
    events = EventSerializer(many=True, read_only=True)

    barcode = serializers.CharField(
        validators=[validators.UniqueValidator(queryset=Sample.objects.all(), message="duplicate")]
    )

    def create(self, validated_data):
        if "access_code" not in validated_data:
            validated_data["access_code"] = generate_access_code()
        return Sample.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        instance.content = validated_data.get("content", instance.content)
        instance.created = validated_data.get("created", instance.created)
        instance.save()
        return instance

    class Meta:
        model = Sample
        extra_kwargs = {"access_code": {"required": False}}
        fields = ["id", "barcode", "access_code", "bag", "rack", "password_hash", "registrations", "events"]
        optional_fields = ["access_code", "bag", "rack", "password_hash", "registrations", "events"]


class BagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bag
        fields = ["id", "name", "comment", "rsa_key"]


class KeySamplesSerializers(serializers.ModelSerializer):
    samples = SampleSerializer(many=True, read_only=True)

    class Meta:
        model = RSAKey
        fields = ["id", "key_name", "samples"]
