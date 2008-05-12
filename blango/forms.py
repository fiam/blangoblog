from Crypto.Cipher import ARC4
import cPickle as pickle
from datetime import datetime, timedelta
from base64 import urlsafe_b64encode as b64encode
from base64 import urlsafe_b64decode as b64decode

from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django.conf import settings

try:
    from django import newforms as forms
except ImportError:
    from django import forms

from blango.models import Comment

WAIT_SECONDS = 5

# This violates the DRY principe, but it's the only
# way I found for editing staff comments from
# the Django admin application

class CommentForm(forms.ModelForm):
    author = forms.CharField(label=_('Name'), max_length=16)
    author_uri = forms.CharField(label=_('Website'), max_length=256, required=False)
    author_email = forms.EmailField(label=_('Email'), help_text=mark_safe('<span class="small">%s</span>' % _('(Won\'t be published)')))
    subscribed = forms.BooleanField(label='', help_text=mark_safe('<span class="medium">%s</span>' % _('Notify me of followup comments via e-mail')))
    magic = forms.CharField(max_length=124, widget=forms.HiddenInput())

    class Meta:
        model = Comment
        fields = ('author', 'author_uri', 'author_email', 'body', 'subscribed')

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        if not self.data.get('magic'):
            arc4 = ARC4.new(settings.SECRET_KEY)
            curtime = pickle.dumps(datetime.now())
            self.initial['magic'] = b64encode(arc4.encrypt(curtime))

    def save(self, entry):
        self.instance.entry = entry
        super(CommentForm, self).save()

    def clean_author(self):
        author = self.cleaned_data['author']
        try:
            User.objects.get(username=author)
            raise forms.ValidationError(_('This username belongs to a registered user'))
        except User.DoesNotExist:
            return author

    def clean_magic(self):
        m = self.cleaned_data['magic']
        arc4 = ARC4.new(settings.SECRET_KEY)
        curtime = datetime.now()
        try:
            d = b64decode(str(m))
            before = pickle.loads(arc4.decrypt(d))
            curdelta = curtime - before
        except TypeError:
            raise forms.ValidationError('This form was not generated for this site')

        mindelta = timedelta(seconds=WAIT_SECONDS)
        if curdelta < mindelta:
            d = mindelta - curdelta
            raise forms.ValidationError('Wait for another %.2f seconds before submitting this form' % (d.seconds + float(d.microseconds)/1000000))

        return m

class UserCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body', )

    def save(self, entry, request):
        self.instance.user = request.user
        self.instance.entry = entry
        super(UserCommentForm, self).save(entry)

