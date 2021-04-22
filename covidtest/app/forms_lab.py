from django import forms
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields import BLANK_CHOICE_DASH
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import RSAKey, Bag
from .statuses import SampleStatus


class LabQueryForm(forms.Form):
    search = forms.CharField(label=_("Barcode"), max_length=100)


class LabCheckInForm(forms.Form):
    barcodes = forms.CharField(
        label=_("Barcodes"),
        widget=forms.Textarea(
            attrs={"autofocus": "autofocus", "placeholder": "Barcode ..."}
        ),
    )
    rack = forms.CharField(
        label=_("Rack Barcode (Optional)"),
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Rack ..."}),
        required=False,
    )
    status = forms.ChoiceField(
        label="Status",
        choices=BLANK_CHOICE_DASH + [(s.name, s.name) for s in SampleStatus],
        required=True,
    )
    comment = forms.CharField(
        label="Kommentar (Optional)",
        widget=forms.TextInput(attrs={"placeholder": "Add a comment ..."}),
        required=False,
    )


class LabRackResultsForm(forms.Form):
    rack = forms.CharField(label=_("Rack (Barcode)"), max_length=100, required=False)

    lamp_positive = forms.CharField(label=_("LAMP positiv"), required=False)
    lamp_inconclusive = forms.CharField(
        label=_("LAMP unklares Ergebnis"), required=False
    )
    lamp_failed = forms.CharField(label=_("LAMP fehlgeschlagen"), required=False)


status_choices = [("-", "-")] + [
    (status.value, status.value) for status in SampleStatus
]


class LabProbeEditForm(forms.Form):
    barcode = forms.CharField(label=_("Barcode"))
    rack = forms.CharField(label=_("Rack"))
    status = forms.ChoiceField(
        label=_("Probenstatus"), choices=status_choices, widget=forms.Select()
    )
    comment = forms.CharField(
        label=_("Kommentar"), max_length=10000, required=False, widget=forms.Textarea()
    )


class LabGenerateBarcodeForm(forms.Form):
    count = forms.IntegerField(label=_("Anzahl der batches"))
    key = forms.ModelChoiceField(RSAKey.objects.all(), label=_("Schlüssel"))


class BagManagementQueryForm(forms.Form):
    search = forms.CharField(max_length=255)

    def clean_search(self) -> list:
        search_value = self.cleaned_data["search"]
        if "," in search_value:
            search_value = [value.strip() for value in search_value.split(",")]
            return search_value
        return [search_value]


class BagHandoutForm(forms.ModelForm):
    comment = forms.CharField(max_length=1000, disabled=True, required=False)
    name = forms.CharField(max_length=255, disabled=True, required=False)

    class Meta:
        model = Bag
        fields = (
            "id",
            "name",
            "comment",
            "recipient",
            "handed_out_on",
            "handed_out_by",
        )

    def clean(self):
        # Check if bag has at least one sample
        if self.instance.samples.count() == 0:
            raise ValidationError(
                f"Beutel mit ID {self.instance.pk} enthält keine Proben!"
            )

        # Check if no prior recipient
        elif self.instance.recipient:
            raise ValidationError(
                f"Beutel mit ID {self.instance.pk} ist bereits einem Abnehmer zugeordnet!"
            )

        # Check if all samples have status PRINTED
        invalid_status = []
        for sample in self.instance.samples.all():
            event = sample.get_statuses().last()
            if event is None or event.status != SampleStatus.PRINTED.value:
                invalid_status.append(sample.barcode)
        if len(invalid_status) > 0:
            raise ValidationError(
                f"Beutel mit ID {self.instance.pk} enthält mindestens eine "
                + f"Probe mit ungültigem Status -- Barcodes: {invalid_status}"
            )

        # Check if a new recipient was set
        if not self.cleaned_data.get("recipient"):
            raise ValidationError(
                f"Beutel mit ID {self.instance.pk} wurde keinem Abnehmer zugeordnet"
            )

        self.cleaned_data["handed_out_on"] = timezone.now()

        return self.cleaned_data


BagHandoutModelFormSet = forms.modelformset_factory(Bag, form=BagHandoutForm, extra=0)
