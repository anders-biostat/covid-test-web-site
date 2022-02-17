import logging
import datetime

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseNotFound, HttpResponseRedirect

from .forms_public import ResultsQueryForm, AbonnementForm
from .models import Sample, News, PushAbonnement
from .statuses import SampleStatus

log = logging.getLogger(__name__)

def check_access_allowed(request):
    access_check = request.session.get("access_checked")
    access_code = request.session.get("access_code")
    if access_check is not True or access_code is None:
        messages.add_message(
            request,
            messages.ERROR,
            _("Bitte einen Zugangscode / Access Code angeben"),
        )
        return redirect("app:access_check")
    return access_code

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
                return render(request, "public/pages/access-check.html", {"form": form}, status=404)
            # If sample found
            sample.events.create(
                status="INFO", comment="accessed page"
            )
            request.session["access_checked"] = True
            request.session["access_code"] = access_code
            return redirect("app:home")
    return render(request, "public/pages/access-check.html", {"form": form})

def news(request):
    check = check_access_allowed(request)
    if type(check) is HttpResponseRedirect: return check

    news_query = News.objects.filter(relevant=True).order_by("-created_on")
    page = request.GET.get("page", 1)
    paginator = Paginator(news_query, 5)
    try:
        news = paginator.page(page)
    except PageNotAnInteger:
        news = paginator.page(1)
    except EmptyPage:
        news = paginator.page(paginator.num_pages)
    return render(request, "public/pages/news.html", {"news": news})

result_page_dict = {
    SampleStatus.WAIT: "public/result_pages/test-WAIT.html",
    SampleStatus.PRINTED: "public/result_pages/test-WAIT.html",
    SampleStatus.UNDEF: "public/result_pages/test-UNDEF.html",
    SampleStatus.LAMPPOS1: "public/result_pages/test-LAMPPOS-1.html",
    SampleStatus.LAMPPOS2: "public/result_pages/test-LAMPPOS-2.html",
    SampleStatus.LAMPPOS3: "public/result_pages/test-LAMPPOS-3.html",
    SampleStatus.LAMPNEG: "public/result_pages/test-LAMPNEG.html",
    SampleStatus.LAMPFAIL: "public/result_pages/test-LAMPFAIL.html",
    SampleStatus.RECEIVED: "public/result_pages/test-RECEIVED.html",
    SampleStatus.MESSAGE: "public/result_pages/test-MESSAGE.html",
}

def render_status_page(request, sample, external=True):
    last_external_status = sample.get_latest_external_status()
    if last_external_status is None:
        return render(request, "public/result_pages/test-WAIT.html")
    last_external_status_updated = last_external_status.updated_on
    data = {"updated_on": last_external_status_updated}
    try:
        status = SampleStatus[last_external_status.status]
    except KeyError:
        data["error"] = _("Status unbekannt")
        return render(request, "public/result_pages/test-ERROR.html", data)

    status_age = (datetime.datetime.now(datetime.timezone.utc) - last_external_status_updated).days  # Last status age in days
    if (status_age > 5) and (status not in [SampleStatus.WAIT, SampleStatus.PRINTED]) and external:
        return render(request, "public/result_pages/test-EXPIRED.html")
    if status in [SampleStatus.MESSAGE]:
        data["msg"] = last_external_status.comment
    return render(request, result_page_dict[status], data)

def result(request):
    check = check_access_allowed(request)
    if type(check) is HttpResponseRedirect: return check
    access_code = check

    sample = Sample.objects.filter(access_code=access_code).first()
    try:
        sample.events.create(
            status="INFO", comment="accessed result: " + sample.get_latest_external_status().status.value
        )
    except:
        pass
    return render_status_page(request, sample, external=True)


def abonnement(request):
    if request.method == "GET":
        if request.GET.get("uuid") is not None:
            uuid = request.GET.get("uuid")
            abonnement = PushAbonnement.objects.filter(id=uuid).first()
            if abonnement is not None:
                form = AbonnementForm(initial={"key": abonnement.key, "action": "2"})
                return render(request, "public/pages/abonnement.html", {"form": form, "selected": "Deabonnieren"})
    if request.method == "POST":
        form = AbonnementForm(request.POST)
        if form.is_valid():
            # Action: "1" for subscription, "2" for unsubscribing
            action = form.cleaned_data["action"]
            key = form.cleaned_data["key"]

            # Check if abonnement exists
            abonnement = PushAbonnement.objects.filter(key=key).first()

            # Case subscription:
            if action == "1":
                if abonnement is None:
                    PushAbonnement.objects.create(key=key)
                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        _("Mitteilungen erfolgreich abonniert")
                    )
                    return redirect("app:home")
                else:
                    messages.add_message(
                        request,
                        messages.WARNING,
                        _("Mitteilungen bereits abonniert")
                    )
                    return redirect("app:home")
            if action == "2":
                if abonnement is None:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        _("Key nicht gefunden")
                    )
                else:
                    PushAbonnement.objects.filter(key=key).delete()
                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        _("Mitteilungen erfolgreich deabonniert")
                    )
                    return redirect("app:home")
    form = AbonnementForm()
    return render(request, "public/pages/abonnement.html", {"form": form, "selected": "Abonnieren"})

def render_status(request, event, external=True):
    if event is not None:
        sample = event.sample
        return render_status_page(request, sample, external=external)
    return render(request, "public/result_pages/test-WAIT.html")

def home(request):
    check = check_access_allowed(request)
    if type(check) is HttpResponseRedirect: return check
    return render(request, "public/pages/home.html")

def instructions(request):
    check = check_access_allowed(request)
    if type(check) is HttpResponseRedirect: return check
    return render(request, "public/pages/instructions.html")

def information(request):
    check = check_access_allowed(request)
    if type(check) is HttpResponseRedirect: return check
    return render(request, "public/pages/information.html")

def pages(request, page):
    if page in ["contact.html", "impressum.html", "data-protection.html"]:
        return render(request, "public/pages/" + page)
    return HttpResponseNotFound("<h1>404: Page not found</h1>")