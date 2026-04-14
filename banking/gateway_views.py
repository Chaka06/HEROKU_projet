"""
Portail public de création de compte — /gateway/
Page accessible à tous : le client remplit ses infos, choisit son type
de compte, paie via GeniusPay et reçoit ses identifiants par email.
L'URL /gateway/ est neutre et ne révèle pas la nature du projet.
"""
import hashlib
import hmac
import json
import logging
import random
import string
import time
from decimal import Decimal

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import AccountCreationOrder, BankAccount, Card, UserProfile
from .utils import generate_account_number, generate_card_number, generate_iban

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Page principale — formulaire public
# ─────────────────────────────────────────────

def gateway_home(request):
    """
    Formulaire public de création de compte.
    Accessible à tous, sans authentification.
    """
    banks = BankAccount  # pour les currencies
    errors = []
    post_data = {}

    # Récupérer les banques actives pour le sélecteur
    from .models import Bank
    active_banks = Bank.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        post_data = request.POST

        # --- Récupération des champs ---
        first_name  = request.POST.get('first_name', '').strip()
        last_name   = request.POST.get('last_name', '').strip()
        email       = request.POST.get('email', '').strip().lower()
        phone       = request.POST.get('phone', '').strip()
        dob         = request.POST.get('date_of_birth', '') or None
        address     = request.POST.get('address', '').strip()
        city        = request.POST.get('city', '').strip()
        country     = request.POST.get('country', 'France').strip()
        bank_id     = request.POST.get('bank_id', '')
        currency    = request.POST.get('currency', 'EUR')

        create_checking = request.POST.get('create_checking') == 'on'
        create_savings  = request.POST.get('create_savings') == 'on'

        try:
            initial_checking = Decimal(request.POST.get('initial_checking_balance') or '0')
        except Exception:
            initial_checking = Decimal('0')
        try:
            initial_savings = Decimal(request.POST.get('initial_savings_balance') or '0')
        except Exception:
            initial_savings = Decimal('0')

        account_status    = request.POST.get('account_status', 'ACTIVE')
        suspension_reason = request.POST.get('suspension_reason', '').strip()
        try:
            deblocage_fee = Decimal(request.POST.get('deblocage_fee') or '0')
        except Exception:
            deblocage_fee = Decimal('0')

        # --- Validation ---
        if not first_name or not last_name:
            errors.append("Le prénom et le nom sont obligatoires.")
        if not email:
            errors.append("L'adresse email est obligatoire.")
        elif User.objects.filter(email=email).exists():
            errors.append("Cette adresse email est déjà utilisée. Contactez le support.")
        if not bank_id:
            errors.append("Veuillez choisir une banque.")
        if not create_checking and not create_savings:
            errors.append("Sélectionnez au moins un type de compte.")
        if account_status not in ('ACTIVE', 'SUSPENDED'):
            errors.append("Statut de compte invalide.")

        if not errors:
            try:
                from .models import Bank
                bank = Bank.objects.get(id=bank_id, is_active=True)
            except Bank.DoesNotExist:
                errors.append("Banque invalide.")

        if not errors:
            # Générer username unique
            base = ''.join(
                c for c in f"{first_name.lower()}.{last_name.lower()}"
                if c.isalnum() or c == '.'
            )
            username = base
            while User.objects.filter(username=username).exists():
                username = f"{base}{''.join(random.choices(string.digits, k=4))}"

            # Mot de passe temporaire (12 caractères)
            temp_password = ''.join(
                random.choices(string.ascii_letters + string.digits, k=12)
            )

            # Calcul des frais
            fee = (
                settings.AGENT_FEE_ACTIVE
                if account_status == 'ACTIVE'
                else settings.AGENT_FEE_SUSPENDED
            )

            try:
                with db_transaction.atomic():
                    order = AccountCreationOrder.objects.create(
                        bank=bank,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone,
                        date_of_birth=dob,
                        address=address,
                        city=city,
                        country=country,
                        username=username,
                        temp_password=temp_password,
                        currency=currency,
                        create_checking=create_checking,
                        initial_checking_balance=initial_checking,
                        create_savings=create_savings,
                        initial_savings_balance=initial_savings,
                        account_status=account_status,
                        suspension_reason=suspension_reason,
                        deblocage_fee=deblocage_fee,
                        creation_fee=Decimal(str(fee)),
                        order_status='PENDING_PAYMENT',
                    )

                # Appel GeniusPay (hors transaction atomique)
                checkout_data = _create_geniuspay_payment(order, request)
                order.checkout_url             = checkout_data.get('checkout_url', '')
                order.geniuspay_reference      = checkout_data.get('reference', '')
                order.geniuspay_transaction_id = checkout_data.get('id')
                order.save(update_fields=[
                    'checkout_url', 'geniuspay_reference', 'geniuspay_transaction_id'
                ])

                return redirect('gateway:payment', order_id=order.id)

            except requests.RequestException as e:
                logger.error(f"GeniusPay API error: {e}")
                errors.append(
                    "Le service de paiement est temporairement indisponible. "
                    "Réessayez dans quelques instants."
                )
            except Exception as e:
                logger.error(f"Erreur création commande: {e}", exc_info=True)
                errors.append("Une erreur est survenue. Veuillez réessayer.")

    return render(request, 'gateway/home.html', {
        'active_banks': active_banks,
        'currencies':   BankAccount.CURRENCIES,
        'errors':       errors,
        'post_data':    post_data,
        'fee_active':    settings.AGENT_FEE_ACTIVE,
        'fee_suspended': settings.AGENT_FEE_SUSPENDED,
        'fee_currency':  settings.AGENT_FEE_CURRENCY,
    })


# ─────────────────────────────────────────────
#  Page de paiement
# ─────────────────────────────────────────────

def gateway_payment(request, order_id):
    """Récapitulatif + redirection vers la page checkout GeniusPay."""
    order = get_object_or_404(AccountCreationOrder, id=order_id)
    return render(request, 'gateway/payment.html', {
        'order':        order,
        'fee_currency': settings.AGENT_FEE_CURRENCY,
    })


def gateway_payment_success(request, order_id):
    """GeniusPay redirige ici après paiement réussi."""
    order = get_object_or_404(AccountCreationOrder, id=order_id)
    return render(request, 'gateway/payment_success.html', {'order': order})


def gateway_payment_error(request, order_id):
    """GeniusPay redirige ici en cas d'échec."""
    order = get_object_or_404(AccountCreationOrder, id=order_id)
    if order.payment_status == 'PENDING':
        order.payment_status = 'FAILED'
        order.order_status   = 'FAILED'
        order.save(update_fields=['payment_status', 'order_status'])
    return render(request, 'gateway/payment_error.html', {'order': order})


def gateway_payment_retry(request, order_id):
    """Recréer un lien de paiement GeniusPay pour une commande échouée."""
    order = get_object_or_404(AccountCreationOrder, id=order_id)
    if order.order_status not in ('PENDING_PAYMENT', 'FAILED'):
        return redirect('gateway:payment', order_id=order.id)
    try:
        order.payment_status = 'PENDING'
        order.order_status   = 'PENDING_PAYMENT'
        order.save(update_fields=['payment_status', 'order_status'])
        checkout_data = _create_geniuspay_payment(order, request)
        order.checkout_url             = checkout_data.get('checkout_url', '')
        order.geniuspay_reference      = checkout_data.get('reference', '')
        order.geniuspay_transaction_id = checkout_data.get('id')
        order.save(update_fields=[
            'checkout_url', 'geniuspay_reference', 'geniuspay_transaction_id',
            'payment_status', 'order_status',
        ])
        return redirect('gateway:payment', order_id=order.id)
    except Exception as e:
        logger.error(f"Retry paiement error: {e}", exc_info=True)
        return render(request, 'gateway/payment_error.html', {
            'order':       order,
            'retry_error': "Impossible de créer un nouveau lien. Réessayez.",
        })


# ─────────────────────────────────────────────
#  Webhook GeniusPay
# ─────────────────────────────────────────────

@csrf_exempt
def gateway_webhook_geniuspay(request):
    """
    Reçoit les notifications GeniusPay en temps réel.
    Sur payment.success → crée le compte et envoie les emails.
    Répond toujours 200 pour éviter les renvois GeniusPay.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    signature  = request.META.get('HTTP_X_WEBHOOK_SIGNATURE', '')
    timestamp  = request.META.get('HTTP_X_WEBHOOK_TIMESTAMP', '')
    event_type = request.META.get('HTTP_X_WEBHOOK_EVENT', '')

    # Vérification signature HMAC-SHA256
    body   = request.body.decode('utf-8')
    secret = settings.GENIUSPAY_WEBHOOK_SECRET

    if secret and signature and timestamp:
        data_to_sign = f"{timestamp}.{body}"
        expected = hmac.new(
            secret.encode(), data_to_sign.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            logger.warning("Webhook GeniusPay: signature invalide")
            return HttpResponse(status=200)
        # Protection anti-replay (5 min max)
        try:
            if abs(time.time() - int(timestamp)) > 300:
                logger.warning("Webhook GeniusPay: timestamp trop ancien")
                return HttpResponse(status=200)
        except (ValueError, TypeError):
            return HttpResponse(status=200)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return HttpResponse(status=200)

    reference = payload.get('data', {}).get('reference', '')

    if event_type == 'payment.success':
        try:
            order = (
                AccountCreationOrder.objects
                .select_related('bank')
                .get(geniuspay_reference=reference, payment_status='PENDING')
            )
            _process_paid_order(order, payload)
        except AccountCreationOrder.DoesNotExist:
            logger.warning(f"Webhook: commande introuvable — référence {reference}")
        except Exception as e:
            logger.error(f"Webhook payment.success error: {e}", exc_info=True)

    elif event_type in ('payment.failed', 'payment.expired'):
        try:
            AccountCreationOrder.objects.filter(
                geniuspay_reference=reference,
                payment_status='PENDING',
            ).update(
                payment_status='FAILED' if event_type == 'payment.failed' else 'EXPIRED',
                order_status='FAILED',
            )
        except Exception as e:
            logger.error(f"Webhook {event_type} error: {e}")

    return HttpResponse(status=200)


# ─────────────────────────────────────────────
#  Helpers internes
# ─────────────────────────────────────────────

def _create_geniuspay_payment(order, request):
    """Appelle l'API GeniusPay pour créer une session checkout. Retourne data{}."""
    site_url = settings.SITE_URL.rstrip('/')
    payload = {
        "amount":      int(order.creation_fee),
        "currency":    "XOF",
        "description": f"Création compte bancaire {order.bank.name} — {order.first_name} {order.last_name}",
        "customer": {
            "name":  f"{order.first_name} {order.last_name}",
            "email": order.email,
            "phone": order.phone or "",
        },
        "success_url": f"{site_url}/gateway/pay/{order.id}/success/",
        "error_url":   f"{site_url}/gateway/pay/{order.id}/error/",
        "metadata": {
            "order_id":  str(order.id),
            "bank_slug": order.bank.slug,
        },
    }
    response = requests.post(
        f"{settings.GENIUSPAY_BASE_URL}/payments",
        json=payload,
        headers={
            "X-API-Key":    settings.GENIUSPAY_API_KEY,
            "X-API-Secret": settings.GENIUSPAY_API_SECRET,
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get('success'):
        raise Exception(f"GeniusPay error: {data}")
    return data['data']


def _process_paid_order(order, payload):
    """Crée le compte bancaire après confirmation du paiement GeniusPay."""
    with db_transaction.atomic():
        order.payment_status = 'PAID'
        order.paid_at        = timezone.now()
        order.order_status   = 'PROCESSING'
        order.save(update_fields=['payment_status', 'paid_at', 'order_status'])

        # Créer l'utilisateur Django
        user = User.objects.create_user(
            username=order.username,
            email=order.email,
            password=order.temp_password,
            first_name=order.first_name,
            last_name=order.last_name,
        )

        # Créer le profil
        UserProfile.objects.create(
            user=user,
            phone=order.phone,
            address=order.address,
            city=order.city,
            country=order.country,
            date_of_birth=order.date_of_birth,
        )

        # Créer les comptes demandés + carte pour chacun
        def _make_account(account_type, balance):
            account = BankAccount.objects.create(
                user=user,
                bank=order.bank,
                account_number=generate_account_number(),
                account_type=account_type,
                currency=order.currency,
                balance=balance,
                iban=generate_iban(order.country, order.bank.swift_code),
                bic=order.bank.swift_code or 'BANKXXXXXX',
                status=order.account_status,
                suspension_reason=order.suspension_reason,
            )
            Card.objects.create(
                account=account,
                card_number=generate_card_number(),
                card_holder_name=f"{user.first_name.upper()} {user.last_name.upper()}",
                card_type='DEBIT',
                card_network='MASTERCARD',
                expiry_date='12/28',
                cvv=str(random.randint(100, 999)),
            )

        if order.create_checking:
            _make_account('CHECKING', order.initial_checking_balance)
        if order.create_savings:
            _make_account('SAVINGS', order.initial_savings_balance)

        # Finaliser la commande
        order.created_user = user
        order.order_status = 'COMPLETED'
        order.completed_at = timezone.now()
        order.save(update_fields=['created_user', 'order_status', 'completed_at'])

    # Emails hors transaction atomique
    try:
        from .email_service import send_welcome_email
        send_welcome_email(user, order.bank, order.temp_password)
    except Exception as e:
        logger.error(f"Email bienvenue (commande #{order.id}): {e}")


# ─────────────────────────────────────────────
#  Historique des commandes (lecture seule)
# ─────────────────────────────────────────────

def gateway_orders(request):
    """Liste paginée de toutes les commandes — lecture seule, sans auth."""
    from django.core.paginator import Paginator

    status_filter = request.GET.get('status', '')
    qs = AccountCreationOrder.objects.select_related('bank').order_by('-created_at')
    if status_filter:
        qs = qs.filter(order_status=status_filter)

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'gateway/orders.html', {
        'page_obj':       page_obj,
        'status_filter':  status_filter,
        'order_statuses': AccountCreationOrder.ORDER_STATUS,
    })


def gateway_order_detail(request, order_id):
    """Détail d'une commande — lecture seule."""
    order     = get_object_or_404(AccountCreationOrder, id=order_id)
    login_url = None
    if order.order_status == 'COMPLETED':
        site_url  = settings.SITE_URL.rstrip('/')
        login_url = f"{site_url}/login/"
    return render(request, 'gateway/order_detail.html', {
        'order':     order,
        'login_url': login_url,
    })
