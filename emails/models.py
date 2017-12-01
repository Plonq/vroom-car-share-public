#
#   Author(s): Huon Imberger
#   Description: Defines email-related database models for
#

from django.db import models

from ckeditor.fields import RichTextField


class EmailTemplate(models.Model):
    """
    Email template object, including a rich text body to allow staff to edit emails sent to users
    """
    name = models.CharField(
        max_length=30,
        help_text='If editing the name of existing template, you must also update any code that uses it!'
    )
    subject = models.CharField(max_length=30, help_text='Please refer to the code to determine the context available')
    body = RichTextField( help_text='Please refer to the code to determine the context available')
