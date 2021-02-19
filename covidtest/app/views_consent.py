from .forms_public import AgeGroupForm, ConsentForm
from django.views import View
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.template.loader import get_template
from django.http import HttpResponse
import hashlib

import logging
logger = logging.getLogger(__name__)

class AgeGroupFormView(View):

    def get(self, request):
        return render(request, "public/age-group-form.html")


def consent_pages_to_be_displayed( agegroup ):

    consents = []

    # First, forms for parents, if participant is a minor
    if agegroup != "adult":
        consents.append({"consent_type": "parents", "required": True})
        consents.append({"consent_type": "parents_biobank", "required": True})

    # Now, forms for the participants, depending on the age
    if agegroup == "adult":
        consents.append({"consent_type": "adults", "required": True})
        consents.append({"consent_type": "adults_biobank", "required": True})
    elif agegroup == "adolescent":
        consents.append({"consent_type": "adolescents", "required": True})
        consents.append({"consent_type": "adolescents_biobank", "required": True})
    elif agegroup == "child":
        consents.append({"consent_type": "children", "required": True})
        consents.append({"consent_type": "children_biobank", "required": True})
    else:
        # TODO handle this exception in case some enters with an invalid agegroup
        raise Exception("Unexpected 'agegroup' value.")

    return consents

def get_template_file_for_consent_type(consent_type):
    return "public/info_and_consent/" + consent_type + ".html"

class ConsentView(View):

    def render_info_and_consent(self, request):

        if "consent_forms_to_be_displayed" not in request.session:
            logger.warning("Consent page accessed bypassing age query")
            return redirect("app:consent_age")

        # Is there still work to do?
        if len(request.session["consent_forms_to_be_displayed"]) == 0:
            print( "Consents obtained:", request.session["consents_obtained"] )
            return redirect("app:register")

        data = request.session["consent_forms_to_be_displayed"][0].copy()
        if not data["required"]:
            raise Exception("Non-required consent is not yet implemented.")
        data["num_pages"] = request.session["num_pages"]
        data["page_number"] = data["num_pages"] - len(request.session["consent_forms_to_be_displayed"]) + 1

        return render(request, get_template_file_for_consent_type(data["consent_type"]), data)

    def get(self, request):

        if "agegroup" in request.GET:
            consents = consent_pages_to_be_displayed( request.GET["agegroup"] )
            request.session["consent_forms_to_be_displayed"] = consents
            request.session["num_pages"] = len(consents)
            request.session["consents_obtained"] = []

        return self.render_info_and_consent(request)

    def post(self, request):
        form = ConsentForm(request.POST)
        if form.is_valid():
            # First assert that we use the right template
            # TODO find a better solution for this fix
            #  An error occurs if a user clicks on consent and then goes one step back via the browser button
            try:
                if request.session["consent_forms_to_be_displayed"][0]["consent_type"] != form.cleaned_data["consent_type"]:
                    raise ValueError("Template mix-up")
            except (IndexError, ValueError) as e:
                logger.warning(e)
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("Ein technischer Fehler ist aufgetreten. Bitte die Registrierung nochmals versuchen.")
                )
                return redirect("app:index")
            # Now store the consent in the session
            if form.cleaned_data["consent_given"]:
                request.session["consents_obtained"].append( form.cleaned_data["consent_type"] )
            # And remove the template from the to-do list
            request.session["consent_forms_to_be_displayed"] = request.session["consent_forms_to_be_displayed"][1:]
            # Finally, go back to start
            return self.render_info_and_consent(request)
        raise "Invalid form"  # shouldn't happen



def get_consent_md5(consent_type):
    # get full path of HTML file with info and consent text
    filepath = get_template(get_template_file_for_consent_type(consent_type)).origin.name
    # calculate its MD5 hash
    with open(filepath, 'rb' ) as f:
        hashsum = hashlib.md5(f.read())
    return hashsum.hexdigest()
