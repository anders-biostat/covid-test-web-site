from rest_framework import permissions, viewsets
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate, login

from .models import Bag, Event, Registration, RSAKey, Sample
from .serializers import (
    BagSerializer,
    EventSerializer,
    KeySamplesSerializers,
    RegistrationSerializer,
    RSAKeySerializer,
    SampleSerializer,
)


def get_csrf_token(request):
    token = get_token(request)
    resp = JsonResponse({"data": token}, status=201)
    resp['Access-Control-Allow-Origin'] = '*'
    return resp


def authorize_and_request_data(request):
    if request.is_ajax and request.method == "POST":
        context = {}
        email = request.POST['username']
        password = request.POST['password']
        barcode = request.POST['sampleCode']

        account = authenticate(request, username=email, password=password)
        if account is None:
            context['message1'] = 'Invalid Login Credentials!'
            return JsonResponse(context, status=401)

        elif account is not None and not account.is_active:
            context['message'] = 'Account is in-Active'
            return JsonResponse(context, status=401)

        elif account:
            login(request, account)

            registrations = Registration.objects.filter(sample__barcode=barcode)
            if not registrations.exists():
                return JsonResponse({"message": "Invalid Barcode"}, status=400)
            context = RegistrationSerializer(registrations, many=True)
            return JsonResponse(context.data, status=200, safe=False)

        else:
            context['message'] = 'Invalid credentials'
            return JsonResponse(context, status=401)

    return JsonResponse({"message": "invalid request"}, status=400)


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
