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
from django.http import HttpResponseNotFound
import qrcode

from .encryption_helper import encrypt_subject_data, rsa_instance_from_key
from .forms_public import (
    RegistrationForm,
    ResultsQueryForm,
    ResultsQueryFormLegacy,
)
from .models import Event, Registration, RSAKey, Sample, News
from .statuses import SampleStatus

log = logging.getLogger(__name__)


def access_check(request):
    request.session.flush()
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
                return render(request, "public/access-check.html", {"form": form}, status=404)
            # If sample found
            sample.events.create(
                status="INFO", comment="accessed page"
            )
            request.session["access_checked"] = True
            request.session["access_code"] = access_code
            return redirect("app:home")
    return render(request, "public/access-check.html", {"form": form})


def home(request):
    return render(request, "public/home.html")

def news_archive(request):
    news_query = News.objects.filter(relevant=True).order_by("-created_on")
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
    return render(request, "public/pages/test-WAIT.html")


def information(request):
    return render(request, "public/pages/information.html")


def get_access_code(form):
    return form.cleaned_data["access_code"].upper().strip()




def pages(request, page):
    if page in ["contact.html", "impressum.html"]:
        return render(request, "public/pages/" + page)
    return HttpResponseNotFound("<h1>404: Page not found</h1>")
