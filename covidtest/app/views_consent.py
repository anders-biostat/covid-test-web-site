from .forms_public import AgeGroupForm, ConsentForm
from django.views import View
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.template.loader import get_template, render_to_string
import hashlib


class AgeGroupFormView(View):
    def get(self, request):
        form = AgeGroupForm()
        clear_consent_session(request.session)
        return render(request, "public/age-group-form.html")

    def post(self, request):
        form = AgeGroupForm(request.POST)
        if form.is_valid():
            age = form.cleaned_data["age"]
            if age_is_valid(age):
                request.session["age"] = age
                return redirect("app:consent")

        messages.add_message(request, messages.ERROR, _("Der Teilnehmer muss mindestens 7 Jarhe alt sein."))
        return render(request, "public/age-group-form.html")


def age_is_valid(age):
    return age >= 7


def get_age_wizard(age):
    "returns consent names and info templates, None if age is None"
    if not age:
        return None
    if age >= 18:
        return dict(consent_adult="public/information-text.html")
    if age >= 12:
        return dict(
            consent_parent="public/information-parents.html",
            consent_teenager="public/information-teenager.html",
        )
    if age >= 7:
        return dict(
            consent_parent="public/information-parents.html",
            consent_child="public/information-child.html",
        )
    if age < 7:
        raise ValueError


def get_consent(session):
    return session.get("consent", [])


def set_consent(session, value):
    session["consent"] = value.copy()
    return session


def clear_consent_session(session):
    session.pop("age", None)
    session.pop("consent", None)


def get_age(session):
    return session.get("age")


def has_consent(session):
    consent = get_consent(session)
    age = get_age(session)
    wizard = get_age_wizard(age)
    if wizard:
        return all([cons in consent for cons in wizard.keys()])
    return False


class ConsentView(View):
    """
    consent is kept in the session variable "consent" as a list of strings,
    i.e. session["consent"] = ["consent_parents", "consent_teenager"].
    The view dispatches upon the state of the consent variable and renders
    the corresponding template, where different info is included in template_name.
    """

    success_url = "app:register"

    def get(self, request):
        if not get_age(request.session):
            return redirect("app:consent_age")
        return self.dispatch_consent(request)

    def post(self, request):
        """
        We check validity of consent submission:
        - there is age set
        - consent type is allowed and form md5 sums coincides with the
          md5 for this consent type in the session
        - ONLY then add consent to the session
        """
        age = get_age(request.session)
        if not age:
            return redirect("app:consent_age")
        form = ConsentForm(request.POST)
        if form.is_valid():
            if self.consent_is_valid(request.session, form):
                ## check that consent type is allowed and add it
                consent_type = form.cleaned_data["consent_type"]
                if consent_type in get_age_wizard(age):
                    request.session = self.add_consent(request.session, consent_type)
                return self.dispatch_consent(request)
        messages.add_message(request, messages.WARNING, _("Sie müssen erst der Teilnahme zustimmen, um fortzufahren"))
        return self.dispatch_consent(request)

    def next_consent(self, session_consents, consent_forms):
        "None if no any consents needed, info template path otherwise"
        for consent_type in consent_forms.keys():
            if consent_type not in session_consents:
                return consent_type

    def consent_is_valid(self, session, form):
        try:
            consent_type = form.cleaned_data["consent_type"]
            hash_is_correct = self.get_consent_md5(session, consent_type) == form.cleaned_data["version"]
            return form.cleaned_data["terms"] and hash_is_correct
        except KeyError:
            return False

    def add_consent(self, session, consent_type):
        consents = get_consent(session)
        if consent_type not in consents:
            consents.append(consent_type)
        return set_consent(session, consents)

    def dispatch_consent(self, request):
        """
        returns response with a new consent form or a redirect response.
        In case a form is sent, saves md5 fingerprint of the consent text to session.
        """
        age_wizard = get_age_wizard(get_age(request.session))
        consents = get_consent(request.session)
        consent_type = self.next_consent(consents, age_wizard)
        if consent_type:
            template_name = age_wizard[consent_type]
            md5 = self.compute_consent_md5(template_name)
            self.set_consent_md5(request.session, consent_type, md5)
            form = ConsentForm(initial=dict(consent_type=consent_type, version=md5))
            info_template = get_template(template_name)
            return render(
                request,
                "public/consent.html",
                dict(form=form, template_name=template_name),
            )
        return redirect(self.success_url)

    def compute_consent_md5(self, template):
        text = render_to_string(template)
        hashsum = hashlib.md5(text.encode("utf-8"))
        return hashsum.hexdigest()

    def get_consent_md5(self, session, consent_type):
        md5sums = session.get("consent_md5", dict())
        return md5sums.get(consent_type, None)

    def set_consent_md5(self, session, consent_type, md5):
        if "consent_md5" not in session:
            session["consent_md5"] = {}
        session["consent_md5"][consent_type] = md5
