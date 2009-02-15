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
    from os.path import abspath, dirname, join
    PROJECT_DIR = dirname(abspath(__file__))
    urlpatterns += patterns('',
        (r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'django.views.static.serve', {'document_root': join(PROJECT_DIR, 'media')}),
    )
