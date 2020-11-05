import hashlib, binascii
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from .forms_public import ConsentForm, RegistrationForm, ResultsQueryForm, ResultsQueryFormLegacy
from .models import Sample, Registration, Event, RSAKey
from .statuses import SampleStatus
from .encryption_helper import rsa_instance_from_key, encrypt_subject_data


def index(request):
    access_code = None
    if 'access_code' in request.GET:
        access_code = request.GET['access_code']
    if access_code is not None:
        request.session['access_code'] = access_code
        return redirect('consent')
    return render(request, 'public/index.html')


def instructions(request):
    access_code = None
    if 'access_code' in request.session:
        access_code = request.session.get('access_code')
    if 'access_code' in request.GET:
        access_code = request.GET['access_code']
    return render(request, 'public/instructions.html')


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


def render_status(request, event):
    if event is not None:
        try:
            status = SampleStatus[event.status]
        except KeyError:
            return render(request, "public/pages/test-ERROR.html", {'error': _('Status unbekannt')})

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
        if status == SampleStatus.LAMPFAIL:
            return render(request, "public/pages/test-LAMPFAIL.html")
        if status == SampleStatus.UNDEF:
            return render(request, "public/pages/test-UNDEF.html")
        if status == SampleStatus.WAIT:
            return render(request, "public/pages/test-WAIT.html")
        return render(request, "public/pages/test-UNDEF.html")
    return render(request, 'public/pages/test-ERROR.html', {'error': _('Kein Status vorhanden')})


def results_query(request):
    form = ResultsQueryForm()
    if request.method == 'POST':
        form = ResultsQueryForm(request.POST)
        if form.is_valid():
            access_code = form.cleaned_data['access_code']

            # Check if access_code exists
            sample = Sample.objects.filter(access_code=access_code).first()

            # No sample found for access_code
            if sample is None:
                messages.add_message(request, messages.ERROR,
                                     _('Der Zugangscode ist unbekannt. Bitte erneut versuchen.'))
                return redirect('app:results_query')

            # No registration -> redirection to registration
            registration_count = sample.registrations.count()
            if registration_count < 1:
                messages.add_message(request, messages.WARNING,
                                     _(
                                         'Der Zugangscode wurde nicht registriert. Bitte registrieren Sie sich vorher.'))
                request.session['access_code'] = access_code
                return redirect('app:register')

            # Legacy code for old samples with password registrations


            # Registered and password exists
            if sample.password_hash is not None:
                form = ResultsQueryFormLegacy(request.POST)

                # Check if form is legacy
                if 'password' not in request.POST.keys():
                    return render(request, 'public/result-query.html', {'form': form})

                if form.is_valid():
                    password = form.cleaned_data['password']
                    sha_instance = hashlib.sha3_384()
                    sha_instance.update(password.encode("utf-8"))
                    password_hashed = binascii.b2a_base64(sha_instance.digest(), newline=False).decode("ascii")
                    if password_hashed != sample.password_hash:
                        messages.add_message(request, messages.ERROR,
                                             _(
                                                 'Das eingegebene Passwort ist falsch. Bitte probieren sie es nochmal.'))
                        request.session['access_code'] = access_code
                        return render('public/result-query.html', {'form': form})

            # Checking the status of the sample
            event = sample.get_status()
            return render_status(request, event)

    return render(request, 'public/result-query.html', {'form': form})


def information(request):
    return render(request, 'public/pages/information.html')


def register(request):
    access_code = None

    if 'access_code' in request.session:
        access_code = request.session.get('access_code')
    if 'access_code' in request.GET:
        access_code = request.GET['access_code']

    if request.session.get("consent") != True:
        return redirect('app:consent')

    request.session["access_code"] = None

    form = RegistrationForm(initial={'access_code': access_code})
    if request.method == 'POST':  # POST
        form = RegistrationForm(request.POST)
        if form.is_valid():
            access_code = form.cleaned_data['access_code'].upper().strip()
            name = form.cleaned_data['name']
            address = form.cleaned_data['address']
            contact = form.cleaned_data['contact']

            sample = Sample.objects.filter(access_code=access_code).first()

            if sample is None:
                messages.add_message(request, messages.ERROR,
                                     _('Der Zugangscode ist unbekannt. Bitte erneut versuchen.'))
                return render(request, 'public/register.html', {'form': form})

            request.session["access_code"] = access_code

            rsa_inst = rsa_instance_from_key(sample.bag.rsa_key.public_key)
            doc = encrypt_subject_data(rsa_inst, name, address, contact)

            sample.registrations.create(
                name_encrypted=doc['name_encrypted'],
                address_encrypted=doc['address_encrypted'],
                contact_encrypted=doc['contact_encrypted'],
                public_key_fingerprint=doc['public_key_fingerprint'],
                session_key_encrypted=doc['session_key_encrypted'],
                aes_instance_iv=doc['aes_instance_iv'],
            )
            sample.events.create(
                status="INFO",
                comment="sample registered"
            )

            messages.add_message(request, messages.SUCCESS, _('Erfolgreich registriert'))
            return redirect('app:instructions')
    return render(request, 'public/register.html', {'form': form})


def pages(request, page):
    return render(request, "public/pages/" + page)