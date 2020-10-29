import sys
from django.shortcuts import render
from django.contrib import messages
from django.utils.translation import gettext as _

from common.models import Sample, Event, Registration, KeyInformation
from common.statuses import SampleStatus

from .forms import LabCheckInForm

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


def probe_edit_rack():
    form = LabRackResultsForm()
    if request.method == 'POST':
        if form.validate_on_submit():
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
            return render_template('lab/probe_rack_results.html', form=form)
    return render_template('lab/probe_rack_results.html', form=form)

"""
def probe_query():
    form = LabQueryForm()
    edit_form = LabProbeEditForm()
    if request.method == 'POST':
        if 'search' in request.form:
            if form.validate_on_submit():
                samples = db['samples'].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=timezone))
                search = form.search.data.upper().strip()
                sample = samples.find_one({'_id': search})
                return render_template('lab/probe_query.html', form=form, edit_form=edit_form, sample=sample, search=search)
        if 'edit' in request.form:
            if edit_form.validate_on_submit():
                samples = db['samples'].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=timezone))
                barcode = edit_form.barcode.data.upper().strip()
                status = edit_form.status.data.upper().strip()
                rack = edit_form.rack.data.upper().strip()

                sample = samples.find_one({'_id': barcode})
                if sample is None:
                    flash(_('Sample nicht gefunden'), 'error')
                else:
                    if rack != sample['rack']:
                        samples.update_one({'_id': sample['_id']}, {'$set': {'rack': rack}}, upsert=True)
                        flash(_('Sample rack geupdated'), 'positive')

                    if status != '-':
                        status = SampleStatus[status]
                        new_sample = database_actions.update_status(db, sample['_id'], status, rack=None)
                        if new_sample is not None:
                            flash(_('Status geupdated'), 'positive')
                    else:
                        new_sample = sample
                return render_template('lab/probe_query.html', form=form, edit_form=edit_form, sample=new_sample)

    return render_template('lab/probe_query.html', form=form, edit_form=edit_form)
"""
