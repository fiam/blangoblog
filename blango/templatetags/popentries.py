from datetime import datetime, timedelta

from django import template
from blango.models import Entry
from django.db.models import Q
from django.db import connection

register = template.Library()

DAYS = {
    'd': 1,
    'w': 7,
    'm': 30,
    'y': 365,
}

def truncate(value, max_len):
    if len(value) < max_len:
        return value

    return value[:max_len] + '&hellip;'

@register.simple_tag
def popentries(value):
    try:
        days = DAYS[value.lower()]
    except KeyError:
        raise template.TemplateSyntaxError('Invalid period '
            ' (valid choices are d, w, m and y')

    markup = []
    d = unicode(datetime.now() - timedelta(days=days))
    cursor = connection.cursor()
    cursor.execute('SELECT entry_id FROM blango_entryhit '
        'WHERE "when" > \'%s\' GROUP BY entry_id ORDER BY '
        'COUNT(entry_id) DESC LIMIT 5' % d)
    for row in cursor.fetchall():
        entry = Entry.objects.get(pk=row[0])
        markup.append(u'<dd><a href="%s">%s</a></dd>' %
            (entry.get_absolute_url(), truncate(entry.title, 35)))
    
    cursor.close()
    return ''.join(markup)
