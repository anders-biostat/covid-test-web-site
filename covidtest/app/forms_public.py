from django import forms
from django.utils.translation import ugettext_lazy as _

class ResultsQueryForm(forms.Form):
    access_code = forms.CharField(
        label=_("Access-Code / Zugangscode"), widget=forms.TextInput(attrs={"placeholder": _("Access-Code (z.B. A12 345 678 910)")})
    )

    def clean(self):
        cleaned_data = super(ResultsQueryForm, self).clean()
        cleaned_data["access_code"] = cleaned_data.get("access_code").upper().replace(" ", "").strip()