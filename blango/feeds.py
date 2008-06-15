from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from blango.models import Language, Tag, Entry

class LatestEntries(Feed):
    title_template = 'blango/feeds/title.html'
    description_template = 'blango/feeds/description.html'

    def get_object(self, bits):
        if len(bits) == 1:
            return Language.objects.get(iso639_1=bits[0])
        return None

    def title(self, obj):
        if obj:
            return _('%(title)s | latest entries (%(name)s)') % { 'title': settings.BLANGO_TITLE, 'name': obj.name }
        return _('%(title)s | latest entries') % { 'title': settings.BLANGO_TITLE }

    def link(self, obj):
        if obj:
            return settings.BLANGO_URL + obj.iso639_1 + '/'
        return settings.BLANGO_URL

    def items(self, obj):
        entries = Entry.published.order_by('-pub_date')
        if obj:
            entries = entries.filter(language=obj)

        return entries[:30]

    def item_pubdate(self, obj):
        return obj.pub_date


class LatestEntriesByTag(LatestEntries):
    title_template = 'blango/feeds/title.html'
    description_template = 'blango/feeds/description.html'

    def get_object(self, bits):
        if len(bits) == 2:
            return (Tag.objects.get(slug=bits[0]), Language.objects.get(iso639_1=bits[1]))
        if len(bits) == 1:
             return (Tag.objects.get(slug=bits[0]), None)
        raise FeedDoesNotExist

    def title(self, obj):
        if obj[1]:
            return _('Latest entries in %(language)s tagged with %(tag)s') % { 'language': obj[1].name, 'tag': obj[0].name }
        return _('Latest entries tagged with %(tag)s') % { 'tag': obj[0].name }

    def link(self, obj):
        if obj[1]:
            return '%s/%s/' % (obj[0].get_absolute_url(), obj[1].iso639_1)
        return '%s/' % obj[0].get_absolute_url()

    def items(self, obj):
        if obj[1]:
            return Entry.published.filter(language=obj[1], tags=obj[0]).order_by('-pub_date')[:30]
        return Entry.published.filter(tags=obj[0]).order_by('-pub_date')[:30]

class LatestComments(Feed):
    title_template = 'blango/feeds/title.html'
    description_template = 'blango/feeds/description.html'

    def get_object(self, bits):
        if len(bits) != 1:
            raise FeedDoesNotExist

        return Entry.published.get(slug=bits[0])

    def title(self, obj):
        return _('Latest comments for "%s"') % obj.title

    def link(self, obj):
        return obj.get_absolute_url()

    def items(self, obj):
        return obj.comments.order_by('-submitted')[:30]

    def item_pubddate(self, obj):
        return obj.submitted
