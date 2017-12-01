#
#   Author(s): Huon Imberger
#   Description: Configures django-admin for admin tasks
#

from django.contrib import admin

from .models import Vehicle, Pod, VehicleType, Booking, Invoice


# Methods for bulk action - making vehicles inactive or active
def make_active(modeladmin, request, queryset):
    queryset.update(active=True)


make_active.short_description = "Mark selected vehicles as active"


def make_inactive(modeladmin, request, queryset):
    queryset.update(active=False)


make_inactive.short_description = "Mark selected vehicles as inactive"


# Define what data is displayed on admin pages
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'make', 'model', 'pod', 'active']
    ordering = ['name']
    actions = [make_active, make_inactive]


class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'description', 'hourly_rate', 'daily_rate']
    ordering = ['description']


class PodAdmin(admin.ModelAdmin):
    list_display = ['id', 'description', 'vehicle']
    ordering = ['description']


class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'vehicle', 'schedule_start', 'schedule_end']
    ordering = ['schedule_start']


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'amount']
    ordering = ['id']


# Register custom definitions with django-admin
admin.site.register(VehicleType, VehicleTypeAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(Pod, PodAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Invoice, InvoiceAdmin)
