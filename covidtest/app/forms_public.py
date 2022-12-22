from django import forms
from django.utils.translation import gettext_lazy as _

class ResultsQueryForm(forms.Form):
    access_code = forms.CharField(
        label=_("Access-Code / Zugangscode"), widget=forms.TextInput(attrs={"placeholder": _("Access-Code (z.B. A12 345 678 910)")})
    )

    def clean(self):
        cleaned_data = super(ResultsQueryForm, self).clean()
        cleaned_data["access_code"] = cleaned_data.get("access_code").upper().replace(" ", "").strip()

class AbonnementForm(forms.Form):
    key = forms.CharField(
        label=_("Simplepush.io Key"), widget=forms.TextInput(attrs={"placeholder": _("key")})
    )

    actions = (
        ("1", _("Abonnieren")),
        ("2", _("Deabonnieren")),
    )
    action = forms.ChoiceField(label=_("Abonnieren/Deabonnieren"), widget=forms.Select(), choices=actions)

    def clean(self):
        cleaned_data = super(AbonnementForm, self).clean()
        cleaned_data["key"] = cleaned_data.get("key").replace(" ", "").strip()
