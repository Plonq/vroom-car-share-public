#
#   Author(s): Huon Imberger
#   Description: Defines database models for core functionality
#

from django.db import models
from django.utils import timezone

from decimal import Decimal
from math import ceil

from accounts.models import User


class VehicleType(models.Model):
    """
    Types and costs of vehicles
    """
    description = models.CharField(max_length=30)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)
    daily_rate = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return "{0} - Hourly: ${1:.2f} Daily: ${2:.2f}".format(
            self.description,
            float(self.hourly_rate),
            float(self.daily_rate)
        )


class Pod(models.Model):
    """
    A designated/reserved parking spot for Vroom vehicles
    """
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    description = models.CharField(max_length=200)

    def coordinates(self):
        return "{0},{1}".format(self.latitude, self.longitude)

    def __str__(self):
        string = "{0}".format(self.description)
        if hasattr(self, 'vehicle'):
            string += " ({0})".format(self.vehicle.name)
        return string


class Vehicle(models.Model):
    """
    A Vroom vehicle
    """
    type = models.ForeignKey(VehicleType, related_name='type')
    pod = models.OneToOneField(Pod, null=True, blank=True)
    name = models.CharField(max_length=30, unique=True)
    make = models.CharField(max_length=30)
    model = models.CharField(max_length=30)
    year = models.PositiveSmallIntegerField()
    active = models.BooleanField(default=True)
    registration = models.CharField(max_length=6, unique=True)

    def is_active(self):
        return self.active

    def is_available(self):
        """
        Is the vehicle available for booking right now?
        """
        current_bookings = self.booking_set.all()
        active_bookings = [b for b in current_bookings if b.is_active()]
        if not active_bookings:
            return True
        else:
            return False

    def is_available_at(self, datetime):
        """
        Checks if the vehicle is available at the time specified
        :param datetime: when to check
        :return: Boolean
        """
        for booking in self.booking_set.all():
            if booking.schedule_start <= datetime < booking.schedule_end and not booking.is_cancelled():
                return False
        return True

    def get_booking_at(self, datetime):
        """
        Returns the booking for this vehicle at the specified time, or None if it is not booked
        """
        for booking in self.booking_set.all():
            if booking.schedule_start <= datetime < booking.schedule_end and not booking.is_cancelled():
                return booking
        return None

    def __str__(self):
        # E.g. 'Jackie - 2014 Toyota Corolla'
        return "{0} - {1} {2} {3}".format(
            self.name,
            self.year,
            self.make,
            self.model,
        )


class Booking(models.Model):
    """
    Details about particular booking by a user for a vehicle
    """
    user = models.ForeignKey(User)
    vehicle = models.ForeignKey(Vehicle)
    schedule_start = models.DateTimeField(verbose_name='Start time')
    schedule_end = models.DateTimeField(verbose_name='End time')
    cancelled = models.DateTimeField(null=True, blank=True)

    MAX_LENGTH_DAYS = 90

    def calculate_cost(self):
        """
        Calculates total cost of booking, taking into account hourly rate and daily rate of the vehicle.
        As soon as hourly cost reaches the daily rate, the daily rate is used instead.
        E.g. if hourly rate is $10 and daily rate $100, a booking lasting from 10 hours up to 24 hours will cost $100.
        :return: float
        """
        booking_days, booking_hours = self.calculate_daily_hourly_billable_counts()
        day_cost = booking_days * Decimal(self.vehicle.type.daily_rate)
        hour_cost = booking_hours * Decimal(self.vehicle.type.hourly_rate)
        if hour_cost > self.vehicle.type.daily_rate:
            hour_cost = self.vehicle.type.daily_rate
        return float(day_cost + hour_cost)

    def calculate_daily_hourly_billable_counts(self):
        """
        Calculates the number of days and hours as they are billable.
        E.g. if hourly rate is $10 and daily rate $100, a booking lasting 5 hours would be days = 0 hours = 5
        E.g. if hourly rate is $10 and daily rate $100, a booking lasting 13 hours would be days = 1 hours = 0
        E.g. if hourly rate is $10 and daily rate $100, a booking lasting 26 hours would be days = 1 hours = 2
        E.g. if hourly rate is $10 and daily rate $100, a booking lasting 40 hours would be days = 2 hours = 0
        :return: tuple
        """
        booking_length = self.schedule_end - self.schedule_start
        booking_length_hours_total = booking_length.days * 24 + booking_length.seconds / 60 / 60
        booking_days = int(booking_length_hours_total / 24)
        booking_hours = ceil(booking_length_hours_total % 24)
        if booking_hours * Decimal(self.vehicle.type.hourly_rate) >= self.vehicle.type.daily_rate:
            booking_days += 1
            booking_hours = 0
        return booking_days, booking_hours

    def is_active(self):
        return (
            self.schedule_start < (timezone.now()) < self.schedule_end and
            not self.is_cancelled()
        )

    def is_cancelled(self):
        return self.cancelled is not None

    def is_complete(self):
        return self.schedule_end < timezone.now()

    def is_confirmed(self):
        return self.schedule_start > timezone.now()

    def is_paid(self):
        return hasattr(self, 'invoice')

    def get_status(self):
        """
        Returns a string indicating the status
        """
        if self.cancelled:
            return "Cancelled"
        elif self.is_active():
            s = "Active"
            if self.is_paid():
                return "{0} - Paid".format(s)
            else:
                return "{0} - Unpaid".format(s)
        elif self.is_complete():
            s = "Complete"
            if self.is_paid():
                return "{0} - Paid".format(s)
            else:
                return "{0} - Unpaid".format(s)
        elif self.is_confirmed():
            s = "Confirmed"
            if self.is_paid():
                return "{0} - Paid".format(s)
            else:
                return "{0} - Unpaid".format(s)
        else:
            return "Unknown - contact staff"

    def __str__(self):
        return "{0} - {1}".format(self.id, self.get_status())


class Invoice(models.Model):
    """
    Invoice for a single booking
    """
    booking = models.OneToOneField(Booking, related_name='invoice')
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return '{0} - Booking {1}'.format(self.id, self.booking.id)
