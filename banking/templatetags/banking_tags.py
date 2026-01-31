from django import template
from banking.utils import get_currency_symbol

register = template.Library()

@register.filter
def currency_symbol(currency_code):
    """Retourne le symbole de la devise"""
    return get_currency_symbol(currency_code)


@register.filter
def translate_account_type(account_type, lang='fr'):
    """Traduit le type de compte"""
    translations = {
        'Compte Courant': {'fr': 'Compte Courant', 'en': 'Checking Account', 'es': 'Cuenta Corriente', 'it': 'Conto Corrente', 'pl': 'Rachunek Bieżący'},
        'Compte Épargne': {'fr': 'Compte Épargne', 'en': 'Savings Account', 'es': 'Cuenta de Ahorros', 'it': 'Conto di Risparmio', 'pl': 'Rachunek Oszczędnościowy'},
    }
    if account_type in translations:
        return translations[account_type].get(lang, account_type)
    return account_type


@register.filter
def translate_transaction_type(transaction_type, lang='fr'):
    """Traduit le type de transaction"""
    translations = {
        'Dépôt': {'fr': 'Dépôt', 'en': 'Deposit', 'es': 'Depósito', 'it': 'Deposito', 'pl': 'Wpłata'},
        'Retrait': {'fr': 'Retrait', 'en': 'Withdrawal', 'es': 'Retiro', 'it': 'Prelievo', 'pl': 'Wypłata'},
        'Virement': {'fr': 'Virement', 'en': 'Transfer', 'es': 'Transferencia', 'it': 'Bonifico', 'pl': 'Przelew'},
        'Paiement de facture': {'fr': 'Paiement de facture', 'en': 'Bill Payment', 'es': 'Pago de Factura', 'it': 'Pagamento Bolletta', 'pl': 'Opłata Rachunku'},
        'Achat TPV': {'fr': 'Achat TPV', 'en': 'POS Purchase', 'es': 'Compra TPV', 'it': 'Acquisto POS', 'pl': 'Zakup POS'},
        'Achat en ligne': {'fr': 'Achat en ligne', 'en': 'Online Purchase', 'es': 'Compra en Línea', 'it': 'Acquisto Online', 'pl': 'Zakup Online'},
    }
    if transaction_type in translations:
        return translations[transaction_type].get(lang, transaction_type)
    return transaction_type


@register.filter
def translate_text(text, lang='fr'):
    """Traduit un texte complexe avec pattern matching"""
    from banking.translations import translate
    
    if not text:
        return text
    
    # Patterns de traduction pour les descriptions composées
    patterns = {
        'Virement interne depuis': translate('Virement interne depuis', lang),
        'Virement interne vers': translate('Virement interne vers', lang),
        'Virement vers': translate('Virement vers', lang),
        'Compte Courant': translate('Checking Account', lang),
        'Compte Épargne': translate('Savings Account', lang),
        'Virement électronique': translate('Virement électronique', lang),
        'Paiement de facture': translate('Paiement de facture', lang),
        'Achat en magasin': translate('Achat en magasin', lang),
        'Transaction d\'achat': translate('Transaction d\'achat', lang),
        'Bénéficiaire': translate('Beneficiary', lang),
    }
    
    # Remplacer tous les patterns trouvés
    result = text
    for french, translation in patterns.items():
        result = result.replace(french, translation)
    
    return result
