from django.conf.urls.defaults import *
from blango.feeds import *

feeds = {
    'latest': LatestEntries,
    'tag': LatestEntriesByTag,
    'comments': LatestComments,
}
urlpatterns = patterns('blango.views',
    (r'^((?P<lang>[a-z]{2})/)?(tag/(?P<tag_slug>[\w\-]+)/)?((?P<year>\d{4})/(?P<month>\d{2})/)?((?P<page>\d+)/)?$', 'list_view'),
    (r'^entry/(?P<entry_slug>[\w\-]+)/$', 'entry_view'),
) + patterns('django.contrib.syndication.views',
    (r'^feeds/(?P<url>.*)/$', 'feed', { 'feed_dict': feeds })
)
