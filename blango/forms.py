from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django import forms

from blango.models import Comment
from blango.jsforms import JSModelForm


# This violates the DRY principe, but it's the only
# way I found for editing staff comments from
# the Django admin application

class CommentForm(JSModelForm):
    author = forms.CharField(label=_('Name'), max_length=256)
    author_uri = forms.CharField(label=_('Website'), max_length=256, required=False)
    author_email = forms.EmailField(label=_('Email'), help_text=mark_safe('<span class="small">%s</span>' % _('(Won\'t be published)')))

    class Meta:
        model = Comment
        fields = ('author', 'author_uri', 'author_email', 'body')

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

    def save(self, entry):
        self.instance.user = self.user
        self.instance.entry = entry
        super(UserCommentForm, self).save(entry)

