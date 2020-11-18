from rest_framework import permissions, viewsets

from .models import Bag, Event, Registration, RSAKey, Sample
from .serializers import (
    BagSerializer,
    EventSerializer,
    KeySamplesSerializers,
    RegistrationSerializer,
    RSAKeySerializer,
    SampleSerializer,
)


class SampleViewSet(viewsets.ModelViewSet):
    serializer_class = SampleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Sample.objects.all()
        barcode = self.request.query_params.get("barcode", None)
        access_code = self.request.query_params.get("access_code", None)
        if not barcode and not access_code:
            return queryset.none()
        if barcode:
            queryset = queryset.filter(barcode=barcode)
        if access_code:
            queryset = queryset.filter(access_code=access_code)
        return queryset


class RSAKeyViewSet(viewsets.ModelViewSet):
    queryset = RSAKey.objects.all()
    serializer_class = RSAKeySerializer
    permission_classes = [permissions.IsAuthenticated]


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]


class BagViewSet(viewsets.ModelViewSet):
    queryset = Bag.objects.all()
    serializer_class = BagSerializer
    permission_classes = [permissions.IsAuthenticated]


class KeySamplesViewSet(viewsets.ModelViewSet):
    queryset = RSAKey.objects.all()
    serializer_class = KeySamplesSerializers
    permission_classes = [permissions.IsAuthenticated]
