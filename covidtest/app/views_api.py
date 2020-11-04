from rest_framework import viewsets
from rest_framework import permissions

from .serializers import SampleSerializer, RSAKeySerializer, RegistrationSerializer, EventSerializer, BagSerializer, KeySamplesSerializers
from .models import Sample, RSAKey, Registration, Event, Bag


class SampleViewSet(viewsets.ModelViewSet):
    serializer_class = SampleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  # with filter for barcode
        queryset = Sample.objects.all()
        barcode = self.request.query_params.get('barcode', None)
        if barcode is not None:
            print("Filtering to barcode:", barcode)
            queryset = queryset.filter(barcode=barcode)
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