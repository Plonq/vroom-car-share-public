#
#   Author(s): Huon Imberger
#   Description: Custom account-related managers for managing sets of objects
#

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    User manager that provides methods for creating users and superusers, setting password's properly
    """
    def create_user(self, email, first_name, last_name, date_of_birth, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, date_of_birth, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
