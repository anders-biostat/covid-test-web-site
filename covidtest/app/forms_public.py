from django import forms
from django.utils.translation import ugettext_lazy as _
import bleach


class ConsentForm(forms.Form):
    consent_type = forms.CharField(widget=forms.HiddenInput())
    consent_given = forms.BooleanField(label=_("Einverständnis"), required=True)

class AgeGroupForm(forms.Form):
    age = forms.IntegerField(required=True)

class RegistrationForm(forms.Form):
    class Meta:
        layout = [
            ("Field", "access_code"),
            ("Field", "name"),
            ("Field", "address"),
            ("Field", "contact"),
        ]

    access_code = forms.CharField(
        label=_("Zugangscode (beiliegender Zettel):"),
        widget=forms.TextInput(attrs={"placeholder": _("Zugangscode"), "help": "Hallo"}),
    )
    name = forms.CharField(
        label=_("Name:"), widget=forms.TextInput(attrs={"placeholder": _("Nachname, Vorname")})
    )
    address = forms.CharField(
        label=_("Anschrift:"),
        widget=forms.Textarea(attrs={"placeholder": _("Straße, Hausnummer, Postleitzahl, Wohnort")}),
    )
    contact = forms.CharField(
        label=_("Telefonnummer:"), widget=forms.TextInput(attrs={"placeholder": _("Telefonnummer")})
    )

    def clean_name(self):
        return bleach.clean(self.cleaned_data["name"])

    def clean_address(self):
        return bleach.clean(self.cleaned_data["address"])

    def clean_contact(self):
        return bleach.clean(self.cleaned_data["contact"])

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        cleaned_data["access_code"] = cleaned_data.get("access_code").upper().replace(" ", "").strip()


class ResultsQueryForm(forms.Form):
    access_code = forms.CharField(
        label=_("Zugangscode / Access-Code"), widget=forms.TextInput(attrs={"placeholder": _("Zugangscode / Access-Code")})
    )

    def clean(self):
        cleaned_data = super(ResultsQueryForm, self).clean()
        cleaned_data["access_code"] = cleaned_data.get("access_code").upper().replace(" ", "").strip()

class ResultsQueryFormLegacy(forms.Form):
    access_code = forms.CharField(
        label=_("Zugangscode"), widget=forms.TextInput(attrs={"placeholder": _("Zugangscode")})
    )
    password = forms.CharField(label=_("Passwort"), widget=forms.PasswordInput(attrs={"placeholder": _("Passwort")}))
