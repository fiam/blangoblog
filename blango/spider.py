#!/usr/bin/python

import urllib
import urllib2
import StringIO
import gzip
import re
import os
from tempfile import mkstemp
from htmlentitydefs import name2codepoint
from xmlrpclib import ServerProxy, Error

import sys

def is_absolute_link(link):
    return link.startswith('http://') or link.startswith('https://')

def hostname_from_uri(uri, http=True):
    if not is_absolute_link(uri):
        return None

    if http:
        return '/'.join(uri.split('/')[:3])

    return uri.split('/')[2]

def absolute_link(uri, link):
    if link is None:
        link = ''
    if is_absolute_link(link):
        return link

    if link[0] != '/':
        return '%s%s' % (hostname_from_uri(uri), link)


    return '%s/%s' % (uri, link)

class SpiderErrorHandler(urllib2.HTTPDefaultErrorHandler):
    def http_error_default(self, req, fp, code, msg, headers):
        result = urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)
        result.status = code

        return result

class BaseSpider(object):
    #XXX: Crashes if uri is utf8 string
    def __init__(self, uri):
        self.stream = None
        self.code = 0
        if is_absolute_link(uri):
            self.uri = uri
        else:
            self.uri = 'http://%s' % uri
        if self.uri.find('#') >= 0:
            self.uri = self.uri[:self.uri.find('#')]
        self.request = urllib2.Request(self.uri)
        self.request.add_header('User-Agent', 'Blango/0.1 +http://blango.net')
        self.request.add_header('Accept-encoding', 'gzip')
        self.opener = urllib2.build_opener()

    def _set_code(self, code):
        self.code = code

    def _require_fetch(self):
        if not self.uri:
            raise RuntimeError('URI value missing')
        if not self.code:
            self.fetch()
        return self.code == 200

    def _translate_entities(self):
        def repl(match):
            m = match.groups()[0]
            if m[0] == u'#':
                if m[1] == 'x':
                    return unichr(int(m[2:], 16))
                return unichr(int(m[1:]))
            if m.decode('utf8') in name2codepoint:
                return unichr(name2codepoint[m])
            return m
        r = re.compile('&([\w#]+);')
        self.data = r.sub(repl, self.data)

    def _to_unicode(self):
        encoding_match = re.compile('^<\?.*encoding=[\'"](.*?)[\'"].*\?>', re.I).match(self.data)
        if not encoding_match:
            encoding_match = re.compile('<meta.*?content=[\'"].*?charset=(.*?)[\'"]', re.I).search(self.data)
        if not encoding_match:
            encoding_match = re.compile(';.*charset=(.*)', re.I).search(self.stream.headers.get('Content-Type'))
        if encoding_match:
            encoding = encoding_match.groups()[0].lower()
        else:
            encoding = 'utf8'
        #Ignore invalid data
        newdata = ''
        while True:
            try:
                newdata += self.data.decode(encoding)
                break
            except UnicodeDecodeError, e:
                newdata += self.data[:e.start].decode(encoding)
                try:
                    if encoding in ('utf-8', 'utf8'):
                        fallback = 'latin1'
                    else:
                        fallback = 'utf8'
                    newdata += self.data[e.start:e.end].decode(fallback)
                except UnicodeDecodeError:
                    pass
                self.data = self.data[e.end:]

        self.data = newdata

    def fetch(self):
        try:
            try:
                self.stream = self.opener.open(self.request)
                self.data = self.stream.read()
                self.code = 200
            except urllib2.URLError:
                self.code = 600
                return ''
        except urllib2.HTTPError, e:
            self.code = e.code
            return u''

        if self.stream.headers.get('Content-Encoding', '') == 'gzip':
            iobuf = StringIO.StringIO(self.data)
            self.data = gzip.GzipFile(fileobj=iobuf).read()


        if self.is_text():
            self._to_unicode()
            self._translate_entities()
        else:
            return self.data

    def is_text(self):
        text_mimetypes = [ 'text/', 'application/xhtml+xml', 'application/xml' ]
        for t in text_mimetypes:
            if self.content_type.find(t) != -1:
                return True
        return False

    @property
    def content_type(self):
        if self.stream:
            return self.stream.headers.get('Content-Type', '')
        return ''

    def is_image(self):
        return self.stream and self.stream.headers['Content-Type'].find('image') == 0

class Spider(BaseSpider):
    def __init__(self, uri, data = ''):
        super(Spider, self).__init__(uri)
        self.data = data

    def pingback(self, source):
        if not self._require_fetch():
            return False
        pburi = self.stream.headers.get('X-Pingback')
        if not pburi:
            r = re.compile('<link.*?rel="pingback".*?href="([^"]+)" ?/?>', re.I)
            m = r.search(self.data)
            if not m:
                return False
            pburi = m.group(1)
        server = ServerProxy(pburi)
        try:
            server.pingback.ping(source, self.uri)
            return True
        except Error, v:
            return False

    def trackback(self, url, page_name='', title='', excerpt=''):
        if not self._require_fetch():
            print self.code
            return False

        r = re.compile('trackback:ping="([^"]+)"')
        m = r.search(self.data)
        if not m:
            return False
        tburi = m.group(1)
        t = Spider(tburi)
        t.request.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=utf-8')
        values = { 'title': title,
            'excerpt': excerpt,
            'url': url,
            'blog_name': page_name }
        data = urllib.urlencode(values)
        t.request = urllib2.Request(tburi, data)
        t.fetch()
        return t.data.find('<error>0</error>') != -1

    def backlinks(self, back):
        if not self._require_fetch():
            return False

        r = re.compile('<a.*?href="%s".*>' % back)
        return r.search(self.data) != None
