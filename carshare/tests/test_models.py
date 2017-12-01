from django.test import TestCase

from ..models import *
from datetime import datetime, timedelta
from django.utils import timezone


# Create datetime objects relative to now, in order to properly test 'now'-based methods
two_days_ago = timezone.now() - timedelta(days=2)
yesterday = timezone.now() - timedelta(days=1)
tomorrow = timezone.now() + timedelta(days=1)
two_days_from_now = timezone.now() + timedelta(days=2)


class CarshareBookingModelTests(TestCase):
    def setUp(self):
        vt = VehicleType.objects.create(description='Premium', hourly_rate=12.50, daily_rate=80.00)
        p1 = Pod.objects.create(latitude='-39.34523453', longitude='139.53524344', description='Pod 1')
        self.v1 = Vehicle.objects.create(pod=p1, type=vt, name='Vehicle1', make='Toyota', model='Yaris', year=2012, registration='AAA222')
        self.u = User.objects.create(email='test@test.com', first_name='John', last_name='Doe', date_of_birth='2017-01-01')

    def test_active_paid_booking(self):
        """
        Active booking returns expected results
        """
        active_booking = Booking(schedule_start=yesterday, schedule_end=tomorrow, vehicle=self.v1, user=self.u)
        active_booking.invoice = Invoice(booking=active_booking, amount=active_booking.calculate_cost(), date=timezone.now())
        self.assertTrue(active_booking.is_active())
        self.assertFalse(active_booking.is_cancelled())
        self.assertFalse(active_booking.is_complete())
        self.assertEqual(active_booking.get_status(), "Active - Paid")

    def test_active_unpaid_booking(self):
        """
        Active booking returns expected results
        """
        active_booking = Booking(schedule_start=yesterday, schedule_end=tomorrow)
        self.assertTrue(active_booking.is_active())
        self.assertFalse(active_booking.is_cancelled())
        self.assertFalse(active_booking.is_complete())
        self.assertEqual(active_booking.get_status(), "Active - Unpaid")

    def test_booking_within_an_hour_of_now(self):
        """
        Booking booked for within one hour of now is active
        """
        now = timezone.make_naive(timezone.now())
        nearest_hour_from_now = timezone.make_aware(now + (datetime.min - now) % timedelta(hours=1))
        active_booking = Booking(schedule_start=nearest_hour_from_now, schedule_end=tomorrow)
        self.assertFalse(active_booking.is_active())
        self.assertFalse(active_booking.is_cancelled())
        self.assertFalse(active_booking.is_complete())

    def test_future_paid_booking(self):
        """
        Future booking returns expected results
        """
        future_booking = Booking(schedule_start=tomorrow, schedule_end=two_days_from_now, vehicle=self.v1, user=self.u)
        future_booking.invoice = Invoice(booking=future_booking, amount=future_booking.calculate_cost(), date=timezone.now())
        self.assertFalse(future_booking.is_active())
        self.assertFalse(future_booking.is_cancelled())
        self.assertFalse(future_booking.is_complete())
        self.assertEqual(future_booking.get_status(), "Confirmed - Paid")

    def test_future_unpaid_booking(self):
        """
        Future booking returns expected results
        """
        future_booking = Booking(schedule_start=tomorrow, schedule_end=two_days_from_now)
        self.assertFalse(future_booking.is_active())
        self.assertFalse(future_booking.is_cancelled())
        self.assertFalse(future_booking.is_complete())
        self.assertEqual(future_booking.get_status(), "Confirmed - Unpaid")

    def test_complete_unpaid_booking(self):
        """
        Ended booking returns expected results
        """
        ended_booking = Booking(schedule_start=two_days_ago, schedule_end=yesterday)
        self.assertFalse(ended_booking.is_active())
        self.assertFalse(ended_booking.is_cancelled())
        self.assertTrue(ended_booking.is_complete())
        self.assertEqual(ended_booking.get_status(), "Complete - Unpaid")

    def test_complete_paid_booking(self):
        """
        Ended booking returns expected results
        """
        ended_booking = Booking(schedule_start=two_days_ago, schedule_end=yesterday, vehicle=self.v1, user=self.u)
        ended_booking.invoice = Invoice(booking=ended_booking, amount=ended_booking.calculate_cost(), date=timezone.now())
        self.assertFalse(ended_booking.is_active())
        self.assertFalse(ended_booking.is_cancelled())
        self.assertTrue(ended_booking.is_complete())
        self.assertEqual(ended_booking.get_status(), "Complete - Paid")

    def test_cancelled_booking(self):
        """
        Cancelled booking returns expected results
        """
        cancelled_booking = Booking(schedule_start=yesterday, schedule_end=tomorrow, cancelled=datetime.now())
        self.assertFalse(cancelled_booking.is_active())
        self.assertTrue(cancelled_booking.is_cancelled())
        self.assertFalse(cancelled_booking.is_complete())
        self.assertEqual(cancelled_booking.get_status(), "Cancelled")

    def test_booking_cost_two_days_one_hour(self):
        """
        Booking cost calculated correctly for a mix of daily and hourly rate
        """
        u = User.objects.get(email='test@test.com')
        v = Vehicle.objects.get(name='Vehicle1')
        fixed_start = timezone.make_aware(datetime.strptime('2017-09-01 12:00:00', '%Y-%m-%d %H:%M:%S'))
        fixed_end = timezone.make_aware(datetime.strptime('2017-09-03 13:00:00', '%Y-%m-%d %H:%M:%S'))
        b = Booking.objects.create(user=u, vehicle=v, schedule_start=fixed_start, schedule_end=fixed_end)
        self.assertEqual(b.calculate_cost(), 172.5)

    def test_booking_cost_two_days_ten_hours(self):
        """
        Booking cost calculated correctly for a mix of daily and hourly rate
        """
        u = User.objects.get(email='test@test.com')
        v = Vehicle.objects.get(name='Vehicle1')
        fixed_start = timezone.make_aware(datetime.strptime('2017-09-01 12:00:00', '%Y-%m-%d %H:%M:%S'))
        fixed_end = timezone.make_aware(datetime.strptime('2017-09-03 22:00:00', '%Y-%m-%d %H:%M:%S'))
        b = Booking.objects.create(user=u, vehicle=v, schedule_start=fixed_start, schedule_end=fixed_end)
        self.assertEqual(b.calculate_cost(), 240.0)

    def test_booking_cost_two_days_zero_hours(self):
        """
        Booking cost calculated correctly for a round number of days
        """
        u = User.objects.get(email='test@test.com')
        v = Vehicle.objects.get(name='Vehicle1')
        fixed_start = timezone.make_aware(datetime.strptime('2017-09-01 12:00:00', '%Y-%m-%d %H:%M:%S'))
        fixed_end = timezone.make_aware(datetime.strptime('2017-09-03 12:00:00', '%Y-%m-%d %H:%M:%S'))
        b = Booking.objects.create(user=u, vehicle=v, schedule_start=fixed_start, schedule_end=fixed_end)
        self.assertEqual(b.calculate_cost(), 160.0)

    def test_booking_cost_zero_days_5_hours(self):
        """
        Booking cost calculated correctly for less than a day
        """
        u = User.objects.get(email='test@test.com')
        v = Vehicle.objects.get(name='Vehicle1')
        fixed_start = timezone.make_aware(datetime.strptime('2017-09-01 12:00:00', '%Y-%m-%d %H:%M:%S'))
        fixed_end = timezone.make_aware(datetime.strptime('2017-09-01 17:00:00', '%Y-%m-%d %H:%M:%S'))
        b = Booking.objects.create(user=u, vehicle=v, schedule_start=fixed_start, schedule_end=fixed_end)
        self.assertEqual(b.calculate_cost(), 62.5)


class CarshareVehicleModelTests(TestCase):
    def setUp(self):
        vt = VehicleType.objects.create(description='Premium', hourly_rate='12.50', daily_rate='80.00')
        p1 = Pod.objects.create(latitude='-39.34523453', longitude='139.53524344', description='Pod 1')
        p2 = Pod.objects.create(latitude='60.34523453', longitude='109.53524344', description='Pod 2')
        v1 = Vehicle.objects.create(pod=p1, type=vt, name='Vehicle1', make='Toyota', model='Yaris', year=2012, registration='AAA111')
        v2 = Vehicle.objects.create(pod=p2, type=vt, name='Vehicle2', make='Mazda', model='2', year=2014, registration='AAA112')
        u = User.objects.create(email='test@test.com', first_name='John', last_name='Doe', date_of_birth='2017-01-01')

        # Booking for Vehicle1 that should make Vehicle1 unavailable
        Booking.objects.create(user=u, vehicle=v1, schedule_start=yesterday, schedule_end=tomorrow)

        # Bookings for Vehicle2 but Vehicle2 should still be available to book
        Booking.objects.create(user=u, vehicle=v2, schedule_start=two_days_ago, schedule_end=yesterday)
        Booking.objects.create(user=u, vehicle=v2, schedule_start=yesterday, schedule_end=tomorrow, cancelled=timezone.now())
        Booking.objects.create(user=u, vehicle=v2, schedule_start=tomorrow, schedule_end=two_days_from_now)

    def test_available_vehicle(self):
        """
        Available vehicle correctly identified as available
        """
        v = Vehicle.objects.get(name='Vehicle2')
        self.assertTrue(v.is_available())

    def test_unavailable_vehicle(self):
        """
        Unavailable vehicle correctly identified as unavailable
        """
        v = Vehicle.objects.get(name='Vehicle1')
        self.assertFalse(v.is_available())
