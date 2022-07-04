from django.forms import Form, EmailField, CharField, Textarea, EmailInput


class ContactForm(Form):
    subject = CharField(label="Sujet", max_length=100)
    message = CharField(label="", max_length=1000, widget=Textarea)
    email = EmailField(help_text="Remplissez le champ avec votre email si vous souhaitez être recontacté",
                       label="Email (facultatif)",
                       widget=EmailInput(attrs={"placeholder": "exemple@monsite.com"}),
                       required=False)
