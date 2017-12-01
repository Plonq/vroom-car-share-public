#
#   Author(s): Huon Imberger
#   Description: Email utility methods
#

from django.template import Engine, Context
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from .models import EmailTemplate


def send_templated_email(template_name, context, recipient_list, from_email=settings.DEFAULT_FROM_EMAIL, attachment_filename=None, attachment_data=None):
    """
    Sends an email using a template stored in the database (based on the template name)
    Also supports attaching a file
    """
    # Get template from database, render it using the provided context
    template_engine = Engine()
    email_template = EmailTemplate.objects.get(name=template_name)
    subject_template = template_engine.from_string(email_template.subject)
    body_template = template_engine.from_string(email_template.body)
    email_context = Context(context)
    email_subject = subject_template.render(email_context)
    email_body = body_template.render(email_context)
    email_body_full = render_to_string(
        'emails/default.html',
        context = {'rendered_email_body': email_body}
    )

    # Send the email
    text_message = strip_tags(email_body_full)
    email = EmailMultiAlternatives(
        to=recipient_list,
        from_email=from_email,
        subject=email_subject,
        body=text_message,
    )
    email.attach_alternative(email_body_full, "text/html")
    # Attachment?
    if attachment_filename:
        if attachment_data:
            email.attach(attachment_filename, attachment_data)
        else:
            email.attach_file(attachment_filename)
    elif attachment_data:
        email.attach('attachment', attachment_data)
    email.send()
