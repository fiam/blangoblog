from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.db import connection
from django.core.paginator import QuerySetPaginator, InvalidPage
from django.utils.translation import ugettext as _

from blango.spider import Spider, hostname_from_uri, is_absolute_link

from xml.etree import cElementTree


from datetime import date

from settings import LANGUAGE_CODE

from blango.models import *
from blango.forms import *

def iso639_1(val):
    return val.split('-')[0]

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

    paginator = QuerySetPaginator(entries, 5, base_url=base_url, page_suffix='%d/')
    page = paginator.page_or_404(page or 1)

    return render_to_response('blango/list.html', locals(),
            context_instance=RequestContext(request))

def entry_view(request, entry_slug):
    entry = get_object_or_404(Entry, slug=entry_slug)

    dates = dates_for_language(entry.language)
    tags = Tag.for_language(entry.language)

    if request.user.is_authenticated():
        comment_form = UserCommentForm()
    else:
        comment_form = CommentForm()

    if request.method == 'POST':
        try:
            if request.user.is_authenticated():
                comment_form = UserCommentForm(request.POST)
                comment_form.save(entry, request)
            else:
                comment_form = CommentForm(request.POST)
                comment_form.save(entry)
            return HttpResponseRedirect(entry.get_absolute_url())
        except ValueError:
            pass

    return render_to_response('blango/entry.html', locals(),
            context_instance=RequestContext(request))

def trackback_view(request, entry_id):
    title = request.POST.get('title')
    excerpt = request.POST.get('excerpt', '')
    url = request.POST.get('url')
    blog_name = request.POST.get('blog_name')

    if not url:
        return HttpResponse('''<?xml version="1.0" encoding="utf-8"?>
                <response>
                    <error>1</error>
                    <message>No URL specified</message>
                </response>''', mimetype='text/xml')
    if len(url) > 1024:
        return HttpResponse('''<?xml version="1.0" encoding="utf-8"?>
                <response>
                    <error>1</error>
                    <message>Entity Too Large</message>
                </response>''', mimetype='text/xml')

    if not is_absolute_link(url):
        return HttpResponse('''<?xml version="1.0" encoding="utf-8"?>
                <response>
                    <error>1</error>
                    <message>URL must match https?://.*</message>
                </response>''', mimetype='text/xml')
    
    entry = get_object_or_404(Entry, pk=entry_id)

    try:
        Comment.objects.get(entry=entry, type__in=['T', 'P'], author_uri=url)
        return HttpResponse('''<?xml version="1.0" encoding="utf-8"?>
                <response>
                    <error>1</error>
                    <message>Trackback already registered</message>
                </response>''', mimetype='text/xml')
    except Comment.DoesNotExist:
        pass

    s = Spider(url)
    if not s.backlinks(entry.get_absolute_url()):
        return HttpResponse('''<?xml version="1.0" encoding="utf-8"?>
                <response>
                    <error>1</error>
                    <message>URL doesn't link back</message>
                </response>''', mimetype='text/xml')

    if not blog_name:
        blog_name = url.split('/')[2]

    if title:
        excerpt = '%s\n\n%s' % (title, excerpt)

    Comment.objects.create(entry=entry, author=blog_name, author_uri=url, body=excerpt, type='T')

    return HttpResponse('''<?xml version="1.0" encoding="utf-8"?>
                <response>
                    <error>0</error>
                </response>''')

def xmlrpc_view(request):
    return XmlRpcDispatcher(request).dispatch()

class XmlRpcDispatcher(object):
    @staticmethod
    def fault(code, msg):
        return HttpResponse('''<?xml version="1.0"?>
        <methodResponse>
            <fault>
                <value>
                    <struct>
                        <member>
                            <name>faultCode</name>
                            <value><int>%d</int></value>
                        </member>
                        <member>
                            <name>faultString</name>
                            <value><string>%s</string></value>
                        </member>
                    </struct>
                </value>
            </fault>
        </methodResponse>''' % (code, msg), mimetype='text/xml')
    @staticmethod
    def pingback_reply(msg):
        return HttpResponse('''<?xml version="1.0"?>
        <methodResponse>
            <params>
                <param>
                    <value>
                        <string>%s</string>
                    </value>
                </param>
            </params>
        </methodResponse>''' % msg, mimetype='text/xml')
    def __init__(self, request):
        self.request = request

    def dispatch(self):
        if not self.request.raw_post_data:
            return HttpResponse('')

        self.tree = cElementTree.fromstring(self.request.raw_post_data.strip())
        method_name = self.tree.find('methodName').text
        method = getattr(self, method_name.replace('.', '_'), None)
        if method:
            self.params = []
            for v in self.tree.findall('params/param/value'):
                try:
                    child = v.getchildren()[0]
                except KeyError:
                    self.params.append(v.text) #string
                if child.tag == 'string':
                    self.params.append(child.text)
                if child.tag in ('int', 'i4'):
                    self.params.append(int(child.text))
                if child.tag == 'boolean':
                    self.params.append(child.text == '1')
                if child.tag == 'double':
                    self.params.append(float(chold.text))
                # Missing types, but for now, only strings are needed
            return method()
        else:
            return XmlRpcDispatcher.fault(1, 'Invalid method')

    def pingback_ping(self):
        source = self.params[0]
        target = self.params[1]
        slug = target.split('/')[-2]
        try:
            entry = Entry.objects.get(slug=slug)
        except Entry.DoesNotExist:
            return XmlRpcDispatcher.fault(33, 'The specified URI cannot be used as target')

        try:
            Comment.objects.get(entry=entry, type__in=['P', 'T'], author_uri=source)
            return XmlRpcDispatcher.fault(48, 'The pingback has already been registered')
        except Comment.DoesNotExist:
            pass

        s = Spider(source)
        if not s.backlinks(target):
            if s.code == 200:
                return XmlRpcDispatcher.fault(17, 'The source URI does not contain a link to the target URI')

            return XmlRpcDispatcher.fault(16, 'The source URI does not exist')

        Comment.objects.create(entry=entry, type='P',
                author=hostname_from_uri(source, http=False),
                author_uri=source, body='')

        return XmlRpcDispatcher.pingback_reply('Pingback stored')

