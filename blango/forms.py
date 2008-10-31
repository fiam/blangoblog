from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django import forms

from blango.models import Comment
from blango.magicforms import MagicModelForm


# This violates the DRY principe, but it's the only
# way I found for editing staff comments from
# the Django admin application

class CommentForm(MagicModelForm):
    author = forms.CharField(label=_('Name'), max_length=32)
    author_uri = forms.CharField(label=_('Website'), max_length=256, required=False)
    author_email = forms.EmailField(label=_('Email'), help_text=mark_safe('<span class="small">%s</span>' % _('(Won\'t be published)')))
    subscribed = forms.BooleanField(required=False, label='', help_text=mark_safe('<span class="medium">%s</span>' % _('Notify me of followup comments via e-mail')))

    class Meta:
        model = Comment
        fields = ('author', 'author_uri', 'author_email', 'body', 'subscribed')

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


class UserCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body', )

    def save(self, entry, request):
        self.instance.user = request.user
        self.instance.entry = entry
        super(UserCommentForm, self).save(entry)

