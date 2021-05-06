from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import user_passes_test

from .forms_lab import LabProbeEditForm
from .models import Event, Sample, Bag
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


def is_in_group(*group_names):
    def in_groups(user):
        if user.is_authenticated:
            if bool(user.groups.filter(name__in=group_names)) | user.is_superuser:
                return True
        return False

    return user_passes_test(in_groups, login_url="/lab/access-denied")


class Search(object):
    """
    Start of a general purpose Search object to abstract and streamline all search needs.

    returns: None or Queryset
    """

    def __init__(self, value):
        self.__set_search(value)

    def __get_search(self):
        return self.__search

    def __set_search(self, search):
        if type(search) == list:
            self.__search = search
        else:
            self.__search = list(search)

    value = property(__get_search, __set_search)

    def bags(self):
        try:
            bags = (
                Bag.objects.prefetch_related("samples")
                .select_related("recipient")
                .filter(pk__in=self.__search)
            )
            if not bags:
                raise ValueError
        except ValueError:
            bags = (
                Bag.objects.prefetch_related("samples")
                .select_related("recipient")
                .filter(recipient__recipient_name__in=self.__search)
            )

        if not bags:
            return None
        return bags
