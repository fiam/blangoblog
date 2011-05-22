import random

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

class JSHiddenInput(forms.HiddenInput):
    def render(self, name, value, attrs=None):
        value = super(JSHiddenInput, self).render(name, value, attrs)
        return mark_safe('<script type="text/javascript">document.write(\'%s\')</script>' % value)

def initialize_js_form(form):
    if not form.data.get('js'):
        form.initial['js'] = random.randint(1, 10000)

def clean_js(form):
    js = form.data.get('js')
    if not js:
        raise forms.ValidationError(_('Invalid security token. Please, enable Javascript to use this form.'))

class JSForm(forms.Form):
    js = forms.CharField(max_length=32, widget=forms.HiddenInput())
    def __init__(self, *args, **kwargs):
        super(JSForm, self).__init__(*args, **kwargs)
        initialize_js_form(self)
    
    def clean_js2(self):
        clean_js(self)

class JSModelForm(forms.ModelForm):
    js = forms.CharField(required=False, max_length=32, widget=JSHiddenInput())
    def __init__(self, *args, **kwargs):
        super(JSModelForm, self).__init__(*args, **kwargs)
        initialize_js_form(self)

    def clean_js(self):
        clean_js(self)
