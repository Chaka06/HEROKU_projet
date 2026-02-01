from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as db_transaction
from django.http import HttpResponse
from decimal import Decimal
from .models import BankAccount, Transaction, Beneficiary, Notification, SupportMessage


def select_bank_view(request):
    """Page de sélection de la banque"""
    from .models import Bank
    banks = Bank.objects.filter(is_active=True).order_by('name')
    return render(request, 'banking/bank_selection.html', {'banks': banks})


def bank_login_view(request, bank_slug):
    """Page de connexion spécifique à une banque"""
    from .models import Bank
    bank = get_object_or_404(Bank, slug=bank_slug, is_active=True)
    
    if request.user.is_authenticated:
        return redirect('banking:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Vérifier que l'utilisateur appartient à cette banque
            user_bank = user.bank_accounts.first().bank if user.bank_accounts.exists() else None
            if user_bank and user_bank.id != bank.id:
                messages.error(request, f'Ce compte n\'appartient pas à {bank.name}')
                return render(request, 'banking/bank_login.html', {'bank': bank})
            
            # Créer et envoyer OTP
            from .email_service import create_otp, send_otp_email
            otp = create_otp(user, 'LOGIN')
            
            try:
                send_otp_email(user, otp.code, 'LOGIN')
                request.session['otp_user_id'] = user.id
                request.session['otp_type'] = 'LOGIN'
                messages.success(request, f'Code envoyé à {user.email}')
                return redirect('banking:verify_otp')
            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
        else:
            messages.error(request, 'Identifiants incorrects')
    
    return render(request, 'banking/bank_login.html', {'bank': bank})


def login_view(request):
    """Redirection vers la sélection de banque"""
    return redirect('banking:select_bank')


def verify_otp_view(request):
    """Vue de vérification du code OTP"""
    user_id = request.session.get('otp_user_id')
    otp_type = request.session.get('otp_type', 'LOGIN')
    
    if not user_id:
        return redirect('banking:login')
    
    from django.contrib.auth.models import User
    user = User.objects.get(id=user_id)
    
    # Récupérer les infos de la banque pour le thème
    account = user.bank_accounts.first()
    bank_primary_color = account.bank.primary_color if account and account.bank else '#009464'
    bank_secondary_color = account.bank.secondary_color if account and account.bank else '#007850'
    bank_name = account.bank.name if account and account.bank else 'Banque'
    
    # Renvoyer le code si demandé
    if request.GET.get('resend') == '1':
        from .email_service import create_otp, send_otp_email
        otp = create_otp(user, otp_type)
        send_otp_email(user, otp.code, otp_type)
        messages.success(request, 'Un nouveau code a été envoyé')
    
    if request.method == 'POST':
        # Récupérer le code OTP
        code = ''.join([
            request.POST.get('otp1', ''),
            request.POST.get('otp2', ''),
            request.POST.get('otp3', ''),
            request.POST.get('otp4', ''),
            request.POST.get('otp5', '')
        ])
        
        from .email_service import verify_otp
        if verify_otp(user, code, otp_type):
            if otp_type == 'LOGIN':
                login(request, user)
                del request.session['otp_user_id']
                del request.session['otp_type']
                messages.success(request, 'Connexion réussie!')
                return redirect('banking:dashboard')
            elif otp_type == 'CHANGE_PASSWORD':
                # Rediriger vers le formulaire de changement de MDP
                return redirect('banking:change_password_confirm')
            elif otp_type == 'EDIT_PROFILE':
                # Rediriger vers le formulaire d'édition
                return redirect('banking:edit_profile_confirm')
        else:
            context = {
                'error': 'Code incorrect ou expiré',
                'user': user,
                'bank_primary_color': bank_primary_color,
                'bank_secondary_color': bank_secondary_color,
                'bank_name': bank_name,
            }
            return render(request, 'banking/otp_verification.html', context)
    
    context = {
        'user': user,
        'bank_primary_color': bank_primary_color,
        'bank_secondary_color': bank_secondary_color,
        'bank_name': bank_name,
    }
    return render(request, 'banking/otp_verification.html', context)




@login_required
def dashboard_view(request):
    """Vue du tableau de bord avec statistiques"""
    # Récupérer le compte principal et la carte
    primary_account = request.user.bank_accounts.filter(account_type='CHECKING').first()
    primary_card = primary_account.cards.first() if primary_account else None
    
    # Récupérer les transactions récentes
    transactions = Transaction.objects.filter(
        account__user=request.user
    ).order_by('-created_at')[:20]
    
    # === STATISTIQUES ===
    from django.db.models import Sum, Count
    from datetime import datetime, timedelta
    
    # Toutes les transactions de l'utilisateur
    all_transactions = Transaction.objects.filter(account__user=request.user)
    
    # Total des dépenses (7 derniers jours)
    seven_days_ago = datetime.now() - timedelta(days=7)
    expenses_7d = all_transactions.filter(
        created_at__gte=seven_days_ago,
        transaction_type__in=['TRANSFER', 'PAYMENT', 'PURCHASE', 'ONLINE_PURCHASE']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Total des revenus (7 derniers jours)
    income_7d = all_transactions.filter(
        created_at__gte=seven_days_ago,
        transaction_type='DEPOSIT'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Transactions par type
    stats_by_type = {
        'deposits': all_transactions.filter(transaction_type='DEPOSIT').count(),
        'transfers': all_transactions.filter(transaction_type='TRANSFER').count(),
        'payments': all_transactions.filter(transaction_type='PAYMENT').count(),
        'purchases': all_transactions.filter(transaction_type__in=['PURCHASE', 'ONLINE_PURCHASE']).count(),
    }
    
    # Solde total tous comptes
    total_balance = sum(acc.balance for acc in request.user.bank_accounts.all())
    
    # Nombre de comptes actifs
    active_accounts = request.user.bank_accounts.filter(status='ACTIVE').count()
    
    # Transactions par jour (7 derniers jours)
    daily_stats = []
    for i in range(6, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        count = all_transactions.filter(created_at__range=[day_start, day_end]).count()
        daily_stats.append({
            'date': day.strftime('%d/%m'),
            'count': count
        })
    
    context = {
        'primary_account': primary_account,
        'primary_card': primary_card,
        'transactions': transactions,
        'total_balance': total_balance,
        'active_accounts': active_accounts,
        'expenses_7d': expenses_7d,
        'income_7d': income_7d,
        'stats_by_type': stats_by_type,
        'daily_stats': daily_stats,
    }
    
    return render(request, 'banking/dashboard.html', context)


@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    return render(request, 'banking/profile.html')


@login_required
def settings_view(request):
    """Vue des paramètres"""
    unread_notifications = request.user.notifications.filter(is_read=False).count()
    unread_messages = SupportMessage.objects.filter(user=request.user, sender_is_staff=True, is_read=False).count()
    
    # Déterminer la langue actuelle
    current_lang = request.user.profile.language if hasattr(request.user, 'profile') else 'fr'
    language_names = {
        'fr': 'Français',
        'en': 'English',
        'es': 'Español',
        'it': 'Italiano',
        'pl': 'Polski'
    }
    
    context = {
        'unread_notifications_count': unread_notifications,
        'unread_messages_count': unread_messages,
        'current_language': language_names.get(current_lang, 'Français'),
    }
    return render(request, 'banking/settings.html', context)


@login_required
def notifications_view(request):
    """Vue des notifications"""
    notifications = request.user.notifications.all()
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'banking/notifications.html', context)


@login_required
def support_chat_view(request):
    """Vue du chat support"""
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            SupportMessage.objects.create(
                user=request.user,
                sender_is_staff=False,
                message=message_text
            )
            messages.success(request, 'Message envoyé!')
            return redirect('banking:support_chat')
    
    messages_list = SupportMessage.objects.filter(user=request.user)
    
    context = {
        'messages_list': messages_list,
    }
    
    return render(request, 'banking/support_chat.html', context)


@login_required
def edit_profile_view(request):
    """Vue édition profil - Demande OTP"""
    from .email_service import create_otp, send_otp_email
    otp = create_otp(request.user, 'EDIT_PROFILE')
    
    try:
        send_otp_email(request.user, otp.code, 'EDIT_PROFILE')
        request.session['otp_user_id'] = request.user.id
        request.session['otp_type'] = 'EDIT_PROFILE'
        messages.info(request, f'Code envoyé à {request.user.email}')
        return redirect('banking:verify_otp')
    except Exception as e:
        messages.error(request, f'Erreur: {str(e)}')
        return redirect('banking:settings')


@login_required
def edit_profile_confirm_view(request):
    """Formulaire après OTP"""
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        request.user.save()
        
        if hasattr(request.user, 'profile'):
            request.user.profile.phone = request.POST.get('phone', '')
            request.user.profile.address = request.POST.get('address', '')
            request.user.profile.city = request.POST.get('city', '')
            request.user.profile.country = request.POST.get('country', '')
            request.user.profile.save()
        
        messages.success(request, 'Profil mis à jour!')
        return redirect('banking:profile')
    
    return render(request, 'banking/edit_profile.html')


@login_required
def change_password_view(request):
    """Vue de changement de mot de passe - Demande OTP"""
    from .email_service import create_otp, send_otp_email
    otp = create_otp(request.user, 'CHANGE_PASSWORD')
    
    try:
        send_otp_email(request.user, otp.code, 'CHANGE_PASSWORD')
        request.session['otp_user_id'] = request.user.id
        request.session['otp_type'] = 'CHANGE_PASSWORD'
        messages.info(request, f'Code envoyé à {request.user.email}')
        return redirect('banking:verify_otp')
    except Exception as e:
        messages.error(request, f'Erreur: {str(e)}')
        return redirect('banking:settings')


@login_required
def change_password_confirm_view(request):
    """Formulaire après OTP"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Mot de passe actuel incorrect.')
        elif new_password1 != new_password2:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Mot de passe modifié!')
            return redirect('banking:settings')
    
    return render(request, 'banking/change_password.html')


@login_required
def change_language_view(request):
    """Vue pour changer la langue"""
    from django.utils import translation
    from django.conf import settings
    from .translations import translate as _t
    
    lang = request.GET.get('lang')
    
    if lang and hasattr(request.user, 'profile'):
        # Sauvegarder dans le profil
        request.user.profile.language = lang
        request.user.profile.save()
        
        # Activer la langue immédiatement
        translation.activate(lang)
        request.session['django_language'] = lang
        
        # Message traduit
        success_msg = _t('Language changed successfully', lang)
        messages.success(request, success_msg)
        return redirect('banking:settings')
    
    current_lang = request.user.profile.language if hasattr(request.user, 'profile') else 'fr'
    
    context = {
        'current_language': current_lang,
    }
    
    return render(request, 'banking/change_language.html', context)


@login_required
def transfer_view(request):
    """Vue de virement"""
    user_accounts = request.user.bank_accounts.filter(is_active=True)
    beneficiaries = request.user.beneficiaries.all()[:3]
    
    # Vérifier si l'utilisateur a les deux types de comptes
    has_checking = user_accounts.filter(account_type='CHECKING').exists()
    has_savings = user_accounts.filter(account_type='SAVINGS').exists()
    can_internal_transfer = has_checking and has_savings
    
    # Pré-remplir si un bénéficiaire est sélectionné
    selected_beneficiary = None
    beneficiary_id = request.GET.get('beneficiary')
    if beneficiary_id:
        try:
            selected_beneficiary = request.user.beneficiaries.get(id=beneficiary_id)
        except Beneficiary.DoesNotExist:
            pass
    
    if request.method == 'POST':
        from_account_id = request.POST.get('from_account')
        beneficiary_name = request.POST.get('beneficiary')
        iban = request.POST.get('iban')
        beneficiary_email = request.POST.get('beneficiary_email', '')
        amount = Decimal(request.POST.get('amount', 0))
        reference = request.POST.get('reference', '')
        
        try:
            from_account = BankAccount.objects.get(id=from_account_id, user=request.user)
            
            if amount <= 0:
                messages.error(request, 'Le montant doit être supérieur à 0.')
            elif amount > from_account.balance:
                messages.error(request, 'Solde insuffisant.')
            else:
                with db_transaction.atomic():
                    # Débiter le compte
                    from_account.balance -= amount
                    from_account.save()
                    
                    # Créer la transaction
                    trans = Transaction.objects.create(
                        account=from_account,
                        transaction_type='TRANSFER',
                        amount=amount,
                        balance_after=from_account.balance,
                        description=f'Virement vers {beneficiary_name}',
                        reference=reference,
                        recipient=beneficiary_name,
                        recipient_iban=iban,
                        status='PENDING'
                    )
                    
                    # ENVOYER EMAIL AU TITULAIRE
                    try:
                        from .email_service import send_transaction_email_to_sender
                        send_transaction_email_to_sender(trans)
                    except Exception as e:
                        print(f"Erreur envoi email titulaire: {e}")
                    
                    # ENVOYER EMAIL AU BÉNÉFICIAIRE (si email fourni)
                    if beneficiary_email:
                        try:
                            from .email_service import send_transaction_email_to_beneficiary
                            send_transaction_email_to_beneficiary(trans, beneficiary_email, beneficiary_name)
                        except Exception as e:
                            print(f"Erreur envoi email bénéficiaire: {e}")
                    
                    messages.success(request, f'Virement de {amount}€ effectué avec succès vers {beneficiary_name}. Un email de confirmation vous a été envoyé.')
                    return redirect('banking:dashboard')
                    
        except BankAccount.DoesNotExist:
            messages.error(request, 'Compte introuvable.')
        except Exception as e:
            messages.error(request, f'Erreur lors du virement: {str(e)}')
    
    context = {
        'user_accounts': user_accounts,
        'beneficiaries': beneficiaries,
        'selected_beneficiary': selected_beneficiary,
        'can_internal_transfer': can_internal_transfer,
    }
    
    return render(request, 'banking/transfer.html', context)


@login_required
def transactions_view(request):
    """Vue de l'historique des transactions"""
    user_accounts = request.user.bank_accounts.all()
    
    # Récupérer toutes les transactions
    transactions = Transaction.objects.filter(
        account__user=request.user
    ).order_by('-created_at')
    
    # Calculer les statistiques
    deposits_count = transactions.filter(transaction_type='DEPOSIT').count()
    withdrawals_count = transactions.exclude(transaction_type='DEPOSIT').count()
    
    # Calculer le solde total
    total_balance = sum(acc.balance for acc in user_accounts)
    currency = user_accounts.first().currency if user_accounts.exists() else 'EUR'
    from .utils import get_currency_symbol
    total_balance_display = f"{total_balance} {get_currency_symbol(currency)}"
    
    context = {
        'transactions': transactions,
        'user_accounts': user_accounts,
        'deposits_count': deposits_count,
        'withdrawals_count': withdrawals_count,
        'total_balance': total_balance_display,
    }
    
    return render(request, 'banking/transactions.html', context)


@login_required
def rib_view(request):
    """Vue du RIB"""
    user_accounts = request.user.bank_accounts.filter(is_active=True)
    
    context = {
        'user_accounts': user_accounts,
    }
    
    return render(request, 'banking/rib.html', context)


@login_required
def download_rib_pdf(request, account_id):
    """Télécharge le RIB en PDF"""
    account = get_object_or_404(
        BankAccount,
        id=account_id,
        user=request.user
    )
    
    from .pdf_generator import generate_rib_pdf
    pdf_content = generate_rib_pdf(account)
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="RIB_{account.account_type}_{account.account_number}.pdf"'
    
    return response


@login_required
def beneficiaries_view(request):
    """Vue de la liste des bénéficiaires"""
    beneficiaries = request.user.beneficiaries.all()
    
    context = {
        'beneficiaries': beneficiaries,
    }
    
    return render(request, 'banking/beneficiaries.html', context)


@login_required
def add_beneficiary_view(request):
    """Vue pour ajouter un bénéficiaire"""
    if request.method == 'POST':
        name = request.POST.get('name')
        iban = request.POST.get('iban')
        bic = request.POST.get('bic', '')
        email = request.POST.get('email', '')
        
        try:
            Beneficiary.objects.create(
                user=request.user,
                name=name,
                iban=iban,
                bic=bic,
                email=email
            )
            messages.success(request, f'Bénéficiaire {name} ajouté avec succès!')
            return redirect('banking:beneficiaries')
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout du bénéficiaire: {str(e)}')
    
    return render(request, 'banking/add_beneficiary.html')


@login_required
def internal_transfer_view(request):
    """Vue pour les virements internes entre comptes d'un même utilisateur"""
    user_accounts = request.user.bank_accounts.filter(is_active=True, status='ACTIVE')
    
    if request.method == 'POST':
        from_account_id = request.POST.get('from_account')
        to_account_id = request.POST.get('to_account')
        amount = Decimal(request.POST.get('amount', 0))
        reference = request.POST.get('reference', '')
        
        # Vérifier que les comptes sont différents
        if from_account_id == to_account_id:
            messages.error(request, 'Vous ne pouvez pas transférer vers le même compte.')
            return redirect('banking:internal_transfer')
        
        try:
            from_account = BankAccount.objects.get(id=from_account_id, user=request.user)
            to_account = BankAccount.objects.get(id=to_account_id, user=request.user)
            
            if amount <= 0:
                messages.error(request, 'Le montant doit être supérieur à 0.')
            elif amount > from_account.balance:
                messages.error(request, 'Solde insuffisant sur le compte source.')
            else:
                with db_transaction.atomic():
                    # Débiter le compte source
                    from_account.balance -= amount
                    from_account.save()
                    
                    # Créer la transaction de débit
                    Transaction.objects.create(
                        account=from_account,
                        transaction_type='TRANSFER',
                        amount=amount,
                        balance_after=from_account.balance,
                        description=f'Virement interne vers {to_account.get_account_type_display()}',
                        reference=reference
                    )
                    
                    # Créditer le compte destination
                    to_account.balance += amount
                    to_account.save()
                    
                    # Créer la transaction de crédit
                    Transaction.objects.create(
                        account=to_account,
                        transaction_type='DEPOSIT',
                        amount=amount,
                        balance_after=to_account.balance,
                        description=f'Virement interne depuis {from_account.get_account_type_display()}',
                        reference=reference
                    )
                    
                    from .utils import get_currency_symbol
                    symbol = get_currency_symbol(from_account.currency)
                    messages.success(request, 
                        f'Virement interne de {amount} {symbol} effectué avec succès! '
                        f'{from_account.get_account_type_display()} → {to_account.get_account_type_display()}'
                    )
                    return redirect('banking:dashboard')
                    
        except BankAccount.DoesNotExist:
            messages.error(request, 'Compte introuvable.')
        except Exception as e:
            messages.error(request, f'Erreur lors du virement: {str(e)}')
    
    context = {
        'user_accounts': user_accounts,
        'primary_account': user_accounts.first() if user_accounts.exists() else None,
    }
    
    return render(request, 'banking/internal_transfer.html', context)


@login_required
def transaction_detail_view(request, transaction_id):
    """Vue des détails d'une transaction"""
    transaction = get_object_or_404(
        Transaction, 
        id=transaction_id, 
        account__user=request.user
    )
    
    context = {
        'transaction': transaction,
    }
    
    return render(request, 'banking/transaction_detail.html', context)


@login_required
def download_receipt_view(request, transaction_id):
    """Vue pour télécharger le bordereau de transaction (PDF)"""
    transaction = get_object_or_404(
        Transaction, 
        id=transaction_id, 
        account__user=request.user
    )
    
    # Générer le PDF
    from .pdf_generator import generate_transaction_receipt_pdf
    pdf_content = generate_transaction_receipt_pdf(transaction)
    
    # Créer la réponse HTTP
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bordereau_transaction_{transaction.id}.pdf"'
    
    return response


@login_required
def confirm_transaction_view(request, transaction_id):
    """Confirmer une transaction en attente"""
    transaction = get_object_or_404(
        Transaction,
        id=transaction_id,
        account__user=request.user,
        status='PENDING'
    )
    
    from django.utils import timezone
    
    # Confirmer la transaction
    transaction.status = 'COMPLETED'
    transaction.confirmed_at = timezone.now()
    transaction.save()
    
    # ENVOYER EMAIL DE CONFIRMATION
    try:
        from .email_service import send_transaction_confirmation_email
        send_transaction_confirmation_email(transaction)
    except Exception as e:
        print(f"Erreur envoi email confirmation: {e}")
    
    messages.success(request, 'Transaction confirmée avec succès! Un email de confirmation vous a été envoyé.')
    return redirect('banking:transaction_detail', transaction_id=transaction_id)


@login_required
def reject_transaction_view(request, transaction_id):
    """Rejeter une transaction en attente"""
    transaction = get_object_or_404(
        Transaction,
        id=transaction_id,
        account__user=request.user,
        status='PENDING'
    )
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason')
        rejection_fee = Decimal(request.POST.get('rejection_fee', '0.00'))
        
        from django.utils import timezone
        
        with db_transaction.atomic():
            # Rembourser le montant (sauf si c'était un dépôt)
            if not transaction.is_positive():
                transaction.account.balance += transaction.amount
            else:
                transaction.account.balance -= transaction.amount
            
            # Appliquer les frais de rejet
            if rejection_fee > 0:
                transaction.account.balance -= rejection_fee
            
            transaction.account.save()
            
            # Mettre à jour la transaction
            transaction.status = 'REJECTED'
            transaction.rejection_reason = rejection_reason
            transaction.rejection_fee = rejection_fee
            transaction.rejected_at = timezone.now()
            transaction.balance_after = transaction.account.balance
            transaction.save()
            
            # Créer une notification
            Notification.objects.create(
                user=request.user,
                notification_type='TRANSACTION',
                title='Transaction Rejetée',
                message=f'Votre transaction de {transaction.amount} a été rejetée. Motif: {rejection_reason}'
            )
            
            # ENVOYER EMAIL DE REJET
            try:
                from .email_service import send_transaction_rejection_email
                send_transaction_rejection_email(transaction)
            except Exception as e:
                print(f"Erreur envoi email rejet: {e}")
            
            messages.success(request, 'Transaction rejetée. Le montant a été remboursé sur votre compte. Un email vous a été envoyé.')
            return redirect('banking:transaction_detail', transaction_id=transaction_id)
    
    context = {
        'transaction': transaction,
    }
    
    return render(request, 'banking/reject_transaction.html', context)


@login_required
def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('banking:login')
