#
#   Author(s): Huon Imberger, Shaun O'Malley
#   Description: Defines account-related forms, including validation rules
#

from django.contrib.auth import forms as auth_forms
from django.contrib.auth.password_validation import validate_password, password_validators_help_text_html
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils import timezone

from datetime import date, timedelta

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from datetimewidget.widgets import DateWidget

from .models import User, Address, CreditCard
from .util import is_credit_card_valid, is_digits


class UserCreationForm(forms.ModelForm):
    """
    Base user creation form. Used for admin
    """
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, help_text=password_validators_help_text_html)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'date_of_birth')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        # Validate password using default validators defined in settings
        validate_password(password1)
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserCreationSelfForm(UserCreationForm):
    """
    Form for the end user to create an account
    """
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'date_of_birth')
        today = timezone.localdate()
        dateTimeOptions = {
            'format': 'dd/mm/yyyy',
            'endDate': date(today.year-18, today.month, today.day).isoformat(),
            'startDate': date(today.year-100, today.month, today.day).isoformat(),
            'startView': 4,
        }
        widgets = {
            'date_of_birth': DateWidget(options=dateTimeOptions, bootstrap_version=3)
        }

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        # Validate password using default validators defined in settings
        validate_password(password1)
        return password2

    def clean_date_of_birth(self):
        # Check that DOB indicates user is over 18
        dob = self.cleaned_data.get('date_of_birth')
        today = timezone.localdate()
        eighteen_years_ago = date(today.year-18, today.month, today.day)
        hundred_twenty_years_ago = date(today.year-100, today.month, today.day)
        if dob > eighteen_years_ago:
            raise forms.ValidationError('You must be 18 years old to sign up')
        if dob < hundred_twenty_years_ago:
            raise forms.ValidationError('Are you sure you should be driving at that age?')
        return dob

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationSelfForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        super(UserCreationSelfForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('email', autofocus='autofocus'),
            Field('first_name'),
            Field('last_name'),
            Field('date_of_birth'),
            Field('password1'),
            Field('password2'),
        )


class UserChangeForm(forms.ModelForm):
    """
    A form for updating users. This has all the data
    needed for django-admin
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'password',
            'date_of_birth',
            'is_active',
            'is_staff',
            'is_superuser',
          )

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserChangeSelfForm(forms.ModelForm):
    """
    A form for regular uses to edit their own details.
    """
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
          )
        dateTimeOptions = {
            'format': 'dd/mm/yyyy',
            'endDate': timezone.localtime().date().isoformat(),
            'startView': 4,
        }
        widgets = {
            'date_of_birth': DateWidget(options=dateTimeOptions, bootstrap_version=3)
        }

    def __init__(self, *args, **kwargs):
        super(UserChangeSelfForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class EmailChangeForm(forms.ModelForm):
    """
    A form for changing one's email address
    """
    class Meta:
        model = User
        fields = {
            'requested_email',
        }

    def clean_requested_email(self):
        requested_email = self.cleaned_data.get('requested_email')
        if User.objects.filter(email=requested_email).exists():
            raise forms.ValidationError('That email is already taken')
        return requested_email

    def __init__(self, *args, **kwargs):
        super(EmailChangeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class PasswordResetForm(auth_forms.PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class SetPasswordForm(auth_forms.SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(SetPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class AuthenticationForm(auth_forms.AuthenticationForm):
    username = forms.EmailField(max_length=255)

    def __init__(self, *args, **kwargs):
        super(AuthenticationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


# Auth ModelForms with crispy-forms
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["address_line_1", "address_line_2", "city", "state", "postcode"]

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('address_line_1', autofocus='autofocus'),
            Field('address_line_2'),
            Field('city'),
            Field('state'),
            Field('postcode'),
        )

    def clean_postcode(self):
        # Check postcode is exactly 4 digits
        postcode = self.cleaned_data['postcode']
        if len(postcode) != 4 or not is_digits(postcode):
            raise forms.ValidationError('Must be exactly 4 digits')
        return postcode


class CreditCardForm(forms.ModelForm):
    class Meta:
        model = CreditCard
        fields = ["card_number", "expiry_month", "expiry_year"]

    def clean_card_number(self):
        # Checks number is valid credit card number
        card_number = self.cleaned_data.get('card_number')
        try:
            int(card_number)
            if not is_credit_card_valid(card_number=card_number):
                raise forms.ValidationError('Must be a valid credit card number')
        except ValueError:
            raise forms.ValidationError('Credit card must be numeric')
        return card_number

    def clean_expiry_month(self):
        # Check number is valid month
        expiry_month = self.cleaned_data.get('expiry_month')
        if not (is_digits(expiry_month) and 1 <= int(expiry_month) <= 12):
            raise forms.ValidationError('Must be between 1 and 12 inclusive')
        return expiry_month

    def clean_expiry_year(self):
        # Check number is valid year and that it's at least the current year
        # and no later than 50 years in the future
        expiry_year = self.cleaned_data.get('expiry_year')
        current_year = date.today().year
        if not (is_digits(expiry_year) and current_year <= int(expiry_year) <= (current_year + 50)):
            raise forms.ValidationError('Must not be in the past or later than {0}'.format(current_year + 50))
        return expiry_year

    def clean(self):
        # Check that expiry date is not in the past
        cleaned_data = super(CreditCardForm, self).clean()
        expiry_month = cleaned_data.get('expiry_month')
        expiry_year = cleaned_data.get('expiry_year')
        # Prevents TypeError on int() if data missing
        if expiry_month and expiry_year:
            # Get date objects for first day of month so we can
            # compare only month and year
            t = date.today()
            first_of_month = date(day=1, month=t.month, year=t.year)
            expiry_date = date(day=1, month=int(expiry_month), year=int(expiry_year))
            if expiry_date < first_of_month:
                raise forms.ValidationError('Expiry date must not be in the past')
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super(CreditCardForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('card_number', autofocus='autofocus'),
            Field('expiry_month'),
            Field('expiry_year'),
        )
