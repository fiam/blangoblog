from blango.models import *

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

admin.site.register(Language)

class TagAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ['name'] }),
    )

admin.site.register(Tag, TagAdmin)

class EntryAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Entry'), {'fields': ('title', 'body')}),
        (_('Tags'), {'fields': ('tags', )}),
        (_('Language'), {'fields': ('language', )}),
        (_('Date published'), {'fields': ('pub_date', )}),
        (_('Options'), { 'fields': ('draft', 'allow_comments')}),
        (_('Published translations'), { 'fields': ('translations', )}),
    )

    radio_fields = {'language': admin.HORIZONTAL}
    filter_horizontal = ('tags', 'translations')

    list_display = ('title', 'language', 'formatted_tags', 'pub_date')

admin.site.register(Entry, EntryAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('entry', 'formatted_author', 'body', 'submitted')

admin.site.register(Comment, CommentAdmin)
