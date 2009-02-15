from blango.models import *

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

admin.site.register(Language)

class TagAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ['name'] }),
    )

admin.site.register(Tag, TagAdmin)

class EntryAdmin(admin.ModelAdmin):
    class Media:
        js = ( 'js/wmd/wmd.js', )

    fieldsets = (
        (_('Entry'), {'fields': ('title', 'body')}),
        (_('Tags'), {'fields': ('tags', )}),
        (_('Language'), {'fields': ('language', )}),
        (_('Date published'), {'fields': ('pub_date', )}),
        (_('Options'), { 'fields': ('draft', 'allow_comments')}),
        (_('Published translations'), { 'fields': ('translations', )}),
        (_('This entry is a follow-up to'), { 'fields': ('follows', )}),
    )

    radio_fields = {'language': admin.HORIZONTAL}
    filter_horizontal = ('tags', 'translations')

    list_display = ('title', 'language', 'formatted_tags', 'pub_date')

    def save_form(self, request, form, change):
        form.instance.author = request.user
        return super(EntryAdmin, self).save_form(request, form, change)

admin.site.register(Entry, EntryAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('entry', 'formatted_author', 'body', 'submitted')

admin.site.register(Comment, CommentAdmin)
