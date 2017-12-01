#
#   Author(s): Huon Imberger, Shaun O'Malley
#   Description: Defines forms, including validation rules
#

from django import forms
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, HTML, Submit
from crispy_forms.bootstrap import (PrependedText, FormActions)
from datetimewidget.widgets import DateWidget

import datetime as dt

from .models import Booking


class ContactForm(forms.Form):
    contact_name = forms.CharField(label='Your name', max_length=60)
    contact_email = forms.EmailField(label='Your email address', max_length=255)
    message = forms.CharField(widget=forms.Textarea, max_length=2000)

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'validated-form'
        self.helper.form_tag = True
        self.helper.layout = Layout(
            PrependedText('contact_name', '<span class="glyphicon glyphicon-user"></span>'),
            PrependedText('contact_email', '<span class="glyphicon glyphicon-envelope"></span>'),
            Field('message'),
            FormActions(Submit('Send', 'Send', css_class='btn btn-primary col-lg-12 col-sm-12 col-xs-12'))
        )


class BookingForm(forms.Form):
    TIMES = (
        ('00:00', '00:00'),
        ('01:00', '01:00'),
        ('02:00', '02:00'),
        ('03:00', '03:00'),
        ('04:00', '04:00'),
        ('05:00', '05:00'),
        ('06:00', '06:00'),
        ('07:00', '07:00'),
        ('08:00', '08:00'),
        ('09:00', '09:00'),
        ('10:00', '10:00'),
        ('11:00', '11:00'),
        ('12:00', '12:00'),
        ('13:00', '13:00'),
        ('14:00', '14:00'),
        ('15:00', '15:00'),
        ('16:00', '16:00'),
        ('17:00', '17:00'),
        ('18:00', '18:00'),
        ('19:00', '19:00'),
        ('20:00', '20:00'),
        ('21:00', '21:00'),
        ('22:00', '22:00'),
        ('23:00', '23:00'),
    )
    dateTimeOptions = {
        'format': 'dd/mm/yyyy',
        'startDate': timezone.localtime().date().isoformat(),
        'endDate': (timezone.localtime() + dt.timedelta(days=Booking.MAX_LENGTH_DAYS)).date().isoformat(),
        'clearBtn': False,
    }
    booking_start_date = forms.DateField(widget=DateWidget(options=dateTimeOptions, bootstrap_version=3))
    booking_start_time = forms.ChoiceField(choices=TIMES)
    booking_end_date = forms.DateField(widget=DateWidget(options=dateTimeOptions, bootstrap_version=3))
    booking_end_time = forms.ChoiceField(choices=TIMES)

    def clean_booking_start_time(self):
        booking_start_time = self.cleaned_data.get('booking_start_time')
        # Convert to time object
        booking_start_time = dt.datetime.strptime(booking_start_time, '%H:%M').time()
        return booking_start_time

    def clean_booking_end_time(self):
        booking_end_time = self.cleaned_data.get('booking_end_time')
        # Convert to time object
        booking_end_time = dt.datetime.strptime(booking_end_time, '%H:%M').time()
        return booking_end_time

    def clean(self):
        cleaned_data = super(BookingForm, self).clean()
        if ('booking_start_date' in cleaned_data and 'booking_start_time' in cleaned_data
                and 'booking_end_date' in cleaned_data and 'booking_end_time' in cleaned_data):
            schedule_start = timezone.make_aware(
                dt.datetime.combine(cleaned_data['booking_start_date'], cleaned_data['booking_start_time']),
                timezone=timezone.get_current_timezone()
            )
            schedule_end = timezone.make_aware(
                dt.datetime.combine(cleaned_data['booking_end_date'], cleaned_data['booking_end_time']),
                timezone=timezone.get_current_timezone()
            )
            # Make sure booking is less than max booking length
            length = schedule_end - schedule_start
            if length.days > Booking.MAX_LENGTH_DAYS:
                raise forms.ValidationError(
                    'You cannot book for longer than {0} days'.format(Booking.MAX_LENGTH_DAYS)
                )
            # Make sure schedule_end is later than schedule_start
            if schedule_end < schedule_start:
                raise forms.ValidationError('End time must be after the start time')
            # Make sure schedule_start is in the future or max one hour in past (if 11:15 should allow user
            # to book for 11:00-12:00)
            if schedule_start <= timezone.now() - dt.timedelta(hours=1):
                raise forms.ValidationError('Start time must be in the future')
            # Make sure end is after start (not the same as)
            if schedule_start == schedule_end:
                raise forms.ValidationError('End time must not be the same as the start time')
            # Insert parsed dates into cleaned_data so the view doesn't have to
            cleaned_data['schedule_start'] = schedule_start
            cleaned_data['schedule_end'] = schedule_end
        return cleaned_data

    def __init__(self, *args, **kwargs):
        initial_start_datetime = kwargs.pop('initial_start_datetime', None)
        initial_length = int(kwargs.pop('initial_length', 1))
        super(BookingForm, self).__init__(*args, **kwargs)
        if initial_start_datetime:
            # Set initial start time
            self.initial['booking_start_date'] = dt.datetime.strftime(initial_start_datetime, '%d/%m/%Y')
            self.initial['booking_start_time'] = dt.datetime.strftime(initial_start_datetime, '%H:%M')
            # Set initial end time
            initial_end_datetime = initial_start_datetime + dt.timedelta(hours=initial_length)
            self.initial['booking_end_date'] = dt.datetime.strftime(initial_end_datetime, '%d/%m/%Y')
            self.initial['booking_end_time'] = dt.datetime.strftime(initial_end_datetime, '%H:%M')
        # Crispy Forms
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Booking Start',
                Div(
                    Div(
                        Field('booking_start_date', css_class='datepicker', placeholder='Date'),
                        css_class='col-sm-8',
                    ),
                    Div(
                        'booking_start_time',
                        css_class='col-sm-4',
                    ),
                    css_class='row',
                )
            ),
            Fieldset(
                'Booking End',
                Div(
                    Div(
                        Field('booking_end_date', css_class='datepicker', placeholder='Date'),
                        css_class='col-sm-8',
                    ),
                    Div(
                        'booking_end_time',
                        css_class='col-sm-4',
                    ),
                    css_class='row',
                )
            )
        )


class ExtendBookingForm(forms.Form):
    """
    Form for extending a booking
    """
    dateTimeOptions = {
        'format': 'dd/mm/yyyy',
        'clearBtn': False,
    }
    new_end_date = forms.DateField()
    new_end_time = forms.ChoiceField(choices=BookingForm.TIMES)

    def clean_new_end_time(self):
        new_end_time = self.cleaned_data.get('new_end_time')
        # Convert to time object
        new_end_time = dt.datetime.strptime(new_end_time, '%H:%M').time()
        return new_end_time

    def clean(self):
        cleaned_data = super(ExtendBookingForm, self).clean()
        new_schedule_end = timezone.make_aware(
            dt.datetime.combine(cleaned_data['new_end_date'], cleaned_data['new_end_time']),
            timezone=timezone.get_current_timezone()
        )
        if new_schedule_end:
            # Make sure new end date is not before previous end date
            if new_schedule_end <= self.current_booking_end:
                raise forms.ValidationError('New end time must be later than current end time')
        # Insert parsed date into cleaned_data so the view doesn't have to
        cleaned_data['new_schedule_end'] = new_schedule_end
        return cleaned_data

    def __init__(self, *args, **kwargs):
        self.current_booking_end = kwargs.pop('current_booking_end', None)
        super(ExtendBookingForm, self).__init__(*args, **kwargs)
        # Set date minimum
        if self.current_booking_end:
            self.dateTimeOptions['startDate'] = self.current_booking_end.isoformat()
            self.fields['new_end_date'].widget = DateWidget(options=self.dateTimeOptions, bootstrap_version=3)
            # Set initial values, first converting to naive datetimes so that they are not adjusted to UTC
            initial_booking_end = self.current_booking_end + dt.timedelta(hours=1)
            self.initial['new_end_date'] = dt.datetime.strftime(
                timezone.make_naive(initial_booking_end),
                '%d/%m/%Y'
            )
            self.initial['new_end_time'] = dt.datetime.strftime(
                timezone.make_naive(initial_booking_end),
                '%H:%M'
            )
        # Crispy forms
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Booking Start',
                Div(
                    Div(
                        HTML("<p><strong>Date:</strong></p>"),
                        css_class='col-xs-2',
                    ),
                    Div(
                        HTML("<p>{{ booking.schedule_start|date:'d/m/Y' }}</p>"),
                        css_class='col-xs-5',
                    ),
                    Div(
                        HTML("<p><strong>Time:</strong></p>"),
                        css_class='col-xs-2',
                    ),
                    Div(
                        HTML("<p>{{ booking.schedule_start|date:'H:i' }}</p>"),
                        css_class='col-xs-3',
                    ),
                    css_class='row',
                )
            ),
            Fieldset(
                'Booking End',
                Div(
                    Div(
                        HTML("<p><strong>Date:</strong></p>"),
                        css_class='col-xs-2',
                    ),
                    Div(
                        HTML("<p>{{ booking.schedule_end|date:'d/m/Y' }}</p>"),
                        css_class='col-xs-5',
                    ),
                    Div(
                        HTML("<p><strong>Time:</strong></p>"),
                        css_class='col-xs-2',
                    ),
                    Div(
                        HTML("<p>{{ booking.schedule_end|date:'H:i' }}</p>"),
                        css_class='col-xs-3',
                    ),
                    css_class='row',
                )
            ),
            Fieldset(
                'New Booking End',
                Div(
                    Div(
                        Field('new_end_date', css_class='datepicker', placeholder='Date'),
                        css_class='col-sm-8',
                    ),
                    Div(
                        'new_end_time',
                        css_class='col-sm-4',
                    ),
                    css_class='row',
                )
            ),
        )
