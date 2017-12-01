from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

import datetime as dt

from ..models import Booking, User, Vehicle, Pod, VehicleType, Invoice


# Tests do not work with whitenoise static file storage, so we use the default storage for tests
STATICFILES_STORAGE_FOR_TESTS = 'django.contrib.staticfiles.storage.StaticFilesStorage'


@override_settings(STATICFILES_STORAGE=STATICFILES_STORAGE_FOR_TESTS)
class CarshareIndexViewTests(TestCase):

    def test_homepage_returns_200(self):
        """
        Homepage correctly returns status code 200
        """
        response = self.client.get(reverse('carshare:index'))
        self.assertEqual(response.status_code, 200)

    def test_homepage_contains_text_home(self):
        """
        Homepage correctly contains "Home"
        """
        response = self.client.get(reverse('carshare:index'))
        self.assertContains(response, 'Home')


@override_settings(STATICFILES_STORAGE=STATICFILES_STORAGE_FOR_TESTS)
class CarshareContactUsViewTests(TestCase):

    def test_contact_us_form(self):
        """
        Contact Us form correctly sends email to staff
        """
        form = {
            'contact_name': 'Contact Name',
            'contact_email': 'contactemail@test.com',
            'message': 'This is the message.',
        }
        response = self.client.post(reverse('carshare:contact_us'), data=form)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'New Contact Us from Contact Name')
        self.assertEqual(mail.outbox[0].body, 'This is the message.')
        self.assertEqual(mail.outbox[0].from_email, 'admin@vroomcs.org')
        self.assertEqual(mail.outbox[0].reply_to, ['contactemail@test.com'])
        self.assertEqual(mail.outbox[0].to, ['admin@vroomcs.org'])


@override_settings(STATICFILES_STORAGE=STATICFILES_STORAGE_FOR_TESTS)
class CarshareBookingViewTests(TestCase):
    fixtures = ['email_templates']

    def setUp(self):
        # Create user to log in as
        User.objects.create_user(email='user@test.com', password='bigbadtestuser', first_name='Test', last_name='User', date_of_birth=dt.date(1980, 1, 1))

        # Set up some sample data, including a few bookings
        vt = VehicleType.objects.create(description='Premium', hourly_rate=12.50, daily_rate=80.00)
        p1 = Pod.objects.create(latitude='-39.34523453', longitude='139.53524344', description='Pod 1')
        p2 = Pod.objects.create(latitude='-38.34523453', longitude='138.53524344', description='Pod 2')
        self.v1 = Vehicle.objects.create(pod=p1, type=vt, name='Vehicle1', make='Toyota', model='Yaris', year=2012,
                                    registration='AAA222')
        self.v2 = Vehicle.objects.create(pod=p2, type=vt, name='Vehicle2', make='Toyota', model='Yaris', year=2011,
                                    registration='AAA223')
        u1 = User.objects.create(email='test1@test.com', first_name='John', last_name='Doe', date_of_birth='1980-01-01')
        u2 = User.objects.create(email='test2@test.com', first_name='Jane', last_name='Doly', date_of_birth='1988-01-01')
        # 12 AM - 1 AM
        self.b1 = Booking.objects.create(user=u1, vehicle=self.v1,
                               schedule_start=timezone.make_aware(dt.datetime(year=2999, month=1, day=1, hour=0)),
                               schedule_end=timezone.make_aware(dt.datetime(year=2999, month=1, day=1, hour=1)))
        # 3 AM - 6 AM
        self.b2 = Booking.objects.create(user=u1, vehicle=self.v1,
                               schedule_start=timezone.make_aware(dt.datetime(year=2999, month=1, day=1, hour=3)),
                               schedule_end=timezone.make_aware(dt.datetime(year=2999, month=1, day=1, hour=6)))

    def test_valid_booking(self):
        """
        Booking for a time period that is not already booked by the user or the vehicle is successfully created
        """
        form = {
            'booking_start_date': '01/01/3000',
            'booking_start_time': '00:00',
            'booking_end_date': '01/01/3000',
            'booking_end_time': '01:00',
        }
        self.client.login(email='user@test.com', password='bigbadtestuser')
        # Construct URL with fake data because it's only there to provide initial form values
        kwargs = {
            'vehicle_id': self.v1.id,
            'year': '2000',
            'month': '1',
            'day': '1',
            'hour': '0',
        }
        get_response = self.client.get(reverse('carshare:booking_create_final', kwargs=kwargs))
        self.assertEqual(get_response.status_code, 200)
        post_response = self.client.post(reverse('carshare:booking_create_final', kwargs=kwargs), data=form)
        self.assertEqual(post_response.status_code, 200)
        confirm_response = self.client.get(reverse('carshare:booking_confirm'))
        booking_id = User.objects.get(email='user@test.com').booking_set.first().id
        self.assertRedirects(confirm_response, reverse('carshare:booking_detail', kwargs={'booking_id': booking_id}))

    def test_booking_for_time_period_already_booked(self):
        """
        Booking for a time period that overlaps with an existing booking for the same vehicle returns an error message
        """
        form = {
            'booking_start_date': '01/01/2999',
            'booking_start_time': '00:00',
            'booking_end_date': '01/01/2999',
            'booking_end_time': '01:00',
        }
        self.client.login(email='user@test.com', password='bigbadtestuser')
        # Construct URL with fake data because it's only there to provide initial form values
        kwargs = {
            'vehicle_id': self.v1.id,
            'year': '2000',
            'month': '1',
            'day': '1',
            'hour': '0',
        }
        get_response = self.client.get(reverse('carshare:booking_create_final', kwargs=kwargs))
        self.assertEqual(get_response.status_code, 200)
        post_response = self.client.post(reverse('carshare:booking_create_final', kwargs=kwargs), data=form)
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, 'The selected vehicle is unavailable within the chosen times')

    def test_booking_for_time_period_already_booked_by_user_for_different_vehicle(self):
        """
        Booking for a time period that overlaps with an existing booking by the user returns an error message
        """
        form = {
            'booking_start_date': '01/01/3000',
            'booking_start_time': '00:00',
            'booking_end_date': '01/01/3000',
            'booking_end_time': '01:00',
        }
        self.client.login(email='user@test.com', password='bigbadtestuser')
        # Construct URL with fake data because it's only there to provide initial form values
        kwargs = {
            'vehicle_id': self.v1.id,
            'year': '2000',
            'month': '1',
            'day': '1',
            'hour': '0',
        }
        # First create the valid booking
        get_response = self.client.get(reverse('carshare:booking_create_final', kwargs=kwargs))
        self.assertEqual(get_response.status_code, 200)
        post_response = self.client.post(reverse('carshare:booking_create_final', kwargs=kwargs), data=form)
        self.assertEqual(post_response.status_code, 200)
        confirm_response = self.client.get(reverse('carshare:booking_confirm'))
        booking_id = User.objects.get(email='user@test.com').booking_set.first().id
        self.assertRedirects(confirm_response, reverse('carshare:booking_detail', kwargs={'booking_id': booking_id}))
        # Then try to create another booking for the same time period but different vehicle
        get_response = self.client.get(reverse('carshare:booking_create_final', kwargs=kwargs))
        self.assertEqual(get_response.status_code, 200)
        post_response = self.client.post(reverse('carshare:booking_create_final', kwargs=kwargs), data=form)
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, 'You already have a booking within the selected time frame')

    def test_booking_detail_with_existing_id(self):
        """
        Booking detail page shows correct booking details for an existing booking
        """
        self.client.login(email='user@test.com', password='bigbadtestuser')
        # Create booking for this user
        form = {
            'booking_start_date': '01/01/3000',
            'booking_start_time': '00:00',
            'booking_end_date': '01/01/3000',
            'booking_end_time': '01:00',
        }
        # Construct URL with fake data because it's only there to provide initial form values
        kwargs = {
            'vehicle_id': self.v1.id,
            'year': '2000',
            'month': '1',
            'day': '1',
            'hour': '0',
        }
        self.client.login(email='user@test.com', password='bigbadtestuser')
        get_response = self.client.get(reverse('carshare:booking_create_final', kwargs=kwargs))
        self.assertEqual(get_response.status_code, 200)
        post_response = self.client.post(reverse('carshare:booking_create_final', kwargs=kwargs), data=form)
        self.assertEqual(post_response.status_code, 200)
        confirm_response = self.client.get(reverse('carshare:booking_confirm'))
        booking = User.objects.get(email='user@test.com').booking_set.first()
        self.assertRedirects(confirm_response, reverse('carshare:booking_detail', kwargs={'booking_id': booking.id}))
        # Get detail page for the booking
        response = self.client.get(reverse('carshare:booking_detail', kwargs={'booking_id': booking.id}))
        self.assertContains(response, "Booking Detail")
        self.assertContains(response, str(booking.vehicle.make))
        self.assertContains(response, str(booking.vehicle.model))
        self.assertContains(response, str(booking.vehicle.pod.description))


@override_settings(STATICFILES_STORAGE=STATICFILES_STORAGE_FOR_TESTS)
class CarshareBookingListViewTests(TestCase):
    def setUp(self):
        vt = VehicleType.objects.create(description='Premium', hourly_rate=12.50, daily_rate=80.00)
        p1 = Pod.objects.create(latitude='-39.34523453', longitude='139.53524344', description='Pod 1')
        self.v1 = Vehicle.objects.create(pod=p1, type=vt, name='Vehicle1', make='Toyota', model='Yaris', year=2012,
                                         registration='AAA222')
        self.u1 = User.objects.create_user(email='user@test.com', password='bigbadtestuser', first_name='Test', last_name='User', date_of_birth=dt.date(1980, 1, 1))

    def create_booking(self, start, end):
        return Booking.objects.create(user=self.u1, vehicle=self.v1, schedule_start=start, schedule_end=end)

    def test_no_bookings(self):
        """
        User with no bookings gets shown appropriate message
        """
        self.client.login(email='user@test.com', password='bigbadtestuser')
        response = self.client.get(reverse('carshare:my_bookings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You have no upcoming bookings')
        self.assertContains(response, 'You have no past bookings')

    def test_current_booking(self):
        """
        User with current booking is displayed on the My Bookings page
        """
        now = timezone.localtime()
        now = timezone.make_aware(dt.datetime(now.year, now.month, now.day, now.hour, minute=0))
        two_hours_ago = now - dt.timedelta(hours=2)
        eleven_fifty_nine = timezone.make_aware(dt.datetime(now.year, now.month, now.day, hour=23, minute=59))
        b = self.create_booking(two_hours_ago, eleven_fifty_nine)

        self.client.login(email='user@test.com', password='bigbadtestuser')
        response = self.client.get(reverse('carshare:my_bookings'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_booking'], b)

    def test_upcoming_bookings(self):
        """
        User with upcoming bookings are displayed on the My Bookings page
        """
        now = timezone.localtime()
        now = timezone.make_aware(dt.datetime(now.year, now.month, now.day, now.hour, minute=0))
        two_days_from_now = now + dt.timedelta(days=2)
        twelve_oh_one_tomorrow = timezone.make_aware(dt.datetime(now.year, now.month, now.day, hour=0, minute=1)) + dt.timedelta(days=1)
        b = self.create_booking(twelve_oh_one_tomorrow, two_days_from_now)

        self.client.login(email='user@test.com', password='bigbadtestuser')
        response = self.client.get(reverse('carshare:my_bookings'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['upcoming_bookings'],
            ['<Booking: {0} - {1}>'.format(b.id, b.get_status())]
        )

    def test_past_bookings(self):
        """
        User with past bookings are displayed on the My Bookings page
        """
        now = timezone.localtime()
        now = timezone.make_aware(dt.datetime(now.year, now.month, now.day, now.hour, minute=0))
        two_hours_ago = now - dt.timedelta(hours=2)
        one_minute_ago = now - dt.timedelta(minutes=1)
        b = self.create_booking(two_hours_ago, one_minute_ago)

        self.client.login(email='user@test.com', password='bigbadtestuser')
        response = self.client.get(reverse('carshare:my_bookings'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['past_bookings'],
            ['<Booking: {0} - {1}>'.format(b.id, b.get_status())]
        )


@override_settings(STATICFILES_STORAGE=STATICFILES_STORAGE_FOR_TESTS)
class CarshareBookingDetailViewTests(TestCase):
    def setUp(self):
        vt = VehicleType.objects.create(description='Premium', hourly_rate=12.50, daily_rate=80.00)
        p1 = Pod.objects.create(latitude='-39.34523453', longitude='139.53524344', description='Pod 1')
        self.v1 = Vehicle.objects.create(pod=p1, type=vt, name='Vehicle1', make='Toyota', model='Yaris', year=2012,
                                         registration='AAA222')
        self.u1 = User.objects.create_user(email='test1@test.com', password='flippleflopple', first_name='John', last_name='Doe', date_of_birth='1980-01-01')

    def create_booking(self, start, end):
        return Booking.objects.create(
            user=self.u1,
            vehicle=self.v1,
            schedule_start=timezone.make_aware(start),
            schedule_end=timezone.make_aware(end)
        )

    def test_confirmed_unpaid_booking(self):
        b1 = self.create_booking(start=dt.datetime(year=2999, month=1, day=1, hour=0),
                                 end=dt.datetime(year=2999, month=1, day=1, hour=1))
        self.client.login(email='test1@test.com', password='flippleflopple')
        response = self.client.get(reverse('carshare:booking_detail', kwargs={'booking_id': b1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '>Pay<')
        self.assertContains(response, '>Extend<')
        self.assertContains(response, '>Cancel<')

    def test_active_unpaid_booking(self):
        yesterday = dt.datetime.now() - dt.timedelta(days=1)
        tomorrow = dt.datetime.now() + dt.timedelta(days=1)
        b1 = self.create_booking(start=yesterday, end=tomorrow)
        self.client.login(email='test1@test.com', password='flippleflopple')
        response = self.client.get(reverse('carshare:booking_detail', kwargs={'booking_id': b1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '>Pay<')
        self.assertContains(response, '>Extend<')
        self.assertNotContains(response, '>Cancel<')

    def test_cancelled_booking(self):
        b1 = self.create_booking(start=dt.datetime(year=2999, month=1, day=1, hour=0),
                                 end=dt.datetime(year=2999, month=1, day=1, hour=1))
        b1.cancelled = timezone.now()
        b1.save()
        self.client.login(email='test1@test.com', password='flippleflopple')
        response = self.client.get(reverse('carshare:booking_detail', kwargs={'booking_id': b1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '>Pay<')
        self.assertNotContains(response, '>Extend<')
        self.assertNotContains(response, '>Cancel<')

    def test_complete_unpaid_booking(self):
        start = dt.datetime.now() - dt.timedelta(days=1)
        end = start + dt.timedelta(hours=1)
        b1 = self.create_booking(start=start, end=end)
        self.client.login(email='test1@test.com', password='flippleflopple')
        response = self.client.get(reverse('carshare:booking_detail', kwargs={'booking_id': b1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '>Pay<')
        self.assertNotContains(response, '>Extend<')
        self.assertNotContains(response, '>Cancel<')

    def test_confirmed_paid_booking(self):
        b1 = self.create_booking(start=dt.datetime(year=2999, month=1, day=1, hour=0),
                                 end=dt.datetime(year=2999, month=1, day=1, hour=1))
        invoice = Invoice(booking=b1, amount=b1.calculate_cost(), date=timezone.localdate())
        invoice.save()
        self.client.login(email='test1@test.com', password='flippleflopple')
        response = self.client.get(reverse('carshare:booking_detail', kwargs={'booking_id': b1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '>Pay<')
        self.assertNotContains(response, '>Extend<')
        self.assertNotContains(response, '>Cancel<')
        self.assertContains(response, '>View Invoice<')

    def test_active_paid_booking(self):
        yesterday = dt.datetime.now() - dt.timedelta(days=1)
        tomorrow = dt.datetime.now() + dt.timedelta(days=1)
        b1 = self.create_booking(start=yesterday,end=tomorrow)
        invoice = Invoice(booking=b1, amount=b1.calculate_cost(), date=timezone.localdate())
        invoice.save()
        self.client.login(email='test1@test.com', password='flippleflopple')
        response = self.client.get(reverse('carshare:booking_detail', kwargs={'booking_id': b1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '>Pay<')
        self.assertNotContains(response, '>Extend<')
        self.assertNotContains(response, '>Cancel<')
        self.assertContains(response, '>View Invoice<')

    def test_complete_paid_booking(self):
        start = dt.datetime.now() - dt.timedelta(days=1)
        end = start + dt.timedelta(hours=1)
        b1 = self.create_booking(start=start, end=end)
        invoice = Invoice(booking=b1, amount=b1.calculate_cost(), date=timezone.localdate())
        invoice.save()
        self.client.login(email='test1@test.com', password='flippleflopple')
        response = self.client.get(reverse('carshare:booking_detail', kwargs={'booking_id': b1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '>Pay<')
        self.assertNotContains(response, '>Extend<')
        self.assertNotContains(response, '>Cancel<')
        self.assertContains(response, '>View Invoice<')
