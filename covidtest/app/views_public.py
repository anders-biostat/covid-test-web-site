import logging
import datetime

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseNotFound

from .forms_public import ResultsQueryForm
from .models import Sample, News
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
    return access_check, access_code

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

def news_archive(request):
    access_check, access_code = check_access_allowed(request)
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

result_page_dict = {
    SampleStatus.WAIT: "public/pages/test-WAIT",
    SampleStatus.PRINTED: "public/pages/test-WAIT",
    SampleStatus.UNDEF: "public/pages/test-UNDEF",
    SampleStatus.LAMPPOS: "public/pages/test-LAMPPOS",
    SampleStatus.LAMPNEG: "public/pages/test-LAMPNEG",
    SampleStatus.LAMPFAIL: "public/pages/test-LAMPFAIL",
    SampleStatus.LAMPINC: "public/pages/test-LAMPINC",
    SampleStatus.LAMPREPEAT: "public/pages/test-LAMPREPEAT",
    SampleStatus.RECEIVED: "public/pages/test-RECEIVED",
    SampleStatus.MESSAGE: "public/pages/test-MESSAGE",
}

def render_status_page(request, sample, external=True):
    last_external_status = sample.get_latest_external_status()
    if last_external_status is None:
        return render(request, "public/pages/test-WAIT.html")
    last_external_status_updated = last_external_status.updated_on
    data = {"updated_on": last_external_status_updated}
    try:
        status = SampleStatus[last_external_status.status]
    except KeyError:
        data["error"] = _("Status unbekannt")
        return render(request, "public/pages/test-ERROR.html", data)

    status_age = (datetime.datetime.now() - last_external_status_updated).days  # Last status age in days
    if (status_age > 5) and (status not in [SampleStatus.WAIT, SampleStatus.PRINTED]) and external:
        return render(request, "public/pages/test-EXPIRED.html")
    if status in [SampleStatus.MESSAGE]:
        data["msg"] = last_external_status.comment
    return render(request, result_page_dict[status], data)

def result(request):
    access_check, access_code = check_access_allowed(request)
    sample = Sample.objects.filter(access_code=access_code).first()
    return render_status_page(request, sample, external=True)

def render_status(request, event, external=True):
    sample = event.sample
    return render_status_page(request, sample, external=external)

def home(request):
    return render(request, "public/home.html")

def instructions(request):
    access_check, access_code = check_access_allowed(request)
    return render(request, "public/instructions.html")

def information(request):
    access_check, access_code = check_access_allowed(request)
    return render(request, "public/pages/information.html")

def pages(request, page):
    if page in ["contact.html", "impressum.html"]:
        return render(request, "public/pages/" + page)
    return HttpResponseNotFound("<h1>404: Page not found</h1>")