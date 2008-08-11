from datetime import datetime, timedelta

from django import template
from blango.models import Entry
from django.db.models import Q
from django.db import connection

register = template.Library()

def truncate(value, max_len):
    if len(value) < max_len:
        return value

    return value[:max_len] + '&hellip;'

@register.simple_tag
def popentries(value):
    v = value.strip('"').lower()
    if v == 'w':
        days = 5
    elif v == 'm':
        days = 30
    elif v == 'y':
        days = 365

    markup = []
    d = unicode(datetime.now() - timedelta(days=days))
    cursor = connection.cursor()
    cursor.execute('SELECT entry_id FROM blango_entryhit GROUP BY entry_id ORDER BY COUNT(entry_id) DESC LIMIT 5')
    for row in cursor.fetchall():
        entry = Entry.objects.get(pk=row[0])
        markup.append(u'<dd><a href="%s">%s</a></dd>' % (entry.get_absolute_url(), truncate(entry.title, 35)))
    
    return ''.join(markup)
