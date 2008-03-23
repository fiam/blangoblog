from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.db import connection
from django.core.paginator import QuerySetPaginator, InvalidPage

try:
    from django import newforms as forms
except ImportError:
    from django import forms

from datetime import date

from settings import LANGUAGE_CODE

from blango.models import *

def iso639_1(val):
    return val.split('-')[0]

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('author', 'author_uri', 'author_email', 'body')

    def save(self, entry):
        self.instance.entry = entry
        super(CommentForm, self).save()

def dates_for_language(language):
    cursor = connection.cursor()
    cursor.execute('''SELECT DISTINCT YEAR(published),MONTH(published) FROM
         blango_entry WHERE language_id = %d ORDER BY
         YEAR(published) DESC, MONTH(published) DESC
        ''' % language.id)
    return [date(row[0], row[1], 1) for row in cursor.fetchall()]

def list_view(request, lang, tag_slug, year, month, page):
    entries = Entry.objects.filter(draft=False).order_by('-published')
    base_url = request.path

    if page:
        base_url = base_url[:-1 * len(page) - 1]
    base_url += '%d/'

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        entries = entries.filter(tags=tag)
    if year and month:
        entries = entries.filter(published__year=year, published__month=month)

    if lang:
        blango_lang = lang + '/'
    else:
        lang = iso639_1(request.LANGUAGE_CODE)
        blango_lang = ''

    language = get_object_or_404(Language, iso639_1=lang)
    entries = entries.filter(language=language)

    dates = dates_for_language(language)

    tags = Tag.for_language(language)
    languages = Language.objects.all()

    paginator = QuerySetPaginator(entries, 5, base_url=base_url)
    page = paginator.page_or_404(page or 1)

    return render_to_response('blango/list.html', locals(),
            context_instance=RequestContext(request))

def entry_view(request, entry_slug):
    entry = get_object_or_404(Entry, slug=entry_slug)

    dates = dates_for_language(entry.language)
    tags = Tag.for_language(entry.language)

    comment_form = CommentForm()

    if request.method == 'POST':
        try:
            comment_form = CommentForm(request.POST)
            comment_form.save(entry)
            return HttpResponseRedirect(entry.get_absolute_url())
        except ValueError:
            pass

    return render_to_response('blango/entry.html', locals(),
            context_instance=RequestContext(request))
