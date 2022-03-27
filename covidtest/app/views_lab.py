import json
import csv
import os
import ast
from datetime import date, datetime, time

import pytz
import django_filters
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from simplepush import send, send_encrypted

from djangoql.exceptions import DjangoQLError
from djangoql.queryset import apply_search
from djangoql.schema import DjangoQLSchema
from djangoql.serializers import DjangoQLSchemaSerializer

from .forms_lab import (
    LabCheckInForm,
    LabProbeEditForm,
    LabQueryForm,
    LabQueryFormQL,
    BagManagementQueryForm,
    BagHandoutForm,
    BagHandoutModelFormSet,
    SendNotificationForm
)
from .models import Event, Sample, Bag, BagRecipient, PushAbonnement
from .statuses import SampleStatus
from .tables import SampleTable
from .utils import find_samples, find_samples_ql, Search, is_in_group
from .views_public import render_status


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
    return HttpResponse(
        version_str
        % (branch_name, branch_name, commit_hash, commit_hash, commit_hash[:7])
    )


@login_required
@is_in_group("lab_user")
def sample_check_in(request):
    if request.method == "POST":
        form = LabCheckInForm(request.POST)
        if form.is_valid():
            barcodes = [str(x).strip().upper() for x in form.data["barcodes"].split()]
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
                    set_status = sample.set_status(
                        status, comment=comment, author=request.user
                    )
                    if not set_status:
                        status_not_set.append(barcode)
                    else:
                        successful_barcodes.append(barcode)

            if len(barcodes_not_in_db) > 0:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "Einige Barcodes waren nicht in der Datenbank",
                )
            if len(status_not_set) > 0:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "Einige Status konnten nicht gesetzt werden",
                )
            if len(rack_not_set) > 0:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "Einige Racks konnten nicht gesetzt werden",
                )
            no_success = True
            if (
                len(rack_not_set) == 0
                and len(status_not_set) == 0
                and len(barcodes_not_in_db) == 0
            ):
                no_success = False
                messages.add_message(
                    request, messages.SUCCESS, "Proben erfolgreich eingetragen"
                )

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
                    "successful_barcodes": successful_barcodes,
                },
            )
    else:
        form = LabCheckInForm()
    return render(
        request, "lab/sample_check_in.html", {"form": form, "display_sample": False}
    )

@login_required
@is_in_group("lab_user")
def sample_detail(request, ql=False):
    sample_detail_template = "lab/sample_query.html"
    form = LabQueryForm()

    if ql:
        sample_detail_template = "lab/sample_query_ql.html"
        form = LabQueryFormQL()

    edit_form = LabProbeEditForm()
    if request.method == "POST":
        if "searchql" in request.POST.keys():
            form = LabQueryFormQL(request.POST)
            if form.is_valid():
                search = form.cleaned_data["searchql"].strip()

                template_obj = {"form": form, "edit_form": edit_form, "search": search}
                query_results, query_error = find_samples_ql(query_string=search)
                if query_error != "":
                    messages.add_message(
                        request, messages.ERROR, query_error
                    )
                template_obj.update(
                    query_results
                )
                return render(request, sample_detail_template, template_obj)
        if "search" in request.POST.keys():
            form = LabQueryForm(request.POST)
            if form.is_valid():
                search = form.cleaned_data["search"].upper().strip()

                template_obj = {"form": form, "edit_form": edit_form, "search": search}
                template_obj.update(
                    find_samples(
                        search=search,
                        search_category=request.POST.get("search_category"),
                    )
                )

                return render(request, sample_detail_template, template_obj)
        if "edit" in request.POST.keys():
            edit_form = LabProbeEditForm(request.POST)
            if edit_form.is_valid():
                barcode = edit_form.cleaned_data["barcode"].upper().strip()
                status = edit_form.cleaned_data["status"].upper().strip()
                rack = edit_form.cleaned_data["rack"].upper().strip()
                comment = edit_form.cleaned_data["comment"].strip()
                sample = Sample.objects.filter(barcode=barcode).first()
                if sample is None:
                    messages.add_message(
                        request, messages.ERROR, "Sample nicht gefunden"
                    )
                else:
                    rack_changed = sample.rack != rack
                    if rack_changed:
                        event = Event(
                            sample=sample,
                            status=SampleStatus.INFO.value,
                            comment="Rack changed in lab interface from "
                            + str(sample.rack)
                            + " to "
                            + str(rack)
                            + ".",
                            updated_by=request.user,
                        )
                        sample.rack = rack
                        sample.save()
                        event.save()
                        messages.add_message(
                            request, messages.SUCCESS, "Sample rack geupdated"
                        )
                    if status != "-":
                        status = SampleStatus[status]
                        event = Event(
                            sample=sample,
                            status=status.value,
                            comment=comment,
                            updated_by=request.user,
                        )
                        event.save()
                        messages.add_message(
                            request, messages.SUCCESS, "Status geupdated"
                        )
                    else:
                        messages.add_message(
                            request,
                            messages.ERROR,
                            "Der Probe bitte einen Status geben",
                        )
                return render(
                    request,
                    sample_detail_template,
                    {"form": form, "edit_form": edit_form, "sample": sample},
                )
            else:
                sample = Sample.objects.filter(
                    barcode=request.POST.get("barcode")
                ).first()
                messages.add_message(request, messages.ERROR, edit_form.errors)
                return render(
                    request,
                    sample_detail_template,
                    {"form": form, "edit_form": edit_form, "sample": sample},
                )

    return render(
        request, sample_detail_template, {"form": form, "edit_form": edit_form}
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_status(request):
    if request.method == "POST":
        body = json.loads(request.body)

        bc = str(body["barcode"]).strip().upper()
        bc_ok = []
        bc_missing = []
        bc_duplicated = []
        qset = Sample.objects.filter(barcode=bc)

        if len(qset) == 0:
            bc_missing.append(bc)
            return HttpResponseBadRequest("Barcode %s not found on the server." % bc)
        if len(qset) > 1:
            bc_duplicated.append(bc)
            return HttpResponseBadRequest(
                "Multiple samples with barcode %s found." % bc
            )
        if "status" not in body:
            return HttpResponseBadRequest("No sample status provided")
        if "comment" not in body:
            comment = ""
        else:
            comment = body["comment"]

        sample = qset.first()
        if "rack" in body:
            sample.rack = body["rack"]
            sample.save()
            comment += ". Rack: " + str(body["rack"])
        sample.events.create(status=body["status"], comment=comment)
        bc_ok.append(bc)
        return HttpResponse("Event created successfully", status=201)


@login_required
@is_in_group("lab_user")
def bag_search_statistics(request):
    event_keys = []
    for stat in SampleStatus:
        event_keys.append(stat.name)
    event_keys.insert(0, "Gesamt")
    event_keys.insert(1, "Ohne")
    event_keys.remove("INFO")

    if request.method == "POST":
        if "search" in request.POST.keys():
            form = BagManagementQueryForm(request.POST)
            if form.is_valid():
                search_keys = form.cleaned_data["search"]
                stats_array = []
                total_samples = 0

                find = Search(search_keys)
                bags = find.bags()

                if not bags:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        f"Beutel mit ID oder Abnehmer {search_keys} existieren nicht",
                    )
                    return render(request, "lab/bag_search_statistics.html")

                for bag in bags:
                    stats_obj = dict(status=dict.fromkeys(event_keys, 0))
                    total_samples += bag.samples.count()

                    if bag.recipient:
                        stats_obj["recipient"] = bag.recipient.recipient_name
                        stats_obj["contactPerson"] = bag.recipient.name_contact_person
                        stats_obj["email"] = bag.recipient.email
                        stats_obj["telephone"] = bag.recipient.telephone
                    else:
                        stats_obj["recipient"] = "--"
                        stats_obj["contactPerson"] = "--"
                        stats_obj["email"] = "--"
                        stats_obj["telephone"] = "--"

                    stats_obj["bagId"] = bag.pk
                    stats_obj["createdAt"] = bag.created_on
                    if bag.handed_out_on is not None:
                        stats_obj["handedOutOn"] = bag.handed_out_on
                    else:
                        stats_obj["handedOutOn"] = datetime(
                            1, 1, 1, 0, 0, 0, 0, pytz.UTC
                        )
                    if bag.handed_out_by is not None:
                        stats_obj["handedOutBy"] = bag.handed_out_by
                    else:
                        stats_obj["handedOutBy"] = "--"
                    stats_obj["status"]["Gesamt"] = len(bag.samples.all())
                    for sample in bag.samples.all():
                        event = sample.get_latest_internal_status()
                        try:
                            stats_obj["status"][event.status] += 1
                        except KeyError:
                            stats_obj["status"][event.status] = 1
                        except AttributeError:
                            stats_obj["status"]["Ohne"] += 1
                    stats_array.append(stats_obj)

                # Sort results by handed out time and refactor placeholder datetime to string
                sorted_stats_array = sorted(stats_array, key=lambda k: k["handedOutOn"])
                cleaned_sorted_stats_array = []
                for obj in sorted_stats_array:
                    handed_out_time = obj["handedOutOn"]
                    if handed_out_time.year == 1:
                        obj["handedOutOn"] = "0"
                    cleaned_sorted_stats_array.append(obj)

                return render(
                    request,
                    "lab/bag_search_statistics.html",
                    {
                        "statusEnum": event_keys,
                        "statsArray": cleaned_sorted_stats_array,
                        "search_keys": search_keys,
                        "footerStats": {"total_samples": total_samples},
                    },
                )
            else:
                messages.add_message(request, messages.ERROR, form.errors)

        elif "export" in request.POST.keys():
            response = HttpResponse(content_type="text/csv")
            response[
                "Content-Disposition"
            ] = f'attachment; filename={date.today().strftime("%Y-%m-%d")}_bagStatsExport.csv'
            search_keys = ast.literal_eval(request.POST.get("export"))

            find = Search(search_keys)
            bags = find.bags()

            if not bags:
                messages.add_message(
                    request,
                    messages.ERROR,
                    f"Beutel mit ID oder Abnehmer {search_keys} existieren nicht",
                )
                return render(request, "lab/bag_search_statistics.html")

            columns = [
                "recipient",
                "contactPerson",
                "email",
                "telephone",
                "bagId",
                "createdAt",
                "handedOutOn",
                "handedOutBy",
            ]
            columns.extend(event_keys)

            writer = csv.DictWriter(response, fieldnames=columns)
            writer.writeheader()

            for bag in bags:
                stats_obj = dict.fromkeys(event_keys, 0)

                if bag.recipient:
                    stats_obj["recipient"] = bag.recipient.recipient_name
                    stats_obj["contactPerson"] = bag.recipient.name_contact_person
                    stats_obj["email"] = bag.recipient.email
                    stats_obj["telephone"] = bag.recipient.telephone
                else:
                    stats_obj["recipient"] = "--"
                    stats_obj["contactPerson"] = "--"
                    stats_obj["email"] = "--"
                    stats_obj["telephone"] = "--"

                stats_obj["bagId"] = bag.pk
                stats_obj["createdAt"] = bag.created_on
                if bag.handed_out_on is not None:
                    stats_obj["handedOutOn"] = bag.handed_out_on
                else:
                    stats_obj["handedOutOn"] = "0"
                if bag.handed_out_by is not None:
                    stats_obj["handedOutBy"] = bag.handed_out_by
                else:
                    stats_obj["handedOutBy"] = "--"
                stats_obj["Gesamt"] = len(bag.samples.all())
                for sample in bag.samples.all():
                    event = sample.get_latest_internal_status()
                    try:
                        stats_obj[event.status] += 1
                    except AttributeError:
                        stats_obj["Ohne"] += 1
                writer.writerow(stats_obj)

            return response
    return render(request, "lab/bag_search_statistics.html")


@login_required
@is_in_group("lab_user", "bag_handler")
def bag_handout(request):
    if request.method == "POST":
        if "search" in request.POST.keys():
            form = BagManagementQueryForm(request.POST)
            if form.is_valid():
                search_keys = form.cleaned_data["search"]

                bags = Bag.objects.filter(pk__in=search_keys)
                if bags.exists():
                    formset = BagHandoutModelFormSet(queryset=bags)

                    return render(
                        request,
                        "lab/bag_handout.html",
                        {"formset": formset, "searchKeys": search_keys},
                    )
                else:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        f"Keinen Beutel mit ID(s) {search_keys} gefunden",
                    )
            else:
                messages.add_message(request, messages.ERROR, form.errors)
        else:
            formset = BagHandoutModelFormSet(request.POST)
            if formset.is_valid():
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.handed_out_by = request.user
                    instance.save()
                messages.add_message(
                    request, messages.SUCCESS, "Beutel erfolgreich ausgegeben"
                )
            else:
                messages.add_message(
                    request, messages.ERROR, f"Fehlgeschlagen: {formset.errors}"
                )

    return render(request, "lab/bag_handout.html")


@login_required
@is_in_group("lab_user")
def status_preview(request):
    try:
        sample = Sample.objects.get(barcode=request.GET.get("id"))
    except ObjectDoesNotExist:
        return HttpResponseBadRequest("Something went wrong")
    event = sample.get_latest_external_status()
    return render_status(request, event)


def send_message_to_all(title, message):
    users = PushAbonnement.objects.all()
    for user in users:
        message_end = f"\n\nZum Deabonnieren öffnen Sie bitte:\nhttps://covidtest-hd.de/abonnement/?key={user.key}"
        send(user.key, title, message + message_end)

@login_required
@is_in_group("notification")
def notify(request):
    if request.method == "POST":
        form = SendNotificationForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            message = form.cleaned_data["message"]
            if time(7,0,0) <= datetime.utcnow().time() <= time(19,0,0):
                print("Sending message to all:", repr(message))
                send_message_to_all(title, message)
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    "Successfully send message",
                )
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "Notifications are deactivated between 20:00 and 07:00",
                )
    form = SendNotificationForm()
    return render(request, "lab/notify.html", {"form": form})