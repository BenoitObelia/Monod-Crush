import logging

from django.contrib.messages.views import SuccessMessageMixin
from django.forms import Form
from django.http import HttpResponseRedirect
from django.views.generic import FormView, TemplateView

from about.forms import ContactForm
from monodcrush.customLogging import user_or_ip

log = logging.getLogger(__name__)


class ContactView(SuccessMessageMixin, FormView):
    """ View for the contact form """

    template_name = 'about/contact.html'
    form_class = ContactForm
    success_url = '/'

    success_message = "Votre message a bien été envoyé."

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        log.info(f"{user_or_ip(self.request)} - sent contact form\n"
                 f"subject : {form.cleaned_data['subject']}\n"
                 f"message : {form.cleaned_data['message']}\n"
                 f"email : {form.cleaned_data['email'] if form.cleaned_data['email'] else 'no email'}",
                 extra={"mention": True})
        return super().form_valid(form)


class WhoAreWeView(TemplateView):
    """ View for the "who are we" page """

    template_name = 'about/who-are-we.html'

