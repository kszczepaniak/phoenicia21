from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls import (
handler404, handler500
)

urlpatterns = [
    # Examples:
    # url(r'^$', 'Phoenicia21.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^core/', include('core.urls')),
    url(r'^admin/', include(admin.site.urls)),
]
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
