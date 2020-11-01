from django import forms
from django.utils.translation import gettext as _


class ConsentForm(forms.Form):
    terms = forms.BooleanField(label=_('Einverständnis'), required=True)


class RegistrationForm(forms.Form):
    class Meta:
        layout = [
            ("Field", "barcode"),

            ("Text", _("<h3 class=\"ui dividing header\">Persönliche Daten</h3>")),
            ("Text", _(
                "<p>Datenschutz-Hinweis: Ihr Name und Ihre Kontaktdaten werden streng vertraulich behandelt. Nur die Mitarbeiter des Gesundheitsamts haben darauf Zugriff.</p>")),
            ("Field", "name"),
            ("Field", "address"),
            ("Field", "contact"),

            ("Two Fields",
             ("Field", "password"),
             ("Field", "password_repeat"),
             ),
        ]

    barcode = forms.CharField(label=_('Code auf dem Probenröhrchen (im Testkit erhalten):'),
                              widget=forms.TextInput(
                                attrs={"placeholder": _("Barcode des Teströhrchens"), "help": "Hallo"}))
    name = forms.CharField(label=_('Name (Nachname, Vorname):'),
                           widget=forms.TextInput(attrs={"placeholder": _("Nachname, Vorname")}))
    address = forms.CharField(label=_('Anschrift (Straße, Hausnummer, Postleitzahl, Wohnort):'),
                              widget=forms.TextInput(
                                  attrs={"placeholder": _("Straße, Hausnummer, Postleitzahl, Wohnort")}))
    contact = forms.CharField(label=_('Telefonnummer:'),
                              widget=forms.TextInput(attrs={"placeholder": _("Telefonnummer")}))

    password = forms.CharField(label=_('Passwort:'),
                               widget=forms.PasswordInput(attrs={"placeholder": _("Passwort")}))
    password_repeat = forms.CharField(label=_('Passwort wiederholen:'),
                                      widget=forms.PasswordInput(attrs={"placeholder": _("Passwort wiederholen")}))

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("password_repeat")

        if password != confirm_password:
            raise forms.ValidationError(_("Passwörter müssen übereinstimmen"))


class ResultsQueryForm(forms.Form):
    barcode = forms.CharField(label=_('Barcode'), widget=forms.TextInput(attrs={"placeholder": _("Barcode")}))
    password = forms.CharField(label=_('Passwort'), widget=forms.PasswordInput(attrs={"placeholder": _("Passwort")}))
