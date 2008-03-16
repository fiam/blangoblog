from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.utils.translation import ugettext_lazy as _

from settings import BLANGO_URL, BLANGO_TITLE, LANGUAGE_CODE

from blango.models import Language, Tag, Entry

class LatestEntries(Feed):
    title_template = 'blango/feeds/title.html'
    description_template = 'blango/feeds/description.html'

    def get_object(self, bits):
        if len(bits) == 1:
            lang = bits[0]
        else:
            lang = LANGUAGE_CODE.split('-')[0]

        return Language.objects.get(iso639_1=lang)

    def title(self, obj):
        return _('%(title)s | latest entries (%(name)s)') % { 'title': BLANGO_TITLE, 'name': obj.name }

    def link(self, obj):
        return BLANGO_URL + obj.iso639_1 + '/'

    def items(self, obj):
        return Entry.objects.filter(language=obj).order_by('-published')[:30]
        

class LatestEntriesByTag(LatestEntries):
    title_template = 'blango/feeds/title.html'
    description_template = 'blango/feeds/description.html'

    def get_object(self, bits):
        if len(bits) != 2:
            raise FeedDoesNotExist
    
        return (Tag.objects.get(slug=bits[0]), Language.objects.get(iso639_1=bits[1]))

    def title(self, obj):
        return _('Latest entries in %(language)s (%(name)s)') % { 'langugage': obj[0].name, 'name': obj[1].name }

    def link(self, obj):
        return '%s/%s/' % (obj[0].get_absolute_url(), obj[1].iso639_1)

    def items(self, obj):
        return Entry.objects.filter(language=obj[1], tags=obj[0]).order_by('-published')[:30]

class LatestComments(Feed):
    title_template = 'blango/feeds/title.html'
    description_template = 'blango/feeds/description.html'

    def get_object(self, bits):
        if len(bits) != 1:
            raise FeedDoesNotExist

        return Entry.objects.get(slug=bits[0])

    def title(self, obj):
        return _('Latest comments for "%s"') % obj.title

    def link(self, obj):
        return obj.get_absolute_url()

    def items(self, obj):
        return obj.comments.order_by('-submitted')[:30]
