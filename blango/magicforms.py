from Crypto.Cipher import ARC4
import cPickle as pickle
from datetime import datetime, timedelta
from base64 import urlsafe_b64encode as b64encode
from base64 import urlsafe_b64decode as b64decode

try:
    from django import newforms as forms
except ImportError:
    from django import forms

from django.conf import settings
from django.utils.translation import ugettext as _

MIN_WAIT_SECONDS = 5
MAX_WAIT_SECONDS = 3600

def clean_magic(self):
    m = self.cleaned_data['magic']
    arc4 = ARC4.new(settings.SECRET_KEY)
    try:
        plain = arc4.decrypt(b64decode(str(m)))
        data = pickle.loads(plain)
        before = data['curtime']
        remote_ip = data['remote_ip']
        unique_id = data['unique_id']
    except (TypeError, pickle.UnpicklingError, KeyError):
        raise forms.ValidationError(_('Invalid security token'))

    if remote_ip != self.remote_ip or unique_id != self.unique_id:
        raise forms.ValidationError(_('Invalid security token'))

    try:
        curdelta = datetime.now() - before
    except TypeError:
        raise forms.ValidationError(_('Invalid security token'))

    mindelta = timedelta(seconds=MIN_WAIT_SECONDS)
    if curdelta < mindelta:
        d = mindelta - curdelta
        raise forms.ValidationError(_('Wait for another %.2f seconds before submitting this form') % (d.seconds + float(d.microseconds)/1000000))

    if curdelta > timedelta(seconds=MAX_WAIT_SECONDS):
        raise forms.ValidationError(_('This form has expired. Reload the page to get a new one'))

    return m

def set_initial_magic(self):
    if not self.data.get('magic'):
        arc4 = ARC4.new(settings.SECRET_KEY)
        data = {
            'curtime': datetime.now(),
            'remote_ip': self.remote_ip,
            'unique_id': self.unique_id,
        }
        plain = pickle.dumps(data)
        self.initial['magic'] = b64encode(arc4.encrypt(plain))

class MagicForm(forms.Form):
    magic = forms.CharField(max_length=1024, widget=forms.HiddenInput())
    author_bogus_name = forms.CharField(required=False, max_length=0, label='', widget=forms.TextInput(attrs={ 'style': 'display:none'}))

    def __init__(self, remote_ip, unique_id, *args, **kwargs):
        super(MagicForm, self).__init__(*args, **kwargs)
        self.remote_ip = remote_ip
        self.unique_id = unique_id
        set_initial_magic(self)

    def clean_magic(self):
        return clean_magic(self)

class MagicModelForm(forms.ModelForm):
    magic = forms.CharField(max_length=1024, widget=forms.HiddenInput())
    author_bogus_name = forms.CharField(required=False, max_length=0, label='', widget=forms.TextInput(attrs={ 'style': 'display:none'}))

    def __init__(self, remote_ip, unique_id, *args, **kwargs):
        super(MagicModelForm, self).__init__(*args, **kwargs)
        self.remote_ip = remote_ip
        self.unique_id = unique_id
        set_initial_magic(self)

    def clean_magic(self):
        return clean_magic(self)

