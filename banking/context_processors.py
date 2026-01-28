def bank_theme(request):
    """Context processor pour injecter les couleurs de la banque de l'utilisateur"""
    context = {
        'bank_primary_color': '#e63946',
        'bank_secondary_color': '#d62828',
        'bank_accent_color': '#f4a261',
        'bank_background_color': '#f8f9fa',
        'bank_text_color': '#ffffff',
        'bank_text_dark': '#1a1a1a',
        'bank_name': 'MaBanque',
        'bank_logo': None,
    }
    
    if request.user.is_authenticated and not request.user.is_superuser:
        # Récupérer le premier compte de l'utilisateur
        account = request.user.bank_accounts.first()
        
        if account and account.bank:
            context['bank_primary_color'] = account.bank.primary_color
            context['bank_secondary_color'] = account.bank.secondary_color
            context['bank_accent_color'] = account.bank.accent_color
            context['bank_background_color'] = account.bank.background_color
            context['bank_text_color'] = account.bank.text_color
            context['bank_text_dark'] = account.bank.text_dark
            context['bank_name'] = account.bank.name
            if account.bank.logo:
                context['bank_logo'] = account.bank.logo.url
    
    return context
