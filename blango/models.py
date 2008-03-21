from django.db import models, connection
from django.contrib.auth.models import User
from django.contrib.markup.templatetags.markup import markdown
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from settings import BLANGO_URL

from datetime import datetime

class short_description(object):
    def __init__(self, desc):
        self.desc = desc
    def __call__(self, func):
        func.short_description = self.desc
        return func
            
def make_slug(klass, title):
    slug = slugify(title)[:50]
    retval = slug
    i = 2;
    while True:
        try:
            klass.objects.get(slug=retval)
            retval = slug[:49 - len(str(i))] + '-' + str(i)
            i += 1
        except klass.DoesNotExist:
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
        verbose_name = _('tags')

    def save(self):
        if not self.slug:
            self.slug = make_slug(Tag, self.name)
        super(Tag, self).save()

    def get_absolute_url(self):
        return BLANGO_URL + 'tag/%s/' % self.slug

    def __unicode__(self):
        return self.name

    @staticmethod
    def for_language(language):
        cursor = connection.cursor()
        cursor.execute('''SELECT DISTINCT t.tag_id FROM blango_entry_tags AS t
            JOIN blango_entry AS e ON e.id = t.entry_id WHERE e.language_id = %d
            ''' % language.id)
        return Tag.objects.filter(id__in=[t[0] for t in cursor.fetchall()])

class Entry(models.Model):
    title = models.CharField(max_length=65)
    slug = models.SlugField(max_length=65, blank=True)
    author = models.ForeignKey(User, blank=True)
    language = models.ForeignKey(Language, radio_admin=True)
    body = models.TextField()
    tags = models.ManyToManyField(Tag)
    body_html = models.TextField(blank=True)
    published = models.DateTimeField(default=datetime.now())
    translations = models.ManyToManyField('Entry', blank=True)
     
    class Admin:
        fields = (
            (_('Entry'), {'fields': ('title', 'body')}),
            (_('Tags'), {'fields': ('tags', )}),
            (_('Language'), {'fields': ('language', )}),
            (_('Date published'), {'fields': ('published', )}),
            (_('Published translations'), { 'fields': ('translations', )}),
        )
        list_display = ('title', 'language', 'formatted_tags', 'published')

    class Meta:
        verbose_name = _('entry')
        verbose_name_plural = _('entries')

    def __unicode__(self):
        return self.title

    def save(self):
        if not self.slug:
            self.slug = make_slug(Entry, self.title)
        if not self.author_id:
            self.author = User.objects.get(pk=1)
        self.body_html = markdown(self.body)
        super(Entry, self).save()

    def get_absolute_url(self):
        return BLANGO_URL + 'entry/%s/' % self.slug

    @short_description(_('tags'))
    def formatted_tags(self):
        return u', '.join(t.__unicode__() for t in self.tags.all())

    @property
    def description(self):
        return mark_safe(self.body)

class Comment(models.Model):
    entry = models.ForeignKey(Entry, related_name='comments')
    author = models.CharField(_('Name'), max_length=16)
    author_uri = models.CharField(_('Website'), max_length=256)
    author_email = models.EmailField(_('Email'))
    body = models.TextField(_('Comment'), max_length=500)
    submitted = models.DateTimeField(default=datetime.now())

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
