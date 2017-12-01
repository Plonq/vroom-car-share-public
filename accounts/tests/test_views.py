from django.test import TestCase, override_settings
from django.shortcuts import reverse
from django.core import mail

import datetime as dt

from ..models import User


# Tests do not work with whitenoise static file storage, so we use the default storage for tests
STATICFILES_STORAGE_FOR_TESTS = 'django.contrib.staticfiles.storage.StaticFilesStorage'


@override_settings(STATICFILES_STORAGE=STATICFILES_STORAGE_FOR_TESTS)
class AccountsPageTextViewTests(TestCase):
    def test_register_page(self):
        """
        Register page contains expected text
        """
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Register")

    def test_login_page(self):
        """
        Login page contains expected text
        """
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login")


@override_settings(STATICFILES_STORAGE=STATICFILES_STORAGE_FOR_TESTS)
class AccountsRegisterViewTests(TestCase):
    fixtures = ['email_templates']

    def test_valid_registration(self):
        """
        Registration with valid details is successful and sends email to user
        """

        user_data = {
            'email': 'test123@test.com',
            'first_name': 'Test',
            'last_name': 'Client',
            'date_of_birth': '01/01/1950',
            'password1': ';alskdjf',
            'password2': ';alskdjf',
        }
        address_data = {
            'address_line_1': '123 Fake St',
            'city': 'Melbourne',
            'state': 'VIC',
            'postcode': '3001',
        }
        credit_card_data = {
            'card_number': '6823119834248189', # Valid CC number
            'expiry_month': '12',
            'expiry_year': str(dt.date.today().year), # December of current year should always be valid
        }
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        # User form
        response = self.client.post(reverse('register'), user_data)
        self.assertTrue('user_id' in self.client.session)
        user_id = self.client.session['user_id']
        self.assertRedirects(response, reverse('register_address'))
        # Address form
        response = self.client.post(reverse('register_address'), address_data)
        self.assertTrue('address_id' in self.client.session)
        self.assertRedirects(response, reverse('register_credit_card'))
        # Credit card form
        response = self.client.post(reverse('register_credit_card'), credit_card_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse('user_id' in self.client.session)
        self.assertFalse('address_id' in self.client.session)
        # Email
        user = User.objects.get(id=user_id)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Thank you for joining Vroom!')
        self.assertTrue('Hi {0}!'.format(user.first_name) in mail.outbox[0].body)
        self.assertTrue('Thanks for choosing Vroom as your preferred transport provider.' in mail.outbox[0].body)
        self.assertTrue('Activate Account' in mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].from_email, 'Vroom Car Share <admin@vroomcs.org>')
        self.assertEqual(mail.outbox[0].to, [user.email])
        # Account activation
        self.assertFalse(user.is_active)
        # Note - can't figure out a way to grab activation link from email. Maybe regex, but CBF right now
