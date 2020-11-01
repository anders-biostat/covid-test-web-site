import hashlib, binascii
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from .forms_public import ConsentForm, RegistrationForm, ResultsQueryForm
from .models import Sample, Registration, Event
from .statuses import SampleStatus
from .encryption_helper import rsa_instance_from_key, encrypt_subject_data


def index(request):
    barcode = None
    if 'barcode' in request.GET:
        barcode = request.GET['barcode']
    if barcode is not None:
        request.session['barcode'] = barcode.upper()
        return redirect('consent')
    return render(request, 'public/index.html')


def instructions(request):
    barcode = None
    if 'barcode' in request.session:
        barcode = request.session.get('barcode').upper()
    if 'barcode' in request.GET:
        barcode = request.GET['barcode'].upper()
    return render(request, 'public/instructions.html', {'barcode': barcode})


def consent(request):
    form = ConsentForm()
    if request.method == 'POST':
        form = ConsentForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['terms'] == True:
                request.session['consent'] = True
                return redirect('app:register')
            messages.add_message(request, messages.WARNING,
                                 _('Sie müssen erst der Teilnahme zustimmen, um fortzufahren'))
            return render(request, 'public/consent.html', {'form': form})
    return render(request, 'public/consent.html', {'form': form})


def results_query(request):
    form = ResultsQueryForm()
    if request.method == 'POST':
        form = ResultsQueryForm(request.POST)
        if form.is_valid():
            barcode = form.cleaned_data['barcode'].upper()
            form_password = form.cleaned_data['password']

            # Hash entered password
            sha_instance = hashlib.sha3_384()
            sha_instance.update(form_password.encode("utf-8"))
            form_password_hashed = binascii.b2a_base64(sha_instance.digest(), newline=False).decode("ascii")

            # Check if barcode exists
            sample = Sample.objects.filter(barcode=barcode).first()

            # No sample found for barcode
            if sample is None:
                messages.add_message(request, messages.ERROR, _('Der Barcode ist unbekannt. Bitte erneut versuchen.'))
                return redirect('app:results_query')

            # Checking the count of registrations
            #

            # More than one registration -> not showing result
            registration_count = sample.registrations.count()
            if registration_count > 1:
                return render(request, "pages/multiple-registeration.html", {'barcode': barcode})

            # No registration -> redirection to registration
            if registration_count < 1:
                messages.add_message(request, messages.WARNING,
                                     _(
                                         'Der Barcode wurde nicht registriert. Bitte registrieren Sie den Barcode vorher.'))
                request.session['barcode'] = barcode
                return redirect('app:register')

            # Wrong password
            if form_password_hashed != sample['registrations'][0]['password_hash']:
                messages.add_message(request, messages.ERROR,
                                     _(
                                         'Das Passwort stimmt nicht mit dem überein, dass Sie beim Registrieren der Barcodes gewählt haben. Bitte versuchen Sie es noch einmal.'))
                return redirect('app:results_query')

            # Checking the status of the sample
            status = sample.get_status()
            if status is not None:
                status = SampleStatus[status['status']]
                if status == SampleStatus.PCRPOS:
                    return render(request, "public/pages/test-PCRPOS.html")
                if status == SampleStatus.PCRNEG:
                    return render(request, "public/pages/test-PCRNEG.html")
                if status == SampleStatus.LAMPPOS:
                    return render(request, "public/pages/test-LAMPPOS.html")
                if status == SampleStatus.LAMPNEG:
                    return render(request, "public/pages/test-LAMPNEG.html")
                if status == SampleStatus.LAMPINC:
                    return render(request, "public/pages/test-LAMPINC.html")
                if status == SampleStatus.UNDEF:
                    return render(request, "public/pages/test-UNDEF.html")
                if status == SampleStatus.WAIT:
                    return render(request, "public/pages/test-WAIT.html")
                return render(request, "public/pages/test-UNDEF.html")
    return render(request, 'public/result-query.html', {'form': form})


def information(request):
    return render(request, 'public/pages/information.html')


def register(request):
    if 'barcode' in request.session:
        barcode = request.session.get('barcode').upper()
    if 'barcode' in request.GET:
        barcode = request.GET['barcode'].upper()

    if request.session.get("consent") != True:
        return redirect('app:consent')

    request.session["barcode"] = None

    form = RegistrationForm(initial={'barcode': barcode})
    if request.method == 'POST':  # POST
        form = RegistrationForm(request.POST)
        if form.is_valid():
            barcode = form.cleaned_data['barcode'].upper().strip()

            name = form.cleaned_data['name']
            address = form.cleaned_data['address']
            contact = form.cleaned_data['contact']
            password = form.cleaned_data['password']
            password_repeat = form.cleaned_data['password_repeat']

            sample = Sample.objects.filter(barcode=barcode).first()

            if sample is None:
                messages.add_message(request, messages.ERROR, _('Der Barcode ist unbekannt. Bitte erneut versuchen.'))
                return render(request, 'register.html', {'form': form})

            request.session["barcode"] = barcode

            rsa_inst = rsa_instance_from_key(sample.key.public_key)
            doc = encrypt_subject_data(rsa_inst, name, address, contact, password)

            sample.registrations.create(
                name_encrypted=doc['name_encrypted'],
                address_encrypted=doc['address_encrypted'],
                contact_encrypted=doc['contact_encrypted'],
                password_hash=doc['password_hash'],
                public_key_fingerprint=doc['public_key_fingerprint'],
                session_key_encrypted=doc['session_key_encrypted'],
                aes_instance_iv=doc['aes_instance_iv'],
            )
            messages.add_message(request, messages.SUCCESS, _('Erfolgreich registriert'))
            return redirect('app:instructions')
    return render(request, 'public/register.html', {'form': form, 'barcode': barcode})


def pages(request, page):
    return render(request, "public/pages/" + page)
