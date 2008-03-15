from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^site-media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/fiam/blog/media/'}),
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^', include('blog.blango.urls')),
)
