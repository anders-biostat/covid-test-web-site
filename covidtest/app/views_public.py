import binascii
import hashlib
import logging
from io import BytesIO
import base64
import datetime

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.template.loader import get_template
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
import qrcode

from .encryption_helper import encrypt_subject_data, rsa_instance_from_key
from .forms_public import (
    ConsentForm,
    RegistrationForm,
    ResultsQueryForm,
    ResultsQueryFormLegacy,
    AgeGroupForm,
)
from .models import Event, Registration, RSAKey, Sample, News
from .statuses import SampleStatus

log = logging.getLogger(__name__)


def index(request):
    request.session.flush()
    access_code = None
    if "code" in request.GET:
        access_code = request.GET["code"]
    if access_code is not None:
        request.session["access_code"] = access_code
        return redirect("app:consent_age")
    news = News.objects.filter(relevant=True).order_by("-created_on")
    return render(request, "public/index.html", {"news": news, "without_registration": settings.WITHOUT_REGISTRATION})

def news_archive(request):
    news_query = News.objects.filter(relevant=False).order_by("-created_on")
    page = request.GET.get("page", 1)
    paginator = Paginator(news_query, 5)
    try:
        news = paginator.page(page)
    except PageNotAnInteger:
        news = paginator.page(1)
    except EmptyPage:
        news = paginator.page(paginator.num_pages)

    return render(request, "public/news-archive.html", {"news": news})


def instructions(request):
    return render(request, "public/instructions.html")


def render_status(request, event):
    if event is not None:
        event_updated_on = event.updated_on
        try:
            status = SampleStatus[event.status]
        except KeyError:
            return render(
                request,
                "public/pages/test-ERROR.html",
                {"error": _("Status unbekannt"), "updated_on": event_updated_on},
            )

        status_age = (datetime.datetime.now() - event_updated_on).days # Last status age in days
        if (status_age > 5) and (status not in [SampleStatus.WAIT, SampleStatus.PRINTED]):
            status = "expired"

        if status == SampleStatus.PCRPOS:
            return render(
                request,
                "public/pages/test-PCRPOS.html",
                {"updated_on": event_updated_on},
            )
        if status == SampleStatus.PCRNEG:
            return render(
                request,
                "public/pages/test-PCRNEG.html",
                {"updated_on": event_updated_on},
            )
        if status == SampleStatus.PCRWEAKPOS:
            return render(
                request,
                "public/pages/test-PCRWEAKPOS.html",
                {"updated_on": event_updated_on},
            )
        if status == SampleStatus.LAMPPOS:
            return render(
                request,
                "public/pages/test-LAMPPOS.html",
                {"updated_on": event_updated_on},
            )
        if status == SampleStatus.LAMPNEG:
            return render(
                request,
                "public/pages/test-LAMPNEG.html",
                {"updated_on": event_updated_on},
            )
        if status == SampleStatus.LAMPINC:
            return render(
                request,
                "public/pages/test-LAMPINC.html",
                {"updated_on": event_updated_on},
            )
        if status == SampleStatus.LAMPFAIL:
            return render(
                request,
                "public/pages/test-LAMPFAIL.html",
                {"updated_on": event_updated_on},
            )
        if status == SampleStatus.RECEIVED:
            return render(
                request,
                "public/pages/test-RECEIVED.html",
                {"updated_on": event_updated_on},
            )
        if status == SampleStatus.LAMPREPEAT:
            return render(
                request,
                "public/pages/test-LAMPREPEAT.html",
                {"updated_on": event_updated_on},
            )
        if status == SampleStatus.UNDEF:
            return render(
                request,
                "public/pages/test-UNDEF.html",
                {"updated_on": event_updated_on},
            )
        if status == SampleStatus.MESSAGE:
            return render(
                request,
                "public/pages/test-MESSAGE.html",
                {"msg": event.comment, "updated_on": event_updated_on},
            )
        if status == SampleStatus.WAIT or status == SampleStatus.PRINTED:
            return render(
                request, "public/pages/test-WAIT.html", {"updated_on": event_updated_on}
            )
        if status == "expired":
            return render(
                request, "public/pages/access-expired.html"
            )
        return render(
            request, "public/pages/test-UNDEF.html", {"updated_on": event_updated_on}
        )
    # return render(
    #     request, "public/pages/test-ERROR.html", {"error": _("Kein Status vorhanden (bitte später erneut abrufen)")}
    # )
    return render(request, "public/pages/test-WAIT.html")

def results_query(request, slim_version=False):
    result_query_template = "public/result-query.html"
    if slim_version:
        result_query_template = "public/result-query-slim.html"

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
                    request,
                    messages.ERROR,
                    _("Der Zugangscode ist unbekannt. Bitte erneut versuchen."),
                )
                form = ResultsQueryForm()
                return render(request, result_query_template, {"form": form}, status=404)

            # No registration -> redirection to registration
            registration_count = sample.registrations.count()

            registration_warning = _(
                        "Das Testkit mit diesem Zugangscode wurde noch nicht registriert. Bitte registrieren Sie sich vorher."
            )

            if settings.WITHOUT_REGISTRATION:
                registration_warning = _(
                    "Zum Abrufen des Testergebnisses benötigen wir Ihr Einvertändnis."
                )

            if registration_count < 1 and settings.DISPLAY_CONSENT_PAGES:
                messages.add_message(
                    request,
                    messages.WARNING,
                    registration_warning,
                )
                request.session["access_code"] = access_code
                return redirect("app:register")

            # Legacy code for old samples with password registrations

            # Registered and password exists
            if sample.password_hash is not None and sample.password_hash != "":
                form = ResultsQueryFormLegacy(request.POST)

                # Check if form is legacy
                if "password" not in request.POST.keys():
                    return render(request, result_query_template, {"form": form})

                if form.is_valid():
                    password = form.cleaned_data["password"]
                    sha_instance = hashlib.sha3_384()
                    sha_instance.update(password.encode("utf-8"))
                    password_hashed = binascii.b2a_base64(
                        sha_instance.digest(), newline=False
                    ).decode("ascii")
                    if password_hashed != sample.password_hash:
                        messages.add_message(
                            request,
                            messages.ERROR,
                            _(
                                "Das eingegebene Passwort ist falsch. Bitte probieren sie es nochmal."
                            ),
                        )
                        request.session["access_code"] = access_code
                        return render(request, result_query_template, {"form": form})

            # Checking the status of the sample
            event = sample.get_latest_external_status()
            if event is not None and not settings.PRIVACY_MODE:
                sample.events.create(
                    status="INFO", comment="result queried; status: " + event.status
                )
            elif not settings.PRIVACY_MODE:
                sample.events.create(
                    status="INFO", comment="result queried; status: None"
                )
            return render_status(request, event)

    if settings.WITHOUT_REGISTRATION and "access_code" in request.session:
        access_code = request.session["access_code"]
        sample = Sample.objects.filter(access_code=access_code).first()
        if sample.registrations.count() < 1 and settings.DISPLAY_CONSENT_PAGES:
            messages.add_message(
                request,
                messages.WARNING,
                _(
                    "Zum Abrufen des Testergebnisses benötigen wir Ihr Einvertändnis."
                ),
            )
            return redirect("app:register")
        event = sample.get_latest_external_status()
        return render_status(request, event)

    return render(request, result_query_template, {"form": form, "without_registration": settings.WITHOUT_REGISTRATION})

results_query_slim = lambda request: results_query(request, slim_version=True)

def information(request):
    return render(request, "public/pages/information.html")


def register(request):
    access_code = None

    if "access_code" in request.session:
        access_code = request.session.get("access_code")
    if "code" in request.GET:
        access_code = request.GET["code"]

    if (len(request.session.get("consents_obtained", list())) == 0 and settings.REQUIRE_CONSENT) or ("passed_consent_pages" not in request.session):
        log.warning("Register page accessed without going through consent pages.")
        return redirect("app:consent_age")

    request.session["access_code"] = None

    form = RegistrationForm(initial={"access_code": access_code})
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            access_code = get_access_code(form)
            sample = Sample.objects.filter(access_code=access_code).first()

            if sample is None:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("Der Zugangscode ist unbekannt. Bitte erneut versuchen."),
                )
                return render(request, "public/register.html", {"form": form})

            name = form.cleaned_data["name"]
            address = form.cleaned_data["address"]
            contact = form.cleaned_data["contact"]

            request.session["access_code"] = access_code
            # ! A registration can be created without ensuring a corresponding consent is created with it
            registration = create_registration(sample, form.cleaned_data)
            save_consents(request, registration)
            if not settings.PRIVACY_MODE:
                sample.events.create(status="INFO", comment="sample registered")
            request.session.flush()
            messages.add_message(
                request, messages.SUCCESS, _("Erfolgreich registriert")
            )

            return render(
                request,
                "public/instructions.html",
                {
                    "name": name,
                    "address": address,
                    "contact": contact,
                    "access_code": access_code,
                },
            )
    return render(request, "public/register.html", {"form": form})


def get_access_code(form):
    return form.cleaned_data["access_code"].upper().strip()


def save_consents(request, registration):
    # TODO if len of consents is 0, no consent will be created
    for consent_type in request.session["consents_obtained"]:
        # TODO if an invalid consent type is submitted somehow, create better
        #  solution than throwing a TemplateDoesNotExistError
        md5 = get_consent_md5(consent_type)
        registration.consents.create(consent_type=consent_type, md5=md5)


def create_registration(sample, cleaned_data, clear_fields=False):
    if not clear_fields:
        name = cleaned_data["name"]
        address = cleaned_data["address"]
        contact = cleaned_data["contact"]
        rsa_inst = rsa_instance_from_key(sample.bag.rsa_key.public_key)
        doc = encrypt_subject_data(rsa_inst, name, address, contact)

    registration = sample.registrations.create(
        name_encrypted=doc["name_encrypted"] if not clear_fields else "",
        address_encrypted=doc["address_encrypted"] if not clear_fields else "",
        contact_encrypted=doc["contact_encrypted"] if not clear_fields else "",
        public_key_fingerprint=doc["public_key_fingerprint"] if not clear_fields else "",
        session_key_encrypted=doc["session_key_encrypted"] if not clear_fields else "",
        aes_instance_iv=doc["aes_instance_iv"] if not clear_fields else "",
    )
    return registration


def pages(request, page):
    return render(request, "public/pages/" + page)


def get_certificate(request):

    if request.method == "POST":
        access_code = request.POST.get("access_code")
        try:
            sample = Sample.objects.get(access_code=access_code)
            registration = sample.registrations.last()

            qr = qrcode.QRCode(version=4, box_size=10, border=4)
            qr.add_data(f"https://covidtest-hd.de/test-results?ac={access_code}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="#C81528", back_color="white")

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

            return render(
                request,
                "public/test_certificate.html",
                {
                    "qr_img": img_str,
                    "barcode": sample.barcode,
                    "registered_on": registration.time,
                    "name": request.POST.get("name"),
                    "address": request.POST.get("address"),
                    "contact": request.POST.get("contact"),
                },
            )
        except ObjectDoesNotExist:
            pass
    result_query_template = "public/result-query.html"
    form = ResultsQueryForm()
    return render(request, result_query_template, {"form": form})

def get_template_file_for_consent_type(consent_type):
    return "public/info_and_consent/" + consent_type + ".html"

def get_consent_md5(consent_type):
    # get full path of HTML file with info and consent text
    filepath = get_template(get_template_file_for_consent_type(consent_type)).origin.name
    # calculate its MD5 hash
    with open(filepath, 'rb' ) as f:
        hashsum = hashlib.md5(f.read())
    return hashsum.hexdigest()


def get_result_from_certificate(request):
    access_code = request.GET.get("ac")
    if access_code:
        try:
            sample = Sample.objects.get(access_code=access_code)
            event = sample.get_latest_external_status()
            if event is not None and not settings.PRIVACY_MODE:
                sample.events.create(
                    status="INFO", comment="result queried; status: " + event.status
                )
            elif not settings.PRIVACY_MODE:
                sample.events.create(
                    status="INFO", comment="result queried; status: None"
                )
            return render_status(request, event)
        except ObjectDoesNotExist:
            pass

    result_query_template = "public/result-query.html"
    form = ResultsQueryForm()
    return render(request, result_query_template, {"form": form})
