import os

import django_filters
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, SingleTableView
from django.db.models import Q, Max

from .forms_lab import LabCheckInForm, LabGenerateBarcodeForm, LabProbeEditForm, LabQueryForm, LabRackResultsForm
from .models import Event, Registration, RSAKey, Sample
from .serializers import SampleSerializer
from .statuses import SampleStatus
from .tables import SampleTable
from django.views.decorators.csrf import csrf_exempt
import json

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated


@login_required
def index(request):
    return render(request, "lab/index.html")


@login_required
def version(request):
    # Checking where the .git directory is
    if os.path.isdir("../.git"):
        git_dir = "../.git"
    elif os.path.isdir(".git"):
        git_dir = ".git"
    else:
        return HttpResponse("No .git directory found")

    with open(git_dir + "/HEAD", "r") as head:
        ref = head.readline().split(" ")[-1].strip()
        branch_name = ref.split("/")[-1]
    if "/" in ref:
        with open(git_dir + "/" + ref, "r") as git_hash:
            commit_hash = git_hash.readline().strip()
    else:
        commit_hash = ref

    version_str = """
    <code>
    Branch: <a href='https://github.com/anders-biostat/covid-test-web-site/tree/%s'>%s</a><br>
    Commit: <a href='https://github.com/anders-biostat/covid-test-web-site/commit/%s'>%s</a><br>
    Short: %s <br>
    </code>
    """
    return HttpResponse(version_str % (branch_name, branch_name, commit_hash, commit_hash, commit_hash[:7]))


@login_required
#@permission_required("sample.can_add_sample", login_url='/lab')
def sample_check_in(request):
    if request.method == "POST":
        form = LabCheckInForm(request.POST)
        if form.is_valid():
            barcodes = [x.strip().upper() for x in form.data["barcodes"].split()]
            rack = form.cleaned_data["rack"].strip().upper()
            status = form.data["status"]
            comment = form.data["comment"]

            barcodes_not_in_db = []
            status_not_set = []
            rack_not_set = []
            successful_barcodes = []

            for barcode in barcodes:
                sample = Sample.objects.filter(barcode=barcode).first()
                if not sample:
                    barcodes_not_in_db.append(barcode)
                else:
                    sample.rack = rack
                    sample.save()
                    set_status = sample.set_status(status, comment=comment, author=request.user)
                    if not set_status:
                        status_not_set.append(barcode)
                    else:
                        successful_barcodes.append(barcode)

            if len(barcodes_not_in_db) > 0:
                messages.add_message(request, messages.ERROR, _("Einige Barcodes waren nicht in der Datenbank"))
            if len(status_not_set) > 0:
                messages.add_message(request, messages.ERROR, _("Einige Status konnten nicht gesetzt werden"))
            if len(rack_not_set) > 0:
                messages.add_message(request, messages.ERROR, _("Einige Racks konnten nicht gesetzt werden"))
            no_success = True
            if len(rack_not_set) == 0 and len(status_not_set) == 0 and len(barcodes_not_in_db) == 0:
                no_success = False
                messages.add_message(request, messages.SUCCESS, _("Proben erfolgreich eingetragen"))

            return render(
                request,
                "lab/sample_check_in.html",
                {
                    "form": form,
                    "sample": sample,
                    "barcodes_not_in_db": barcodes_not_in_db,
                    "rack_not_set": rack_not_set,
                    "status_not_set": status_not_set,
                    "no_success": no_success,
                    "successful_barcodes": successful_barcodes
                },
            )
    else:
        form = LabCheckInForm()
    return render(request, "lab/sample_check_in.html", {"form": form, "display_sample": False})


@login_required
def sample_detail(request):
    sample_detail_template = "lab/sample_query.html"

    form = LabQueryForm()
    edit_form = LabProbeEditForm()
    if request.method == "POST":
        if "search" in request.POST.keys():
            form = LabQueryForm(request.POST)
            if form.is_valid():
                search = form.cleaned_data["search"].upper().strip()
                single_sample = Sample.objects.filter(Q(barcode=search) | Q(access_code=search)).first()

                if single_sample:
                    edit_form = LabProbeEditForm(initial={"rack": single_sample.rack, "comment": "Status changed in lab interface"})
                    return render(
                        request,
                        sample_detail_template,
                        {"form": form, "edit_form": edit_form, "sample": single_sample, "search": search},
                    )
                else:
                    # TODO this probably needs some sort of pagination in the future
                    #  to prevent sending too many samples in response
                    sample_pks = []
                    events = Event.objects.filter(status__icontains=search)
                    if events:
                        event_list = events.values("sample").annotate(updated_on=Max("updated_on"))
                        sample_pks = [event["sample"] for event in event_list]
                    multi_sample = Sample.objects.filter(
                        Q(rack__icontains=search) |
                        Q(bag__name__icontains=search) |
                        Q(pk__in=sample_pks)
                    )
                    if multi_sample:
                        return render(
                            request,
                            sample_detail_template,
                            {"form": form, "multi_sample": multi_sample, "search": search},
                        )
                    else:
                        return render(
                            request,
                            sample_detail_template,
                            {"form": form, "edit_form": edit_form, "search": search},
                        )
        if "edit" in request.POST.keys():
            edit_form = LabProbeEditForm(request.POST)
            if edit_form.is_valid():
                barcode = edit_form.cleaned_data["barcode"].upper().strip()
                status = edit_form.cleaned_data["status"].upper().strip()
                rack = edit_form.cleaned_data["rack"].upper().strip()
                comment = edit_form.cleaned_data["comment"].strip()
                sample = Sample.objects.filter(barcode=barcode).first()
                if sample is None:
                    messages.add_message(request, messages.ERROR, _("Sample nicht gefunde"))
                else:
                    rack_changed = sample.rack != rack
                    if rack_changed:
                        event = Event(
                            sample=sample,
                            status=SampleStatus.INFO,
                            comment="Rack changed in lab interface from "+str(sample.rack)+" to "+str(rack)+".",
                            updated_by=request.user
                        )
                        sample.rack = rack
                        sample.save()
                        event.save()
                        messages.add_message(request, messages.SUCCESS, _("Sample rack geupdated"))
                    if status != "-":
                        status = SampleStatus[status]
                        event = Event(
                            sample=sample,
                            status=status.value,
                            comment=comment,
                            updated_by=request.user
                        )
                        event.save()
                        messages.add_message(request, messages.SUCCESS, _("Status geupdated"))
                return render(
                    request, sample_detail_template, {"form": form, "edit_form": edit_form, "sample": sample}
                )

    return render(request, sample_detail_template, {"form": form, "edit_form": edit_form})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_status(request):
    if request.method == "POST":
        body = json.loads(request.body)

        bc = body['barcode'].strip().upper()
        bc_ok = []
        bc_missing = []
        bc_duplicated = []
        qset = Sample.objects.filter(barcode=bc)

        if len(qset) == 0:
            bc_missing.append(bc)
            return HttpResponseBadRequest("Barcode %s not found on the server." % bc)
        if len(qset) > 1:
            bc_duplicated.append(bc)
            return HttpResponseBadRequest("Multiple samples with barcode %s found." % bc)
        if 'status' not in body:
            return HttpResponseBadRequest("No sample status provided")
        if 'comment' not in body:
            comment = ""
        else:
            comment = body['comment']

        sample = qset.first()
        if 'rack' in body:
            sample.rack = body['rack']
            sample.save()
            comment += ". Rack: " + str(body['rack'])
        sample.events.create(status=body['status'], comment=comment)
        bc_ok.append(bc)
        return HttpResponse("Event created successfully", status=201)


class SampleFilter(django_filters.FilterSet):
    class Meta:
        model = Sample
        fields = ["barcode", "access_code"]


class SampleListView(SingleTableMixin, FilterView):
    model = Sample
    table_class = SampleTable
    template_name = "lab/sample_list.html"
    filterset_class = SampleFilter


@login_required
def dashboard(request):

    count_wait = Event.objects.filter(status="PRINTED").count()

    dashboard_values = {"count_Samples": Sample.objects.filter().count(), "count_wait": count_wait}

    return render(request, "lab/dashboard.html", {"dashboard_values": dashboard_values})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sample_details_snippet(request):
    sample = Sample.objects.filter(access_code = request.POST.get("access_code")).first()
    if sample is not None:
       return render(request, "lab/sample_snippet_for_virusfinder.html", {"sample": sample})
    else:
       return HttpResponse("<i>Access code %s not found</i>" % request.POST.get("access_code"))