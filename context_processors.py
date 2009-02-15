from django.conf import settings

def blango_config(request):
    return {
        'BLANGO_URL': settings.BLANGO_URL,
        'BLANGO_TITLE': settings.BLANGO_TITLE,
        'BLANGO_SUBTITLE': settings.BLANGO_SUBTITLE,
        'BLANGO_THEME': settings.BLANGO_THEME,
        'BLANGO_MEDIA_URL': settings.BLANGO_MEDIA_URL,
    }
