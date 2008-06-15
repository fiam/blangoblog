from django.conf import settings

def blango_config(request):
    return {
        'blango_url': settings.BLANGO_URL,
        'blango_title': settings.BLANGO_TITLE,
        'blango_subtitle': settings.BLANGO_SUBTITLE,
        'blango_media': settings.BLANGO_MEDIA,
    }
