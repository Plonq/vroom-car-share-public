#
#   Author(s): Huon Imberger
#   Description: Configures django-admin for account-related admin tasks
#

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Address, CreditCard
from .forms import UserCreationForm, UserChangeForm


# Inlines to allow editing of address and credit card on the same page as user details
class AddressInline(admin.StackedInline):
    model = Address
    can_delete = True
    verbose_name_plural = 'Address'


class CreditCardInline(admin.StackedInline):
    model = CreditCard
    can_delete = True
    verbose_name_plural = 'Credit Card'


class UserAdmin(BaseUserAdmin):
    # Add inline forms for address and credit card
    inlines = (AddressInline, CreditCardInline)

    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # These define the fields in the list view
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff',)
    # These are the fields on the 'edit' page
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'date_of_birth',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    # These are the fields that appear when creating a user via django admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'date_of_birth', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

    # Method overrides to increase security
    def get_inline_instances(self, request, obj=None):
        # Prevents inline fields (address credit card) when creating new user or if user is staff
        if not obj or obj.is_staff:
            return list()
        return super(UserAdmin, self).get_inline_instances(request, obj)

    def get_readonly_fields(self, request, obj=None):
        # Prevent staff changing their own permissions
        rof = super(UserAdmin, self).get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            rof += ('is_staff', 'is_superuser', 'groups', 'user_permissions')
        return rof

    def has_change_permission(self, request, obj=None):
        # Prevent staff changing other user's who may have higher privileges.
        has = super(UserAdmin, self).has_change_permission(request, obj)
        if obj and not request.user.is_superuser:
            if obj != request.user:
                if obj.is_superuser or obj.user_permissions.exists():
                    has = False
        return has


# Register user admin
admin.site.register(User, UserAdmin)
