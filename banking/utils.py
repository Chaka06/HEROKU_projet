import random
import string


# Codes pays IBAN avec longueur
IBAN_COUNTRY_CODES = {
    'France': ('FR', 27),
    'Italie': ('IT', 27),
    'Allemagne': ('DE', 22),
    'Espagne': ('ES', 24),
    'Royaume-Uni': ('GB', 22),
    'Suisse': ('CH', 21),
    'Pays-Bas': ('NL', 18),
    'États-Unis': ('US', 0),  # USA n'utilise pas IBAN
    'Canada': ('CA', 0),  # Canada n'utilise pas IBAN
    'Chine': ('CN', 0),  # Chine n'utilise pas IBAN
    'Japon': ('JP', 0),  # Japon n'utilise pas IBAN
    'Inde': ('IN', 0),  # Inde n'utilise pas IBAN
    'Australie': ('AU', 0),  # Australie n'utilise pas IBAN
    'Singapour': ('SG', 0),  # Singapour n'utilise pas IBAN
    'Arabie Saoudite': ('SA', 24),
    'Émirats Arabes Unis': ('AE', 23),
    'Qatar': ('QA', 29),
    'Afrique du Sud': ('ZA', 0),  # N'utilise pas IBAN standard
    'Brésil': ('BR', 0),  # N'utilise pas IBAN
    'Finlande': ('FI', 18),
}


def generate_account_number():
    """Génère un numéro de compte aléatoire"""
    return ''.join(random.choices(string.digits, k=11))


def generate_iban(country, bank_code=None):
    """
    Génère un IBAN selon le pays
    
    Args:
        country: Nom du pays (ex: 'France', 'Italie')
        bank_code: Code de la banque (optionnel)
    
    Returns:
        IBAN formaté ou numéro de compte si le pays n'utilise pas IBAN
    """
    country_data = IBAN_COUNTRY_CODES.get(country, ('FR', 27))
    country_code, iban_length = country_data
    
    # Si le pays n'utilise pas IBAN (longueur = 0)
    if iban_length == 0:
        # Retourner un numéro de compte standard
        return generate_account_number()
    
    # Générer les chiffres aléatoires
    # IBAN = Code pays (2) + Clé de contrôle (2) + Identifiant bancaire + Numéro de compte
    check_digits = ''.join(random.choices(string.digits, k=2))
    remaining_length = iban_length - 4  # Moins le code pays et la clé
    account_part = ''.join(random.choices(string.digits, k=remaining_length))
    
    return f"{country_code}{check_digits}{account_part}"


def get_currency_for_country(country):
    """Retourne la devise par défaut selon le pays"""
    currency_map = {
        'France': 'EUR',
        'Italie': 'EUR',
        'Allemagne': 'EUR',
        'Espagne': 'EUR',
        'Pays-Bas': 'EUR',
        'Finlande': 'EUR',
        'Royaume-Uni': 'GBP',
        'Suisse': 'CHF',
        'États-Unis': 'USD',
        'Canada': 'CAD',
        'Chine': 'CNY',
        'Japon': 'JPY',
        'Inde': 'INR',
        'Australie': 'AUD',
        'Singapour': 'SGD',
        'Arabie Saoudite': 'SAR',
        'Émirats Arabes Unis': 'AED',
        'Qatar': 'SAR',  # Qatar utilise le Riyal Qatari mais on met SAR pour simplifier
        'Afrique du Sud': 'USD',  # Simplifié
        'Brésil': 'BRL',
    }
    return currency_map.get(country, 'EUR')


def get_currency_symbol(currency_code):
    """Retourne le symbole de la devise"""
    symbols = {
        'EUR': '€',
        'USD': '$',
        'GBP': '£',
        'CHF': 'CHF',
        'JPY': '¥',
        'CNY': '¥',
        'CAD': '$',
        'AUD': '$',
        'INR': '₹',
        'BRL': 'R$',
        'SAR': 'ر.س',
        'AED': 'د.إ',
        'SGD': '$',
        'QAR': 'ر.ق',
        'ZAR': 'R',
    }
    return symbols.get(currency_code, currency_code)


def generate_card_number():
    """Génère un numéro de carte aléatoire"""
    return ''.join(random.choices(string.digits, k=16))
