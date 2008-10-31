from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings

admin.autodiscover()
urlpatterns = patterns('',
    (r'^admin/(.*)', admin.site.root),
    (r'^', include('blangoblog.blango.urls')),
)

handler500 = 'blango.views.server_error'
handler404 = 'blango.views.page_not_found'

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site-media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/fiam/blog/media/'}),
    )
