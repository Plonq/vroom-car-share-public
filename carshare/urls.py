#
#   Author(s): Huon Imberger, Steven Thompson, Shaun O'Malley
#   Description: Maps views (controllers) to URL patterns. AKA routes - for core function pages
#

from django.conf.urls import url

from . import views


app_name = 'carshare'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'contact-us/$', views.contact_us, name='contact_us'),
    url(r'pricing/$', views.pricing, name='pricing'),
    url(r'how-it-works/$', views.how_it_works, name='how_it_works'),
    url(r'faq/$', views.faq, name='faq'),
    url(r'privacy/$', views.privacy, name='privacy'),
    url(r'about-us/$', views.about_us, name='about_us'),
    url(r'find-a-car/$', views.find_a_car, name='find_a_car'),
    url(r'bookings/new/(?P<vehicle_id>[0-9]+)/$', views.booking_timeline, name='booking_create'),
    url(r'bookings/new/(?P<vehicle_id>[0-9]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/$',
        views.booking_timeline, name='booking_create_date'),
    url(r'bookings/new/(?P<vehicle_id>[0-9]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/(?P<hour>[0-9]{1,2})/$',
        views.booking_create, name='booking_create_final'),
    url(r'bookings/new/(?P<vehicle_id>[0-9]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/(?P<hour>[0-9]{1,2})/(?P<length>[0-9]{1,4})/$',
        views.booking_create, name='booking_create_final_length'),
    url(r'bookings/confirm/$', views.booking_confirm, name='booking_confirm'),
    url(r'bookings/(?P<booking_id>[0-9]+)/$', views.booking_detail, name='booking_detail'),
    url(r'bookings/(?P<booking_id>[0-9]+)/extend/$', views.booking_extend, name='booking_extend'),
    url(r'bookings/$', views.my_bookings, name='my_bookings'),
    url(r'bookings/(?P<booking_id>[0-9]+)/cancel/$', views.booking_cancel, name='booking_cancel'),
    url(r'bookings/(?P<booking_id>[0-9]+)/pay/$', views.booking_pay, name='booking_pay'),
    url(r'bookings/(?P<booking_id>[0-9]+)/invoice/$', views.booking_invoice, name='booking_invoice'),
    # AJAX
    url(r'bookings/new/(?P<vehicle_id>[0-9]+)/calculate-cost/', views.booking_calculate_cost, name='ajax_booking_calculate_cost'),
]


