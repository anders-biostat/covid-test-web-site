from django import forms
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields import BLANK_CHOICE_DASH

from .models import RSAKey
from .statuses import SampleStatus


class LabQueryForm(forms.Form):
    search = forms.CharField(label=_("Barcode"), max_length=100)


class LabCheckInForm(forms.Form):
    barcodes = forms.CharField(
        label=_("Barcodes"),
        widget=forms.Textarea(attrs={"autofocus": "autofocus", "placeholder": "Barcode ..."}),
    )
    rack = forms.CharField(
        label=_("Rack Barcode (Optional)"), max_length=100, widget=forms.TextInput(attrs={"placeholder": "Rack ..."}),
        required=False
    )
    status = forms.ChoiceField(
        label="Status",
        choices=BLANK_CHOICE_DASH + [(s.name, s.name) for s in SampleStatus],
        required=True
    )
    comment = forms.CharField(
        label="Kommentar (Optional)", widget=forms.TextInput(attrs={"placeholder": "Add a comment ..."}),
        required=False
    )


class LabRackResultsForm(forms.Form):
    rack = forms.CharField(label=_("Rack (Barcode)"), max_length=100, required=False)

    lamp_positive = forms.CharField(label=_("LAMP positiv"), required=False)
    lamp_inconclusive = forms.CharField(label=_("LAMP unklares Ergebnis"), required=False)
    lamp_failed = forms.CharField(label=_("LAMP fehlgeschlagen"), required=False)


status_choices = [("-", "-")] + [(status.value, status.value) for status in SampleStatus]


class LabProbeEditForm(forms.Form):
    barcode = forms.CharField(label=_("Barcode"))
    rack = forms.CharField(label=_("Rack"))
    status = forms.ChoiceField(label=_("Probenstatus"), choices=status_choices, widget=forms.Select())
    comment = forms.CharField(label=_("Kommentar"), max_length=500, required=False)


class LabGenerateBarcodeForm(forms.Form):
    count = forms.IntegerField(label=_("Anzahl der batches"))
    key = forms.ModelChoiceField(RSAKey.objects.all(), label=_("Schlüssel"))
