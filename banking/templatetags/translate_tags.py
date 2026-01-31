from django import template
from banking.translations import translate as _translate

register = template.Library()


@register.simple_tag(takes_context=True)
def t(context, key):
    """
    Tag de template pour traduire un texte
    Usage: {% t "Dashboard" %}
    """
    request = context.get('request')
    if request and request.user.is_authenticated and hasattr(request.user, 'profile'):
        lang = request.user.profile.language or 'fr'
    else:
        lang = 'fr'
    
    return _translate(key, lang)


@register.filter
def translate(key, lang='fr'):
    """
    Filtre pour traduire un texte
    Usage: {{ "Dashboard"|translate:user.profile.language }}
    """
    return _translate(key, lang)
