#
#   Author(s): Huon Imberger, Steven Thompson, Shaun O'Malley
#   Description: Maps views (controllers) to URL patterns. AKA routes - for account-related pages
#

from django.conf.urls import url, include
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView, PasswordChangeDoneView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView

from .forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from . import views


urlpatterns = [
    # Override django auth templates with our own
    url(r'^login/$', LoginView.as_view(form_class=AuthenticationForm, redirect_authenticated_user=True)),
    url(r'^logout/$', LogoutView.as_view(template_name='accounts/logged_out.html')),
    url(r'^password_change/$', PasswordChangeView.as_view(template_name='accounts/password_change_form.html', form_class=PasswordChangeForm)),
    url(r'^password_change/done/$', PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html')),
    url(r'^password_reset/$', PasswordResetView.as_view(template_name='accounts/password_reset_form.html', form_class=PasswordResetForm)),
    url(r'^password_reset/done/$', PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html')),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html', form_class=SetPasswordForm)),
    url(r'^reset/done/$', PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html')),
    # Fall back on defaults for everything else
    url(r'^', include('django.contrib.auth.urls')),
    # Other accounts-related pages not included in django auth
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$', views.activate_account, name='activate_account'),
    url(r'^register/$', views.register_user, name='register'),
    url(r'^register/address/$', views.register_address, name='register_address'),
    url(r'^register/credit-card/$', views.register_credit_card, name='register_credit_card'),
    url(r'^register/cancel/$', views.register_cancel, name='register_cancel'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^profile/edit/$', views.edit_profile, name='edit_profile'),
    url(r'^profile/edit/update-credit-card/$', views.update_credit_card, name='update_credit_card'),
    url(r'^profile/edit/update-email/$', views.update_email, name='update_email'),
    url(r'^profile/edit/update-email/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$', views.update_email_verify, name='update_email_verify'),
    url(r'^delete/$', views.delete_account, name='delete_account'),
    url(r'^disable/$', views.disable_account, name='disable_account'),
]
