from django.conf.urls.defaults import *
from django.contrib import admin

urlpatterns = patterns('',
    (r'^site-media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/fiam/blog/media/'}),
    (r'^admin/(.*)', admin.site.root),
    (r'^', include('blog.blango.urls')),
)
