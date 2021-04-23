from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from .forms_lab import LabProbeEditForm
from .models import Event, Sample
from .statuses import SampleStatus


def sample_pks_of_event(event_search_key):
    found_events_sample_pks = []
    events = Event.objects.filter(status__icontains=event_search_key).exclude(
        status=SampleStatus.INFO.value
    )
    if events:
        for event in events:
            sample_to_check = Sample.objects.get(events=event)
            latest_status = sample_to_check.get_latest_internal_status()
            if event == latest_status:
                found_events_sample_pks.append(sample_to_check.pk)
    return found_events_sample_pks


def find_samples(search, search_category=None):
    try:
        if search_category is None or search_category == "all":
            found_single_sample = Sample.objects.filter(
                Q(barcode=search) | Q(access_code=search)
            ).first()
            if found_single_sample:
                edit_form = LabProbeEditForm(
                    initial={
                        "rack": found_single_sample.rack,
                        "comment": "Status changed in lab interface",
                    }
                )
                return {"sample": found_single_sample, "edit_form": edit_form}

            found_multiple_samples = Sample.objects.filter(
                Q(rack__icontains=search)
                | Q(bag__pk__iexact=search)
                | Q(pk__in=sample_pks_of_event(event_search_key=search))
            )
            if found_multiple_samples:
                return {"multi_sample": found_multiple_samples}
        elif search_category == "barcode":
            sample = Sample.objects.get(barcode=search)
            return {"sample": sample}
        elif search_category == "accessCode":
            sample = Sample.objects.get(access_code=search)
            return {"sample": sample}
        elif search_category == "status":
            multi_sample = Sample.objects.filter(
                pk__in=sample_pks_of_event(event_search_key=search)
            )
            return {"multi_sample": multi_sample}
        elif search_category == "bag":
            multi_sample = Sample.objects.filter(bag__pk__iexact=search)
            return {"multi_sample": multi_sample}
        elif search_category == "rack":
            multi_sample = Sample.objects.filter(rack__icontains=search)
            return {"multi_sample": multi_sample}
    except ObjectDoesNotExist:
        pass

    return dict()
