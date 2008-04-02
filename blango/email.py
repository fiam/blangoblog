from django.utils.translation import get_language, activate, ugettext as _
from django.conf import settings
from django.core.mail import send_mail

from blango.spider import hostname_from_uri

from hashlib import sha1
from locale import normalize

def send_subscribers_email(comment):
    BLANGO_URL = getattr(settings, 'BLANGO_URL')
    BLANGO_TITLE = getattr(settings, 'BLANGO_TITLE')
    recipients = comment.entry.comment_set.filter(subscribed=True).exclude(pk=comment.pk)
    lang = get_language()
    newlang = normalize(comment.entry.language.iso639_1 + '.UTF-8')
    activate(newlang) 
    subject = _('New comment on %s') % comment.entry.title
    from_email = 'noreply@%s' % hostname_from_uri(BLANGO_URL, http=False)
    for r in recipients:
        message = _('''
        A new comment has been posted in %(entry)s. You can read it at %(uri)s

        
        You're receiving this email because you subscribed to "%(entry)s"
        in %(blog_title)s. If you no longer want to received any followups
        just visit %(unsubscribe)s
        ''') % { 'entry': comment.entry.title, 'uri': comment.get_absolute_url(),
                'blog_title': BLANGO_TITLE,
                'unsubscribe': BLANGO_URL + 'unsubscribe/%s/%s/' % \
                    (r.id, sha1(r.author_email).hexdigest()) }
        
        send_mail(subject, message, from_email, [r.author_email], fail_silently=True)
        
    activate(lang) 
