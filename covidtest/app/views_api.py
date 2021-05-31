from rest_framework import permissions, viewsets, views, status
from rest_framework.response import Response
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from .models import Bag, Event, Registration, RSAKey, Sample
from .serializers import (
    BagSerializer,
    EventSerializer,
    KeySamplesSerializers,
    RegistrationSerializer,
    RegistrationEncryptSerializer,
    RSAKeySerializer,
    SampleSerializer,
    VirusDetectiveSampleSerializer,
    generate_access_code,
)


def authorize_and_request_data(request):
    if request.is_ajax and request.method == "POST":
        context = {}
        email = request.POST["username"]
        password = request.POST["password"]
        barcode = request.POST["sampleCode"]

        account = authenticate(request, username=email, password=password)
        if account is None:
            context["message1"] = "Invalid Login Credentials!"
            return JsonResponse(context, status=401)

        elif account is not None and not account.is_active:
            context["message"] = "Account is in-Active"
            return JsonResponse(context, status=401)

        elif account:
            login(request, account)

            registrations = Registration.objects.filter(sample__barcode=barcode)
            if not registrations.exists():
                return JsonResponse({"message": "Invalid Barcode"}, status=400)

            sample = Sample.objects.get(barcode=barcode)
            sample.events.create(
                status="INFO", comment=f"GA queried result", updated_by=account
            )
            context = RegistrationSerializer(registrations, many=True)
            return JsonResponse(context.data, status=200, safe=False)

        else:
            context["message"] = "Invalid credentials"
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


class RegistrationEncryptViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationEncryptSerializer
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


class VirusDetectiveSampleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            try:
                bag = Bag.objects.get(name="VIRUSDETEKTIV")
            except ObjectDoesNotExist:
                return Response(
                    data={
                        "error": "Bag with name 'VIRUSDETEKTIV' does not exist. "
                        + "Please ask an admin to create the bag before continuing"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except MultipleObjectsReturned:
                return Response(
                    data={
                        "error": "More than one VIRUSDETEKTIV bag exists. "
                        + "Please ask an admin to fix this bag issue before continuing."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            sample = Sample.objects.create(
                bag=bag, access_code=generate_access_code(), barcode=""
            )

            return Response(
                data={"id": sample.pk, "access_code": sample.access_code},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                data={"error": e.__str__()}, status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request):
        try:
            try:
                sample = Sample.objects.get(access_code=request.data.get("access_code"))
            except ObjectDoesNotExist:
                return Response(
                    data={
                        "error": f"A Sample with access code - {request.data.get('access_code')} does not exist"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = VirusDetectiveSampleSerializer(
                data=request.data, instance=sample, context={"user": self.request.user}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise Exception(serializer.errors)
        except Exception as e:
            return Response(
                data={"error": e.__str__()}, status=status.HTTP_400_BAD_REQUEST
            )
