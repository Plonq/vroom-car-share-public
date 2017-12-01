#
#   Author(s): Huon Imberger
#   Description: Defines database models for account-related data
#

from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.conf import settings

from .managers import UserManager
from emails.utils import send_templated_email


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model to use email instead of username
    """
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField()

    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Temporary holding spot when user requests changing their email address
    requested_email = models.EmailField(verbose_name='email address', max_length=255, null=True, blank=True)

    # Custom user manager
    objects = UserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'date_of_birth'] # Only used for createsuperuser command

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def send_email(self, template_name, context, from_email=settings.DEFAULT_FROM_EMAIL, attachment_filename=None, attachment_data=None):
        """
        Sends an email to this User given the template_name (not the template filename)
        """
        send_templated_email(
            template_name=template_name,
            context=context,
            recipient_list=[self.email],
            from_email=from_email,
            attachment_filename=attachment_filename,
            attachment_data=attachment_data,
        )

    def has_perm(self, perm, obj=None):
        """
        Does the user have a specific permission?
        """
        has = super(User, self).has_perm(perm, obj)
        return has

    def has_module_perms(self, app_label):
        """
        Does the user have permissions to view the app `app_label`?
        """
        has = super(User, self).has_module_perms(app_label)
        return has

    def __str__(self):
        return self.email

    def get_current_booking(self):
        """
        Gets this user's current booking
        """
        current_bookings = self.booking_set.all()
        active_bookings = [b for b in current_bookings if b.is_active()]
        # Should only ever be one active booking (enforced via validation when creating a booking),
        # but it's technically possible so we always return the first one.
        if active_bookings:
            return active_bookings[0]
        else:
            return None


class Address(models.Model):
    """
    Stores an address for a user
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='address')

    STATES = (
        ('VIC', 'Victoria'),
        ('NSW', 'New South Wales'),
        ('WA', 'Western Australia'),
        ('TAS', 'Tasmania'),
        ('QLD', 'Queensland'),
        ('SA', 'South Australia'),
    )
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=30)
    state = models.CharField(max_length=3, choices=STATES)
    postcode = models.CharField(max_length=4)

    def __str__(self):
        return "{0}, {1}, {2} {3}".format(self.address_line_1, self.city, self.state, self.postcode)


class CreditCard(models.Model):
    """
    Stores credit card information for a user
    """
    from django.utils import timezone
    MONTHS = [
        ('01', '01'),
        ('02', '02'),
        ('03', '03'),
        ('04', '04'),
        ('05', '05'),
        ('06', '06'),
        ('07', '07'),
        ('08', '08'),
        ('09', '09'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
    ]
    # Dynamically create year list. 30 years starting from today
    today = timezone.localdate()
    YEARS = [(str(year), str(year)) for year in range(today.year, today.year+30)]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='credit_card')
    card_number = models.CharField(max_length=16)
    expiry_month = models.CharField(max_length=2, choices=MONTHS)
    expiry_year = models.CharField(max_length=4, choices=YEARS)

    def __str__(self):
        return "XXXX XXXX XXXX {0}".format(self.card_number[-4:])
