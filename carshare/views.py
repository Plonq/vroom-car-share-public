#
#   Author(s): Huon Imberger, Shaun O'Malley
#   Description: Controllers for core pages
#

from django.contrib import messages
from django.core.mail import EmailMessage, BadHeaderError
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

from wkhtmltopdf.views import PDFTemplateResponse

import datetime as dt
import json

from .forms import ContactForm, BookingForm, ExtendBookingForm
from .models import Vehicle, Booking, Invoice, Pod


def index(request):
    return render(request, 'carshare/index.html')


def pricing(request):
    return render(request, 'carshare/pricing.html')


def how_it_works(request):
    return render(request, 'carshare/how_it_works.html')


def faq(request):
    return render(request, 'carshare/faq.html')


def privacy(request):
    """
    Render privacy policy PDF document
    """
    from django.http import FileResponse
    return FileResponse(open('vroom_car_share/static/privacy_policy.pdf', 'rb'), content_type='application/pdf')


def about_us(request):
    """
    Calculates approximate savings over owning a car and displays About info
    """
    # Owner cost: $75 per trip, calculated using values from GoGet (10,000 kms per annum, car is used 20
    # hours per week, petrol $1.44 per litre). Assuming 20 hours is two trips on average.
    owner_cost = 75 * Booking.objects.count()
    vroom_cost = 0.0
    for b in Booking.objects.filter(schedule_end__lt=timezone.now()):
        vroom_cost += b.calculate_cost()
    estimated_savings = owner_cost - vroom_cost
    context = {
        'num_vehicles': Vehicle.objects.count(),
        'num_locations': Pod.objects.count(),
        'num_shares': Booking.objects.count(),
        'estimated_savings': int(estimated_savings),
    }
    return render(request, 'carshare/about_us.html', context)


def contact_us(request):
    """
    Contact form and Vroom information
    """
    if request.method == 'POST':
        # Create form from POST data and validate
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            contact_name = contact_form.cleaned_data['contact_name']
            contact_email = contact_form.cleaned_data['contact_email']
            subject = 'New Contact Us from {0}'.format(contact_name)
            message = contact_form.cleaned_data['message']
            try:
                # Send email to admin with the contact message
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email='admin@vroomcs.org',
                    to=['admin@vroomcs.org'],
                    reply_to=[contact_email],
                )
                email.send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return render(request, "carshare/contact_us_success.html")
    else:
        contact_form = ContactForm()

    return render(request, "carshare/contact_us.html", {'contact_form': contact_form})


def find_a_car(request):
    """
    Interactive map page
    """
    # Get all active vehicles that have been assigned to a pod
    active_vehicles_with_pods = Vehicle.objects.filter(active=True).exclude(pod__isnull=True)
    context = {
        'vehicles': active_vehicles_with_pods
    }
    return render(request, "carshare/find_a_car.html", context)


@login_required
def booking_timeline(request, vehicle_id, year=None, month=None, day=None):
    """
    The booking timeline view, showing availability of selected vehicle and allowing user to choose a booking start time
    """
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    # Redirect if vehicle is inactive
    if not vehicle.is_active():
        return redirect('carshare:find_a_car')

    # Default to today if no date specified
    if year and month and day:
        date = dt.date(int(year), int(month), int(day))
    else:
        date = timezone.localtime().date()
    # Build dict of hours and whether that hour is available
    hours = {}
    for i in range(0, 24):
        datetime = timezone.make_aware(dt.datetime.combine(date, dt.time(hour=i, minute=0)), timezone.get_current_timezone())
        if vehicle.is_available_at(datetime=datetime) and datetime > timezone.localtime() - dt.timedelta(hours=1):
            hours[i] = 'available'
        elif not vehicle.get_booking_at(datetime=datetime) is None and vehicle.get_booking_at(datetime=datetime).user == request.user:
            hours[i] = 'booked_by_user'
        else:
            hours[i] = 'unavailable'
    context = {
        'vehicle': vehicle,
        'hours': hours,
        'date': date,
        'today': timezone.localtime().today().date(),
    }
    return render(request, "carshare/bookings/create_timeline.html", context)


@login_required
def booking_create(request, vehicle_id, year=None, month=None, day=None, hour=None, length=1):
    """
    Booking form for selected vehicle. Pre-fills form with provided data.
    Also displays a booking review page before creating booking.
    """
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    datetime = dt.datetime(int(year), int(month), int(day), int(hour), minute=0)

    # Redirect if vehicle is inactive
    if not vehicle.is_active():
        return redirect('carshare:find_a_car')

    if request.method == 'POST':
        booking_form = BookingForm(request.POST)
        if booking_form.is_valid():
            data = booking_form.cleaned_data
            booking_start = data['schedule_start']
            booking_end = data['schedule_end']

            # Custom validation
            is_valid_booking = True
            # Prevent booking overlapping with existing booking
            existing_bookings = Booking.objects.filter(vehicle=vehicle, cancelled__isnull=True)
            for b in existing_bookings:
                if (b.schedule_start <= booking_start < b.schedule_end or
                        b.schedule_start < booking_end <= b.schedule_end or
                        booking_start <= b.schedule_start and booking_end >= b.schedule_end):
                    is_valid_booking = False
                    booking_form.add_error(None, "The selected vehicle is unavailable within the chosen times")
                    break
            # Prevent multiple bookings for the same user during the same time period
            user_bookings = request.user.booking_set.filter(cancelled__isnull=True)
            for b in user_bookings:
                if (b.schedule_start <= booking_start < b.schedule_end or
                        b.schedule_start < booking_end <= b.schedule_end or
                        booking_start <= b.schedule_start and booking_end >= b.schedule_end):
                    is_valid_booking = False
                    booking_form.add_error(None, "You already have a booking within the selected time frame")
                    break

            if is_valid_booking:
                # Save details in session, but also provide to template context. When confirmed, we'll create the
                # booking from the session vars.
                request.session['vehicle_id'] = vehicle.id
                request.session['booking_start'] = booking_start
                request.session['booking_end'] = booking_end
                booking = Booking(
                    user=request.user,
                    vehicle=vehicle,
                    schedule_start=booking_start,
                    schedule_end=booking_end,
                )
                # Include start date, hour, and length of booking so we can have a Back button
                length = (booking_end - booking_start)
                length_hours = length.days * 24 + length.seconds / 60 / 60
                context = {
                    'booking': booking,
                    'datetime': booking_start,
                    'length': int(length_hours),
                }
                return render(request, 'carshare/bookings/review.html', context)

            # Else, continue and render the same page with form errors
    else:
        booking_form = BookingForm(initial_start_datetime=datetime, initial_length=length)
        booking_form.is_bound = False  # Prevent validation triggering

    context = {
        'vehicle': vehicle,
        'booking_form': booking_form,
        'date': datetime.date,
        'booking_length': length,
    }
    return render(request, "carshare/bookings/create.html", context)


@login_required
def booking_confirm(request):
    """
    Creates booking from session variables (which should be set in booking_create())
    """
    # Create booking from session vars, since form was previously submitted
    try:
        vehicle_id = request.session['vehicle_id']
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        schedule_start = request.session['booking_start']
        schedule_end = request.session['booking_end']
        del request.session['vehicle_id']
        del request.session['booking_start']
        del request.session['booking_end']
    except KeyError:
        return redirect('carshare:index')

    booking = Booking(
        user=request.user,
        vehicle=vehicle,
        schedule_start=schedule_start,
        schedule_end=schedule_end,
    )
    booking.save()

    # Send confirmation email
    request.user.send_email(
       template_name='Booking Confirmation',
       context={
          'user': request.user,
          'booking': booking,
        },
     )
    messages.success(request, 'Booking created successfully')
    return redirect('carshare:booking_detail', booking.id)


@login_required
def booking_detail(request, booking_id):
    """
    Displays details of a single booking
    """
    # Get booking, or display message and redirect if booking doesn't belong to auth'd user
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.user != booking.user:
        messages.error(request, 'You do not have permission to view that booking')
        return redirect('carshare:index')
    context = {
        'booking': booking,
    }
    return render(request, "carshare/bookings/detail.html", context)


@login_required
def my_bookings(request):
    """
    Page displaying all of a user's bookings, split into logical groups
    """
    # Get list past and upcoming bookings, as well as the current booking
    now = timezone.localtime()
    current_booking = request.user.get_current_booking()
    upcoming_bookings = request.user.booking_set.filter(
        schedule_start__gt=now).filter(cancelled__isnull=True).order_by('schedule_start')
    past_bookings = request.user.booking_set.filter(
        Q(schedule_end__lte=now) | Q(cancelled__isnull=False)).order_by('-schedule_start')
    context = {
        'current_booking': current_booking,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
    }
    return render(request, "carshare/bookings/my_bookings.html", context)


@login_required
def booking_extend(request, booking_id):
    """
    Logic for extending a booking
    """
    booking = get_object_or_404(Booking, pk=booking_id)
    # Redirect conditions
    if request.user != booking.user:
        messages.error(request, 'You do not have permission to view that booking')
        return redirect('carshare:index')
    if booking.is_paid():
        messages.error(request, 'You cannot extend a booking that has already been paid')
        return redirect('carshare:my_bookings')

    if request.method == 'POST':
        # Create form from POST data and validate
        extend_booking_form = ExtendBookingForm(request.POST, current_booking_end=booking.schedule_end)
        if extend_booking_form.is_valid():
            new_schedule_end = extend_booking_form.cleaned_data['new_schedule_end']
            # Custom validation
            is_valid_booking = True
            # Make sure new end date doesn't clash with existing booking
            existing_bookings = Booking.objects.filter(
                vehicle=booking.vehicle, cancelled__isnull=True
            ).exclude(user=request.user)
            for b in existing_bookings:
                if (b.schedule_start <= booking.schedule_start <= b.schedule_end or
                        b.schedule_start <= new_schedule_end <= b.schedule_end or
                        booking.schedule_start <= b.schedule_start and new_schedule_end >= b.schedule_end):
                    is_valid_booking = False
                    extend_booking_form.add_error(None, "The new end date overlaps with existing booking. "
                                                        "The latest date you can choose is {0}".format(b.schedule_start))
                    break
            user_bookings = request.user.booking_set.filter(cancelled__isnull=True).exclude(id__exact=booking.id)
            for b in user_bookings:
                if (b.schedule_start <= booking.schedule_start <= b.schedule_end or
                        b.schedule_start <= new_schedule_end <= b.schedule_end or
                        booking.schedule_start <= b.schedule_start and new_schedule_end >= b.schedule_end):
                    is_valid_booking = False
                    extend_booking_form.add_error(
                        None, "The new booking end overlaps with one of your existing bookings"
                    )
                    break

            # New booking end is valid? Save booking send email
            if is_valid_booking:
                booking.schedule_end = new_schedule_end
                booking.save()

                # Send confirmation email
                request.user.send_email(
                    template_name='Booking Extended',
                    context={
                        'booking': booking,
                    },
                )

                messages.success(
                    request, "Your current booking has been extended. You will receive email confirmation shortly."
                )
                return redirect('carshare:booking_detail', booking_id)
    else:
        extend_booking_form = ExtendBookingForm(current_booking_end=booking.schedule_end)

    context = {
        'booking': booking,
        'extend_booking_form': extend_booking_form,
    }
    return render(request, "carshare/bookings/extend.html", context)


def booking_cancel(request, booking_id):
    """
    Logic for cancelling a booking
    """
    booking = get_object_or_404(Booking, pk=booking_id)
    # Redirect conditions
    if request.user != booking.user:
        messages.error(request, 'You do not have permission to view that booking')
        return redirect('carshare:index')
    if booking.cancelled:
        messages.error(request, 'This booking has already been cancelled')
        return redirect('carshare:my_bookings')
    if booking.is_complete():
        messages.error(request, 'You cannot cancel a booking that has already been completed')
        return redirect('carshare:my_bookings')
    if booking.is_paid():
        messages.error(request, 'You cannot cancel a booking that has already been paid')
        return redirect('carshare:my_bookings')

    # Cancel booking
    booking.cancelled = timezone.now()
    booking.save()
    # Send email confirmation
    request.user.send_email(
        template_name='Booking Cancelled',
        context={
            'booking': booking,
        },
    )
    messages.success(request, 'Successfully cancelled booking for {0} the {1} {2}'.format(booking.vehicle.name,
                                                                                          booking.vehicle.make,
                                                                                          booking.vehicle.model))
    return redirect('carshare:booking_detail', booking.id)


def booking_pay(request, booking_id):
    """
    Logic for paying a booking (note: no actual payment is charged to user's credit card)
    """
    booking = get_object_or_404(Booking, pk=booking_id)
    # Redirect conditions
    if request.user != booking.user:
        messages.error(request, 'You do not have permission to view that booking')
        return redirect('carshare:index')
    # Only allow to end booking if the booking is active.
    if booking.cancelled:
        messages.error(request, 'You cannot pay a booking that has been cancelled')
        return redirect('carshare:my_bookings')
    # Is already paid?
    if hasattr(booking, 'invoice'):
        messages.info(request, 'This booking has already been paid')
        return redirect('carshare:booking_detail', booking.id)

    # Create invoice and email it to user
    invoice = Invoice(booking=booking, amount=booking.calculate_cost())
    invoice.save()
    context = {'invoice': invoice}
    invoice_filename = 'invoice_{0}.pdf'.format(invoice.id)
    response = PDFTemplateResponse(
        request=request,
        template='carshare/pdf/invoice.html',
        context=context,
    )
    request.user.send_email(
        template_name='Booking Invoice',
        context=context,
        attachment_filename=invoice_filename,
        attachment_data=response.rendered_content,
    )
    messages.success(request, 'Thank you for your booking. An invoice has been emailed to you.')
    return redirect('carshare:booking_detail', booking.id)


def booking_invoice(request, booking_id):
    """
    Creates and displays an invoice as PDF for a booking
    """
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.user != booking.user:
        messages.error(request, 'You do not have permission to view that invoice')
        return redirect('carshare:index')
    # Render PDF invoice
    return PDFTemplateResponse(
        request=request,
        template='carshare/pdf/invoice.html',
        context={'invoice': booking.invoice},
    )


#
# AJAX views
#
def booking_calculate_cost(request, vehicle_id):
    """
    Calculates booking cost given start and end times (from POST)
    """
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    if request.method == 'POST':
        booking_form = BookingForm(request.POST)
        if booking_form.is_valid():
            # Create booking object using provided data and use its method
            data = booking_form.cleaned_data
            booking_start = data['schedule_start']
            booking_end = data['schedule_end']
            booking = Booking(user=request.user, vehicle=vehicle, schedule_start=booking_start, schedule_end=booking_end)
            # DO NOT SAVE BOOKING!
            days, hours = booking.calculate_daily_hourly_billable_counts()
            cost = {
                'total': '${0:.2f}'.format(booking.calculate_cost()),
                'days': days,
                'hours': hours,
            }
            # Return calculated cost as string
            return HttpResponse(json.dumps(cost))
        else:
            return HttpResponse(json.dumps({'error': booking_form.errors}))
