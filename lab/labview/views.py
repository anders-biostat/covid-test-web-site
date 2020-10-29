import sys
from django.shortcuts import render
from django.contrib import messages
from django.utils.translation import gettext as _

from common.models import Sample, Event, Registration
from common.statuses import SampleStatus

from .forms import LabCheckInForm, LabQueryForm, LabRackResultsForm, LabProbeEditForm

def index(request):
    return render(request, "index.html")


def probe_check_in(request):
    if request.method == 'POST':
        form = LabCheckInForm(request.POST)
        if form.is_valid():
            barcode = form.cleaned_data['barcode']
            rack = form.cleaned_data['rack']

            sample = Sample.objects.get(barcode=barcode)
            event = Event(
                status=SampleStatus.WAIT.value,
            )

            if sample is None:
                messages.add_message(request, messages.ERROR, _('Barcode nicht in Datenbank'))
            else:
                modified_rack = sample.modify(rack=rack)
                if modified_rack:
                    messages.add_message(request, messages.SUCCESS, _('Rack erfolgreich eingetragen'))
                modified_events = sample.modify(push__events=event)
                if modified_events:
                    messages.add_message(request, messages.SUCCESS, _('Event erfolgreich hinzugefügt'))

            form.fields['rack'].initial = rack
            return render(request, 'probe_check_in.html', {"form": form, "sample": sample})
    else:
        form = LabCheckInForm()
    return render(request, 'probe_check_in.html', {"form": form, "display_sample": False})


def probe_edit_rack(request):
    form = LabRackResultsForm()
    if request.method == 'POST':
        if form.is_valid():
            rack = form.rack.data.upper().strip()

            lamp_positive = form.lamp_positive.data.replace(',', '\n').replace(';', '\n')
            lamp_inconclusive = form.lamp_inconclusive.data.replace(',', '\n').replace(';', '\n')

            lamp_positive = [x.strip() for x in lamp_positive.split()]
            lamp_inconclusive = [x.strip() for x in lamp_inconclusive.split()]

            wrong_status_sequence = database_actions.rack_results(db, rack, lamp_positive, lamp_inconclusive)
            if wrong_status_sequence is None:
                flash(_('Keine Barcodes zu Rack gefunden'), 'error')
            else:
                for barcode in wrong_status_sequence:
                    flash(_('Falsche Statusfolge: ') + str(barcode), 'warning')
            return render_template('probe_rack_results.html', form=form)
    return render_template('probe_rack_results.html', form=form)


def probe_query(request):
    form = LabQueryForm()
    edit_form = LabProbeEditForm()
    if request.method == 'POST':
        if 'search' in request.POST.keys():
            form = LabQueryForm(request.POST)
            if form.is_valid():
                search = form.cleaned_data['search'].upper().strip()
                sample = Sample.objects.filter(barcode=search).first()
                return render(request, 'probe_query.html', {'form':form, 'edit_form':edit_form, 'sample':sample, 'search':search})
        if 'edit' in request.POST.keys():
            edit_form = LabProbeEditForm(request.POST)
            if edit_form.is_valid():
                print("Hello 1")
                barcode = edit_form.cleaned_data['barcode'].upper().strip()
                status = edit_form.cleaned_data['status'].upper().strip()
                rack = edit_form.cleaned_data['rack'].upper().strip()
                print(repr(barcode))
                print(repr(status))
                sample = Sample.objects.filter(barcode=barcode).first()
                if sample is None:
                    messages.add_message(request, messages.ERROR, _('Sample nicht gefunde'))
                else:
                    rack_changed = sample.modify(rack=rack)
                    if rack_changed:
                        messages.add_message(request, messages.SUCCESS, _('Sample rack geupdated'))
                    if status != '-':
                        status = SampleStatus[status]
                        event = Event(
                            status=status.value,
                        )
                        event_added = sample.modify(push__events=event)
                        if event_added:
                            messages.add_message(request, messages.SUCCESS, _('Status geupdated'))
                return render(request, 'probe_query.html', {'form': form, 'edit_form': edit_form, 'sample': sample})

    return render(request, 'probe_query.html', {'form': form, 'edit_form':edit_form})
