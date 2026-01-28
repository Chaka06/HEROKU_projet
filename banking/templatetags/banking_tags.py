from django import template
from banking.utils import get_currency_symbol

register = template.Library()

@register.filter
def currency_symbol(currency_code):
    """Retourne le symbole de la devise"""
    return get_currency_symbol(currency_code)
