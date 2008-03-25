from django.db import models, connection
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from settings import BLANGO_URL, BLANGO_TITLE
from blango.spider import Spider

from markdown import markdown

from datetime import datetime
import re

class short_description(object):
    def __init__(self, desc):
        self.desc = desc
    def __call__(self, func):
        func.short_description = self.desc
        return func

def make_slug(obj):
    slug = slugify(obj.slug_generator)[:50]
    retval = slug
    i = 2;
    pk = obj.pk or 0
    while True:
        try:
            obj.__class__.objects.exclude(pk=pk).get(slug=retval)
            retval = slug[:49 - len(str(i))] + '-' + str(i)
            i += 1
        except obj.__class__.DoesNotExist:
            return retval

class Language(models.Model):
    name = models.CharField('Language name', max_length=20, unique=True)
    iso639_1 = models.CharField('ISO 639-1 language code', max_length=2, unique=True)

    class Admin:
        pass

    class Meta:
        verbose_name = _('language')
        verbose_name_plural = _('languages')

    def __unicode__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField('Tag name', max_length=32)
    slug = models.SlugField(blank=True)

    class Admin:
        fields = (
            (None, {'fields': ('name',)}),
        )

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')

    def save(self):
        self.slug = make_slug(self)
        super(Tag, self).save()

    def get_absolute_url(self):
        return BLANGO_URL + 'tag/%s/' % self.slug

    def __unicode__(self):
        return self.name

    @property
    def slug_generator(self):
        return self.name

    @staticmethod
    def for_language(language):
        cursor = connection.cursor()
        cursor.execute('''SELECT DISTINCT t.tag_id FROM blango_entry_tags AS t
            JOIN blango_entry AS e ON e.id = t.entry_id WHERE e.language_id = %d
            ''' % language.id)
        return Tag.objects.filter(id__in=[t[0] for t in cursor.fetchall()])

class Entry(models.Model):
    title = models.CharField(_('title'), max_length=65)
    slug = models.SlugField(max_length=65, blank=True)
    author = models.ForeignKey(User, blank=True)
    language = models.ForeignKey(Language, radio_admin=True, verbose_name=_('language'))
    body = models.TextField(_('body'))
    tags = models.ManyToManyField(Tag, verbose_name=_('tags'), filter_interface=models.HORIZONTAL)
    body_html = models.TextField(blank=True)
    published = models.DateTimeField(_('Date published'), default=datetime.now())
    draft = models.BooleanField(_('Save as draft (don\'t publish it yet)'), default=False)
    translations = models.ManyToManyField('Entry', blank=True, verbose_name=_('translations'), filter_interface=models.HORIZONTAL)

    class Admin:
        fields = (
            (_('Entry'), {'fields': ('title', 'body')}),
            (_('Tags'), {'fields': ('tags', )}),
            (_('Language'), {'fields': ('language', )}),
            (_('Date published'), {'fields': ('published', )}),
            (_('Save as draft'), { 'fields': ('draft',)}),
            (_('Published translations'), { 'fields': ('translations', )}),
        )
        list_display = ('title', 'language', 'formatted_tags', 'published')

    class Meta:
        verbose_name = _('entry')
        verbose_name_plural = _('entries')

    def __unicode__(self):
        return self.title

    def ping(self):
        r = re.compile('<a.*?href=["\'](.*?)["\'].*?>', re.I | re.S)
        for anchor in r.finditer(self.body_html):
            if anchor.find(BLANGO_URL) == 0:
                continue
            s = Spider(anchor.group(1))
            if not s.trackback(title=self.title,
                    url=self.get_absolute_url(),
                    excerpt=self.body_html,
                    page_name=BLANGO_TITLE):
                s.pingback(self.get_absolute_url())

    def save(self):
        self.slug = make_slug(self)
        if not self.author_id:
            self.author = User.objects.get(pk=1)
        self.body_html = markdown(self.body, ['codehilite'])
        published_now = self.pk is None and not self.draft
        if not self.draft:
            if self.pk and Entry.objects.get(pk=self.pk).draft != self.draft:
                self.published = datetime.now()
                published_now = True

        super(Entry, self).save()
        if published_now:
            self.ping()

    def get_absolute_url(self):
        return BLANGO_URL + 'entry/%s/' % self.slug

    def get_trackback_url(self):
        return BLANGO_URL + 'trackback/%d/' % self.pk

    @short_description(_('tags'))
    def formatted_tags(self):
        return u', '.join(t.__unicode__() for t in self.tags.all())

    @property
    def description(self):
        return mark_safe(self.body)

    @property
    def comments(self):
        return self.comment_set.order_by('submitted')

    @property
    def slug_generator(self):
        return self.title

class Comment(models.Model):
    COMMENT_TYPES = [
        ('C', _('comment')),
        ('T', _('trackback')),
        ('P', _('pingback')),
    ]
    entry = models.ForeignKey(Entry)
    author = models.CharField(_('Name'), max_length=16)
    author_uri = models.CharField(_('Website'), max_length=256)
    author_email = models.EmailField(_('Email'))
    body = models.TextField(_('Comment'), max_length=500)
    submitted = models.DateTimeField(default=datetime.now())
    type = models.CharField(_('Comment type'), max_length=1, choices=COMMENT_TYPES, default='C')

    class Admin:
        list_display = ('entry', 'formatted_author', 'body', 'submitted')

    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')

    def save(self):
        if self.author_uri[:7] != 'http://' and \
                self.author_uri[:8] != 'https://':
            self.author_uri = 'http://%s' % self.author_uri
        super(Comment, self).save()

    def get_absolute_url(self):
        position = Comment.objects.filter(entry=self.entry, submitted__lt=self.submitted).count() + 1
        return BLANGO_URL + 'entry/%s/#comment-%d' % (self.entry.slug, position)

    def __unicode__(self):
        return self.body

    @property
    def title(self):
        return mark_safe(_('Comment by "%s"') % self.author)

    @property
    def description(self):
        return self.body

    @short_description('author')
    def formatted_author(self):
        return ('%s <%s>' % (self.author, self.author_email))
