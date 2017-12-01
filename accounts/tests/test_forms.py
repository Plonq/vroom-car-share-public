from django.test import TestCase
from ..forms import *


# Set up default, valid form data
form_data = {
    'email': 'test@test.com',
    'first_name': 'Test',
    'last_name': 'Account',
    'password1': ';alskdjf',
    'password2': ';alskdjf',
    'date_of_birth': '1950-01-01',
    'address_line_1': 'Suite 13',
    'address_line_2': '123 Fake St',
    'city': 'MelbourneTown',
    'state': 'VIC',
    'postcode': '3000',
    'card_number': '6823119834248189', # Valid CC number
    'expiry_month': '12',
    'expiry_year': str(date.today().year), # December of current year should always be valid
}


class AccountsGeneralFormTests(TestCase):
    def test_valid_form_data(self):
        """
        Valid forms successfully validate
        """
        user_form = UserCreationSelfForm(data=form_data)
        address_form = AddressForm(data=form_data)
        credit_card_form = CreditCardForm(data=form_data)
        self.assertTrue(user_form.is_valid())
        self.assertTrue(address_form.is_valid())
        self.assertTrue(credit_card_form.is_valid())

    def test_missing_form_data(self):
        """
        Valid forms successfully validate
        """
        user_form = UserCreationSelfForm(data={})
        address_form = AddressForm(data={})
        credit_card_form = CreditCardForm(data={})
        self.assertFalse(user_form.is_valid())
        self.assertFalse(address_form.is_valid())
        self.assertFalse(credit_card_form.is_valid())


class AccountsUserCreationFormTests(TestCase):
    def test_email_without_tld(self):
        """
        Email without TLD correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['email'] = 'invalidemail@bad'
        form = UserCreationSelfForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_email_with_bad_chars(self):
        """
        Email with invalid characters correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['email'] = '$&%()#@test.com'
        form = UserCreationSelfForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_email_without_at_symbol(self):
        """
        Email without @ symbol correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['email'] = 'emailtest.com'
        form = UserCreationSelfForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_mismatching_passwords(self):
        """
        Mismatching passwords correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['password1'] = 'dfwew323r23g'
        invalid_form_data['password2'] = 'fgsdfhgraqt4e5'
        form = UserCreationSelfForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_date_of_birth_less_than_18_years_ago(self):
        """
        Date of birth less than 18 years ago correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        seventeen_years_and_364_days_in_the_past = (date.today() - timedelta(days=365*18-1)).isoformat()
        invalid_form_data['date_of_birth'] = seventeen_years_and_364_days_in_the_past
        form = UserCreationSelfForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())


class AccountsAddressFormTests(TestCase):
    def test_alpha_postcode(self):
        """
        Alpha postcode correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['postcode'] = 'a200'
        form = AddressForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_three_digit_postcode(self):
        """
        Three digit postcode correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['postcode'] = '333'
        form = AddressForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())


class AccountsCreditCardFormTests(TestCase):
    def test_invalid_credit_card_number(self):
        """
        Invalid credit card number correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['card_number'] = '8102966371298364' # Looks okay but invalid
        form = CreditCardForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_alpha_expiry_month(self):
        """
        Alpha expiry month correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['expiry_month'] = 'a1'
        form = CreditCardForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_expiry_month_13(self):
        """
        Expiry month of 13 correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['expiry_month'] = '13'
        form = CreditCardForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_expiry_month_0(self):
        """
        Expiry month of 0 correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['expiry_month'] = '0'
        form = CreditCardForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_alpha_expiry_year(self):
        """
        Alpha expiry year correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['expiry_year'] = '202a'
        form = CreditCardForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_expiry_year_in_past(self):
        """
        Expiry year of last year correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['expiry_year'] = str(date.today().year - 1)
        form = CreditCardForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_expiry_year_exactly_29_in_future(self):
        """
        Expiry year exactly 29 years in future correctly identified as valid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['expiry_year'] = str(date.today().year + 29)
        form = CreditCardForm(data=invalid_form_data)
        self.assertTrue(form.is_valid())

    def test_expiry_year_over_30_in_future(self):
        """
        Expiry year of 51 years in future correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        invalid_form_data['expiry_year'] = str(date.today().year + 31)
        form = CreditCardForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_expiry_date_in_past(self):
        """
        Expiry date of last month correctly identified as invalid
        """
        invalid_form_data = form_data.copy()
        last_month = date.today().replace(day=1) - timedelta(days=1)
        invalid_form_data['expiry_month'] = str(last_month.month)
        invalid_form_data['expiry_year'] = str(last_month.year)
        form = CreditCardForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())
