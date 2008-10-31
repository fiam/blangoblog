from datetime import datetime, timedelta

from django import template
from django.db import connection

from blango.models import Tag, EntryHit

register = template.Library()

@register.tag
def tagcloud(parser, token):
    try:
        tag_name, period, min_em, max_em = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('%s tag requires 3 arguments' %
            token.split_contents()[0])

    return TagCloudNode(period, min_em, max_em)

class TagCloudNode(template.Node):
    DAYS = {
        'd': 1,
        'w': 7,
        'm': 30,
        'y': 365,
    }
    def __init__(self, period, min_em, max_em):
        self.period = template.Variable(period)
        self.min_em = template.Variable(min_em)
        self.max_em = template.Variable(max_em)

    def render(self, ctx):
        max_em = float(self.max_em.resolve(ctx))
        min_em = float(self.min_em.resolve(ctx))
        period = self.period.resolve(ctx)

        try:
            days = self.DAYS[period.lower()]
        except KeyError:
            raise template.TemplateSyntaxError('Invalid period '
                '(valid choices are d, w, m and y')

        d = unicode(datetime.now() - timedelta(days=days))
        cursor = connection.cursor()
        cursor.execute('SELECT t.id, t.name, t.slug, COUNT(et.tag_id) FROM '
            'blango_entryhit h JOIN blango_entry_tags et USING (entry_id) '
            'JOIN blango_tag t ON et.tag_id = t.id WHERE h."when" > \'%s\''
            'GROUP BY t.id,t.name, t.slug ORDER BY t.name;' % d)

        max_count = 0
        tags = []
        markup = []
        for row in cursor.fetchall():
            tag  = Tag(*row[:-1])
            count = int(row[-1])
            max_count = max(count, max_count)
            tags.append((tag, count))

        cursor.close()
        for tag, count in tags:
            markup.append('<a title="%s" class="tag" href="%s" '
                'style="font-size:%fem">%s</a>' % \
                (tag.name, tag.get_absolute_url(),
                max(min_em, max_em * count / max_count),
                tag.name))

        return ' '.join(markup)
