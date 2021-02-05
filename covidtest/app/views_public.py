import binascii
import hashlib

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from django.views import View

from .encryption_helper import encrypt_subject_data, rsa_instance_from_key
from .forms_public import ConsentForm, RegistrationForm, ResultsQueryForm, ResultsQueryFormLegacy, AgeGroupForm
from .models import Event, Registration, RSAKey, Sample
from .statuses import SampleStatus
from .views_consent import get_consent_md5


def index(request):
    access_code = None
    if "code" in request.GET:
        access_code = request.GET["code"]
    if access_code is not None:
        request.session["access_code"] = access_code
        return redirect("app:consent")
    return render(request, "public/index.html")


def instructions(request):
    return render(request, "public/instructions.html")


def render_status(request, event):
    if event is not None:
        try:
            status = SampleStatus[event.status]
        except KeyError:
            return render(request, "public/pages/test-ERROR.html", {"error": _("Status unbekannt")})

        if status == SampleStatus.PCRPOS:
            return render(request, "public/pages/test-PCRPOS.html")
        if status == SampleStatus.PCRNEG:
            return render(request, "public/pages/test-PCRNEG.html")
        if status == SampleStatus.LAMPPOS:
            return render(request, "public/pages/test-LAMPPOS.html")
        if status == SampleStatus.LAMPNEG:
            return render(request, "public/pages/test-LAMPNEG.html")
        if status == SampleStatus.LAMPINC:
            return render(request, "public/pages/test-LAMPINC.html")
        if status == SampleStatus.LAMPFAIL:
            return render(request, "public/pages/test-LAMPFAIL.html")
        if status == SampleStatus.UNDEF:
            return render(request, "public/pages/test-UNDEF.html")
        if status == SampleStatus.MESSAGE:
            return render(request, "public/pages/test-MESSAGE.html", {'msg': event.comment})
        if status == SampleStatus.WAIT or status == SampleStatus.PRINTED:
            return render(request, "public/pages/test-WAIT.html")
        return render(request, "public/pages/test-UNDEF.html")
    return render(
        request, "public/pages/test-ERROR.html", {"error": _("Kein Status vorhanden (bitte später erneut abrufen)")}
    )


def results_query(request):
    form = ResultsQueryForm()
    if request.method == "POST":
        form = ResultsQueryForm(request.POST)
        if form.is_valid():
            access_code = form.cleaned_data["access_code"]

            # Check if access_code exists
            sample = Sample.objects.filter(access_code=access_code).first()

            # No sample found for access_code
            if sample is None:
                messages.add_message(
                    request, messages.ERROR, _("Der Zugangscode ist unbekannt. Bitte erneut versuchen.")
                )
                return redirect("app:results_query")

            # No registration -> redirection to registration
            registration_count = sample.registrations.count()
            if registration_count < 1:
                messages.add_message(
                    request,
                    messages.WARNING,
                    _(
                        "Das Testkit mit diesem Zugangscode wurde noch nicht registriert. Bitte registrieren Sie sich vorher."
                    ),
                )
                request.session["access_code"] = access_code
                return redirect("app:register")

            # Legacy code for old samples with password registrations

            # Registered and password exists
            if sample.password_hash is not None and sample.password_hash != "":
                form = ResultsQueryFormLegacy(request.POST)

                # Check if form is legacy
                if "password" not in request.POST.keys():
                    return render(request, "public/result-query.html", {"form": form})

                if form.is_valid():
                    password = form.cleaned_data["password"]
                    sha_instance = hashlib.sha3_384()
                    sha_instance.update(password.encode("utf-8"))
                    password_hashed = binascii.b2a_base64(sha_instance.digest(), newline=False).decode("ascii")
                    if password_hashed != sample.password_hash:
                        messages.add_message(
                            request,
                            messages.ERROR,
                            _("Das eingegebene Passwort ist falsch. Bitte probieren sie es nochmal."),
                        )
                        request.session["access_code"] = access_code
                        return render(request, "public/result-query.html", {"form": form})

            # Checking the status of the sample
            event = sample.get_status()
            if event is not None:
                sample.events.create(status="INFO", comment="result queried; status: " + event.status)
            else:
                sample.events.create(status="INFO", comment="result queried; status: None")
            return render_status(request, event)

    return render(request, "public/result-query.html", {"form": form})


def information(request):
    return render(request, "public/pages/information.html")


def register(request):
    access_code = None

    if "access_code" in request.session:
        access_code = request.session.get("access_code")
    if "code" in request.GET:
        access_code = request.GET["code"]

    if not "consents_obtained" in request.session:
        raise Exception("Register page accessed without going through consent pages.")

    request.session["access_code"] = None

    form = RegistrationForm(initial={"access_code": access_code})
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            access_code = get_access_code(form)
            sample = Sample.objects.filter(access_code=access_code).first()

            if sample is None:
                messages.add_message(
                    request, messages.ERROR, _("Der Zugangscode ist unbekannt. Bitte erneut versuchen.")
                )
                return render(request, "public/register.html", {"form": form})

            request.session["access_code"] = access_code
            registration = create_registration(sample, form.cleaned_data)
            save_consents(request, registration)
            sample.events.create(status="INFO", comment="sample registered")
            clear_consent_session(request.session)
            messages.add_message(request, messages.SUCCESS, _("Erfolgreich registriert"))
            return redirect("app:instructions")
    return render(request, "public/register.html", {"form": form})


def get_access_code(form):
    return form.cleaned_data["access_code"].upper().strip()


def save_consents(request, registration):
    for consent_type in request.session["consents_obtained"]:
        md5 = get_consent_md5(consent_type)
        registration.consents.create(consent_type=consent_type, md5=md5)


def create_registration(sample, cleaned_data):
    name = cleaned_data["name"]
    address = cleaned_data["address"]
    contact = cleaned_data["contact"]
    rsa_inst = rsa_instance_from_key(sample.bag.rsa_key.public_key)
    doc = encrypt_subject_data(rsa_inst, name, address, contact)
    registration = sample.registrations.create(
        name_encrypted=doc["name_encrypted"],
        address_encrypted=doc["address_encrypted"],
        contact_encrypted=doc["contact_encrypted"],
        public_key_fingerprint=doc["public_key_fingerprint"],
        session_key_encrypted=doc["session_key_encrypted"],
        aes_instance_iv=doc["aes_instance_iv"],
    )
    return registration


def pages(request, page):
    return render(request, "public/pages/" + page)
