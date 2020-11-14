from django import forms
from django.utils.translation import gettext as _


class ConsentForm(forms.Form):
    terms = forms.BooleanField(label=_("Einverständnis"), required=True)


class RegistrationForm(forms.Form):
    class Meta:
        layout = [
            ("Field", "access_code"),
            ("Text", _('<h3 class="ui dividing header">Persönliche Daten</h3>')),
            (
                "Text",
                _(
                    "<p>Datenschutz-Hinweis: Ihr Name und Ihre Kontaktdaten werden streng vertraulich behandelt. Nur die Mitarbeiter des Gesundheitsamts haben darauf Zugriff.</p>"
                ),
            ),
            ("Field", "name"),
            ("Field", "address"),
            ("Field", "contact"),
        ]

    access_code = forms.CharField(
        label=_("Zugangscode (beiliegender Zettel):"),
        widget=forms.TextInput(attrs={"placeholder": _("Zugangscode"), "help": "Hallo"}),
    )
    name = forms.CharField(
        label=_("Name (Nachname, Vorname):"),
        widget=forms.TextInput(attrs={"placeholder": _("Nachname, Vorname")}),
    )
    address = forms.CharField(
        label=_("Anschrift (Straße, Hausnummer, Postleitzahl, Wohnort):"),
        widget=forms.Textarea(attrs={"placeholder": _("Straße, Hausnummer, Postleitzahl, Wohnort")}),
    )
    contact = forms.CharField(
        label=_("Telefonnummer:"),
        widget=forms.TextInput(attrs={"placeholder": _("Telefonnummer")}),
    )

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        cleaned_data["access_code"] = cleaned_data.get("access_code").upper().replace(" ", "").strip()


class ResultsQueryForm(forms.Form):
    access_code = forms.CharField(
        label=_("Zugangscode"),
        widget=forms.TextInput(attrs={"placeholder": _("Zugangscode")}),
    )

    def clean(self):
        cleaned_data = super(ResultsQueryForm, self).clean()
        cleaned_data["access_code"] = cleaned_data.get("access_code").upper().replace(" ", "").strip()


class ResultsQueryFormLegacy(forms.Form):
    access_code = forms.CharField(
        label=_("Zugangscode"),
        widget=forms.TextInput(attrs={"placeholder": _("Zugangscode")}),
    )
    password = forms.CharField(
        label=_("Passwort"),
        widget=forms.PasswordInput(attrs={"placeholder": _("Passwort")}),
    )
