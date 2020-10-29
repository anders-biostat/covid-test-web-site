from django import forms
from django.utils.translation import gettext as _


class LabQueryForm(forms.Form):
    search = forms.CharField(label=_('Barcode'), max_length=100)


class LabCheckInForm(forms.Form):
    barcode = forms.CharField(label=_('Barcode'), max_length=100,
                              widget=forms.TextInput(attrs={'autofocus': 'autofocus', 'placeholder': 'Barcode ...'}))
    rack = forms.CharField(label=_('Rack'), max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Rack ...'}))


class LabRackResultsForm(forms.Form):
    rack = forms.CharField(label=_('Rack'), max_length=100)

    lamp_positive = forms.CharField(label=_('LAMP positiv'))
    lamp_inconclusive = forms.CharField(label=_('LAMP unklares Ergebnis'))
