#
#   Author(s): Huon Imberger
#   Description: Master URL configuration
#

from django.conf.urls import url, include
from django.contrib import admin

# Site details (affects admin)
admin.site.site_title = 'Vroom Admin'
admin.site.site_header = 'Vroom Car Share Admin'

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('accounts.urls')),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^', include('carshare.urls', namespace='carshare')),
]
