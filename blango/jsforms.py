import random

from django import forms
from django.forms.util import flatatt
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

OPERATIONS = '/*+^'
SCRIPT = '''
    <script type="text/javascript">
        function __operate_js_value() {
            var js = document.getElementById('id_js')
            var js2 = document.getElementById('id_js2')
            js2.value = Math.floor(eval(js.value));
        }
        if (window.addEventListener){
            window.addEventListener('load', __operate_js_value, false);
        } else if (el.attachEvent){
            windo.attachEvent('onload', __operate_js_value);
        }
    </script>
'''

class JSHiddenInput(forms.HiddenInput):
    def render(self, name, value, attrs=None):
        value = super(JSHiddenInput, self).render(name, value, attrs)
        return mark_safe('<script type="text/javascript">document.write(\'%s\')</script>' % value)

class JSHiddenCopyInput(forms.HiddenInput):
    def render(self, name, value, attrs=None):
        value = super(JSHiddenCopyInput, self).render(name, value, attrs)
        return mark_safe(value + SCRIPT)

def initialize_js_form(form):
    if not form.data.get('js'):
        operand1 = random.randint(10, 99)
        operand2 = random.randint(10, 99)
        value = '%s%s%s' % (operand1, random.choice(OPERATIONS), operand2)
        form.initial['js'] = value

def operate(value):
    operand1 = int(value[:2])
    operand2 = int(value[-2:])
    operation = value[2]

    if operation == '+':
        return operand1 + operand2
    elif operation == '-':
        return operand1 - operand2
    elif operation == '*':
        return operand1 * operand2
    elif operation == '/':
        return operand1 / operand2
    elif operation == '^':
        return operand1 ** operand2
    else:
        raise ValueError('Invalid operation')

def clean_js_form(form):
    cleaned_data = form.cleaned_data
    js = cleaned_data.get('js')
    js2 = cleaned_data.get('js2')

    is_valid = False
    if js and js2:
        try:
            js_value = operate(js)
            js2_value = int(js2)
        except (TypeError, ValueError, IndexError):
            pass
        else:
            is_valid = (js_value == js2_value)

    if not is_valid:
        raise forms.ValidationError(_('Invalid security token. Please, enable Javascript to use this form.'))

    return cleaned_data

class JSForm(forms.Form):
    js = forms.CharField(max_length=32, widget=forms.HiddenInput())
    js2 = forms.CharField(max_length=32, widget=forms.HiddenInput(), required=False)
    def __init__(self, *args, **kwargs):
        super(JSForm, self).__init__(*args, **kwargs)
        initialize_js_form(self)
    
    def clean(self):
        return clean_js_form(self)

class JSModelForm(forms.ModelForm):
    js = forms.CharField(required=False, max_length=32, widget=JSHiddenInput())
    js2 = forms.CharField(max_length=32, widget=JSHiddenCopyInput(), required=False)
    def __init__(self, *args, **kwargs):
        super(JSModelForm, self).__init__(*args, **kwargs)
        initialize_js_form(self)

    def clean(self):
        return clean_js_form(self)
