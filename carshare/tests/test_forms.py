from django.test import TestCase
from ..forms import *

from django.utils import timezone
from datetime import timedelta


# Handy dates based on current time
two_days_ago = timezone.now() - timedelta(days=2)
yesterday = timezone.now() - timedelta(days=1)
tomorrow = timezone.now() + timedelta(days=1)
two_days_from_now = timezone.now() + timedelta(days=2)
date_format = '%d/%m/%Y'
time_format = '%H:00' # Form only accepts times on the hour

class CarshareBookingFormTests(TestCase):
    def test_valid_form_data(self):
        """
        Booking form with end time after start time is valid
        """
        form_data = {
            'booking_start_date': tomorrow.strftime(date_format),
            'booking_start_time': tomorrow.strftime(time_format),
            'booking_end_date': two_days_from_now.strftime(date_format),
            'booking_end_time': two_days_from_now.strftime(time_format),
        }
        booking_form = BookingForm(data=form_data)
        self.assertTrue(booking_form.is_valid())

    def test_end_before_start(self):
        """
        Booking form with end time before start time is invalid
        """
        form_data = {
            'booking_start_date': two_days_from_now.strftime(date_format),
            'booking_start_time': two_days_from_now.strftime(time_format),
            'booking_end_date': tomorrow.strftime(date_format),
            'booking_end_time': tomorrow.strftime(time_format),
        }
        booking_form = BookingForm(data=form_data)
        self.assertFalse(booking_form.is_valid())

    def test_start_time_in_past(self):
        """
        Booking form with start time in the past is invalid
        """
        form_data = {
            'booking_start_date': yesterday.strftime(date_format),
            'booking_start_time': yesterday.strftime(time_format),
            'booking_end_date': tomorrow.strftime(date_format),
            'booking_end_time': tomorrow.strftime(time_format),
        }
        booking_form = BookingForm(data=form_data)
        self.assertFalse(booking_form.is_valid())

    def test_identical_start_and_end(self):
        """
        Booking form with start and end times identical is invalid
        """
        form_data = {
            'booking_start_date': tomorrow.strftime(date_format),
            'booking_start_time': tomorrow.strftime(time_format),
            'booking_end_date': tomorrow.strftime(date_format),
            'booking_end_time': tomorrow.strftime(time_format),
        }
        booking_form = BookingForm(data=form_data)
        self.assertFalse(booking_form.is_valid())