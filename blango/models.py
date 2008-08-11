from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify, capfirst, force_escape
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.safestring import mark_safe

from settings import BLANGO_URL, BLANGO_TITLE
from blango.spider import Spider
from blango.email import send_subscribers_email

from markdown import markdown

from datetime import datetime, timedelta
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

    class Meta:
        verbose_name = _('language')
        verbose_name_plural = _('languages')

    def __unicode__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField('Tag name', max_length=32)
    slug = models.SlugField(blank=True)

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
        return Tag.objects.filter(entry__language=language).distinct()

class PublishedEntryManager(models.Manager):
    def get_query_set(self):
        return super(PublishedEntryManager, self).get_query_set().filter(draft=False, pub_date__lte=datetime.now())

class Entry(models.Model):
    title = models.CharField(_('title'), max_length=65)
    slug = models.SlugField(max_length=65, blank=True)
    author = models.ForeignKey(User, blank=True)
    language = models.ForeignKey(Language, verbose_name=_('language'))
    body = models.TextField(_('body'))
    tags = models.ManyToManyField(Tag, verbose_name=_('tags'))
    body_html = models.TextField(blank=True)
    pub_date = models.DateTimeField(_('Publication date'), default=datetime.now)
    draft = models.BooleanField(_('Save as draft (don\'t publish it yet)'), default=False)
    translations = models.ManyToManyField('Entry', blank=True, verbose_name=_('translations'))
    allow_comments = models.BooleanField(_('Allow new comments to be posted'), default=True)

    objects = models.Manager()
    published = PublishedEntryManager()

    class Meta:
        verbose_name = _('entry')
        verbose_name_plural = _('entries')

    def __unicode__(self):
        return self.title

    def ping(self):
        r = re.compile('<a.*?href=["\'](.*?)["\'].*?>', re.I | re.S)
        for anchor in r.finditer(self.body_html):
            link = anchor.group(1)
            if link.startswith(BLANGO_URL):
                continue
            s = Spider(link)
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
        published_now = False
        if not self.draft and self.pub_date < datetime.now() + timedelta(seconds=5):
            if not self.pk or Entry.objects.get(pk=self.pk).draft != self.draft:
                self.pub_date = datetime.now()
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
        return mark_safe(self.body_html)

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
    author = models.CharField(_('Name'), max_length=16, blank=True)
    author_uri = models.CharField(_('Website'), max_length=256, blank=True)
    author_email = models.EmailField(_('Email'), blank=True)
    body = models.TextField(_('Comment'), max_length=1000)
    submitted = models.DateTimeField(default=datetime.now)
    type = models.CharField(_('Comment type'), max_length=1, choices=COMMENT_TYPES, default='C')
    user = models.ForeignKey(User, default=None, null=True, blank=True)
    subscribed = models.BooleanField(_('Notify me of followup comments via e-mail'), default=False)

    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')

    def save(self):
        if self.author_uri and \
                not self.author_uri.startswith('http://') and \
                not self.author_uri.startswith('https://'):
            self.author_uri = 'http://%s' % self.author_uri
        super(Comment, self).save()
        send_subscribers_email(self)

    def get_absolute_url(self):
        position = Comment.objects.filter(entry=self.entry, submitted__lt=self.submitted).count() + 1
        return BLANGO_URL + 'entry/%s/#comment-%d' % (self.entry.slug, position)

    def __unicode__(self):
        return self.body

    @property
    def author_name(self):
        if self.user is not None:
            return self.user.username
        
        return self.author

    @property
    def author_link(self):
        if self.user is not None:
            return mark_safe('<a href="%s">%s</a>' % \
                    (BLANGO_URL, self.author_name))

        if self.author_uri:
            return mark_safe('<a rel="external nofollow" href="%s">%s</a>' % \
                    (self.author_uri, force_escape(self.author_name)))

        return mark_safe(force_escape(self.author))
    
    @property
    def web_title(self):
        return mark_safe('%s %s %s' % \
            (capfirst(ugettext(self.get_type_display())), ugettext('by'), self.author_link))

    @property
    def title(self):
        return mark_safe('%s %s %s' % \
            (capfirst(ugettext(self.get_type_display())), ugettext('by'), self.author_name))

    @property
    def description(self):
        return self.body

    @short_description('author')
    def formatted_author(self):
        if self.user is not None:
            return ('%s <%s>' % (self.user.username, self.user.email))
        return ('%s <%s>' % (self.author, self.author_email))
