"""
Service d'envoi d'emails pour les transactions bancaires
"""
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
import random
from datetime import timedelta
import os
import base64


def generate_otp_code():
    """Génère un code OTP à 5 chiffres"""
    return ''.join([str(random.randint(0, 9)) for _ in range(5)])


def create_otp(user, otp_type):
    """Crée un code OTP pour un utilisateur"""
    from .models import OTPCode
    OTPCode.objects.filter(user=user, otp_type=otp_type, is_used=False).delete()
    code = generate_otp_code()
    expires_at = timezone.now() + timedelta(minutes=10)
    otp = OTPCode.objects.create(user=user, code=code, otp_type=otp_type, expires_at=expires_at)
    return otp


def verify_otp(user, code, otp_type):
    """Vérifie un code OTP"""
    from .models import OTPCode
    try:
        otp = OTPCode.objects.get(user=user, code=code, otp_type=otp_type, is_used=False)
        if otp.is_valid():
            otp.is_used = True
            otp.save()
            return True
    except OTPCode.DoesNotExist:
        pass
    return False


# Fonction logo supprimée - on utilise juste le nom de la banque


def send_transaction_email_to_sender(transaction):
    """Email au titulaire avec PDF"""
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    
    if transaction.status == 'PENDING':
        title = "Virement en attente"
        bg_color = "#ff9800"
    elif transaction.status == 'COMPLETED':
        title = "Virement confirmé"
        bg_color = "#2e7d32"
    else:
        title = "Virement rejeté"
        bg_color = "#c62828"
    
    subject = f"{bank.name} - {title}"
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
</head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background-color:#f5f5f5;">
<div style="max-width:600px;margin:20px auto;background:white;border-radius:8px;overflow:hidden;">
<div style="background:linear-gradient(135deg,{bank.primary_color} 0%,{bank.secondary_color} 100%);padding:28px;text-align:center;border-bottom:4px solid {bank.secondary_color};">
<h1 style="color:white;margin:0;font-size:28px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;">{bank.name}</h1>
</div>
<div style="background:{bg_color};padding:15px;text-align:center;">
<h1 style="color:white;margin:0;font-size:20px;">{title}</h1>
</div>
<div style="padding:20px;">
<p style="font-size:15px;color:#333;">Bonjour <strong>{user.get_full_name() or user.username}</strong>,</p>
<p style="font-size:14px;color:#666;">Nous vous informons qu'un virement d'un montant de <strong>{transaction.amount} {symbol}</strong> a été effectué <strong>depuis votre compte</strong> {transaction.account.get_account_type_display()} N° <strong>{transaction.account.account_number}</strong></p>
<p style="font-size:13px;color:#666;">Vous recevrez le statut final sous 48h maximum</p>
<p style="font-size:13px;color:#666;margin-bottom:15px;">Détails de la transaction :</p>
<table style="width:100%;border-collapse:collapse;margin:10px 0;">
<tr><td style="padding:10px;border:1px solid #ddd;background:#f8f9fa;font-weight:bold;">Montant</td><td style="padding:10px;border:1px solid #ddd;">{transaction.amount} {symbol}</td></tr>
<tr><td style="padding:10px;border:1px solid #ddd;background:#f8f9fa;font-weight:bold;">Donneur d'ordre</td><td style="padding:10px;border:1px solid #ddd;">{user.get_full_name() or user.username}</td></tr>
<tr><td style="padding:10px;border:1px solid #ddd;background:#f8f9fa;font-weight:bold;">Motif</td><td style="padding:10px;border:1px solid #ddd;">{transaction.description or 'Non spécifié'}</td></tr>
<tr><td style="padding:10px;border:1px solid #ddd;background:#f8f9fa;font-weight:bold;">Vers le compte</td><td style="padding:10px;border:1px solid #ddd;">{transaction.recipient_iban or 'Non spécifié'}</td></tr>
</table>
</div>
<div style="background:#f8f9fa;padding:15px;text-align:center;">
<p style="font-size:11px;color:#999;margin:0;">Ceci est un mail automatique merci de ne pas y répondre</p>
<p style="font-size:12px;color:{bank.primary_color};font-weight:bold;margin:5px 0 0 0;">{bank.name} - Tous droits réservés</p>
</div>
</div>
</body>
</html>"""
    
    plain = f"{bank.name} - {title}\n\nBonjour {user.get_full_name()},\n\nVirement de {transaction.amount} {symbol} depuis votre compte.\n\n{bank.name}"
    
    email = EmailMultiAlternatives(subject=subject, body=plain, from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>', to=[user.email])
    email.attach_alternative(html, "text/html")
    
    # Attacher PDF
    try:
        from .pdf_generator import generate_transaction_receipt_pdf
        pdf = generate_transaction_receipt_pdf(transaction)
        email.attach(f'bordereau_T{str(transaction.id).zfill(6)}.pdf', pdf, 'application/pdf')
    except Exception as e:
        print(f"Erreur PDF: {e}")
    
    email.send(fail_silently=False)


def send_transaction_email_to_beneficiary(transaction, beneficiary_email, beneficiary_name):
    """Email au bénéficiaire avec PDF"""
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    
    logo_base64 = get_bank_logo_base64(bank)
    subject = f"{bank.name} - Virement reçu"
    
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background-color:#f5f5f5;">
<div style="max-width:600px;margin:40px auto;background:white;border-radius:8px;overflow:hidden;">
<div style="background:{bank.primary_color};padding:30px;text-align:center;">
{f'<img src="{logo_base64}" style="max-width:180px;height:auto;" alt="{bank.name}">' if logo_base64 else f'<h2 style="color:white;margin:0;">{bank.name}</h2>'}
</div>
<div style="background:#2e7d32;padding:20px;text-align:center;">
<h1 style="color:white;margin:0;">Virement reçu</h1>
</div>
<div style="padding:30px;">
<p>Bonjour <strong>{beneficiary_name}</strong>,</p>
<p>Un virement de <strong>{transaction.amount} {symbol}</strong> a été effectué vers votre compte par <strong>{user.get_full_name() or user.username}</strong></p>
<h2 style="font-size:20px;text-align:center;margin:20px 0 15px 0;">Détail de la transaction</h2>
<table style="width:100%;border-collapse:collapse;">
<tr><td style="padding:12px;border:1px solid #ddd;background:#f8f9fa;font-weight:bold;">Montant</td><td style="padding:12px;border:1px solid #ddd;"><strong>{transaction.amount} {symbol}</strong></td></tr>
<tr><td style="padding:12px;border:1px solid #ddd;background:#f8f9fa;font-weight:bold;">Émetteur</td><td style="padding:12px;border:1px solid #ddd;">{user.get_full_name() or user.username}</td></tr>
<tr><td style="padding:12px;border:1px solid #ddd;background:#f8f9fa;font-weight:bold;">Motif</td><td style="padding:12px;border:1px solid #ddd;">{transaction.description or 'Non spécifié'}</td></tr>
<tr><td style="padding:12px;border:1px solid #ddd;background:#f8f9fa;font-weight:bold;">Date</td><td style="padding:12px;border:1px solid #ddd;">{transaction.created_at.strftime('%d/%m/%Y à %H:%M')}</td></tr>
</table>
</div>
<div style="background:#f8f9fa;padding:20px;text-align:center;">
<p style="font-size:12px;color:#999;margin:0;">Ceci est un mail automatique merci de ne pas y répondre</p>
<p style="font-size:13px;color:{bank.primary_color};font-weight:bold;margin:5px 0;">{bank.name}</p>
<p style="font-size:11px;color:#bbb;margin:0;">Tous droits réservés</p>
</div>
</div>
</body>
</html>"""
    
    email = EmailMultiAlternatives(subject=subject, body=f"Virement de {transaction.amount} {symbol}", from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>', to=[beneficiary_email])
    email.attach_alternative(html, "text/html")
    
    try:
        from .pdf_generator import generate_transaction_receipt_pdf
        pdf = generate_transaction_receipt_pdf(transaction)
        email.attach(f'bordereau_T{str(transaction.id).zfill(6)}.pdf', pdf, 'application/pdf')
    except:
        pass
    
    email.send(fail_silently=False)


def send_transaction_confirmation_email(transaction):
    """Email confirmation avec PDF"""
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    
    subject = f"{bank.name} - Transaction confirmée"
    
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background-color:#f5f5f5;">
<div style="max-width:600px;margin:20px auto;background:white;border-radius:8px;overflow:hidden;">
<div style="background:linear-gradient(135deg,{bank.primary_color} 0%,{bank.secondary_color} 100%);padding:28px;text-align:center;border-bottom:4px solid {bank.secondary_color};">
<h1 style="color:white;margin:0;font-size:28px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;">{bank.name}</h1>
</div>
<div style="background:#2e7d32;padding:20px;text-align:center;">
<h1 style="color:white;margin:0;">Transaction Confirmée</h1>
</div>
<div style="padding:30px;">
<p>Bonjour <strong>{user.get_full_name()}</strong>,</p>
<p>Votre transaction de <strong>{transaction.amount} {symbol}</strong> a été confirmée.</p>
<p>Le bordereau est joint en pièce jointe.</p>
</div>
<div style="background:#f8f9fa;padding:20px;text-align:center;">
<p style="font-size:12px;color:#999;">Ceci est un mail automatique merci de ne pas y répondre</p>
<p style="font-size:13px;color:{bank.primary_color};font-weight:bold;margin:5px 0;">{bank.name}</p>
<p style="font-size:11px;color:#bbb;">Tous droits réservés</p>
</div>
</div>
</body>
</html>"""
    
    email = EmailMultiAlternatives(subject=subject, body=f"Confirmée: {transaction.amount} {symbol}", from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>', to=[user.email])
    email.attach_alternative(html, "text/html")
    
    try:
        from .pdf_generator import generate_transaction_receipt_pdf
        pdf = generate_transaction_receipt_pdf(transaction)
        email.attach(f'bordereau_T{str(transaction.id).zfill(6)}.pdf', pdf, 'application/pdf')
    except:
        pass
    
    email.send(fail_silently=False)


def send_transaction_rejection_email(transaction):
    """Email rejet avec PDF"""
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    
    subject = f"{bank.name} - Transaction rejetée par la banque"
    
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background-color:#f5f5f5;">
<div style="max-width:600px;margin:20px auto;background:white;border-radius:8px;overflow:hidden;">
<div style="background:linear-gradient(135deg,{bank.primary_color} 0%,{bank.secondary_color} 100%);padding:28px;text-align:center;border-bottom:4px solid {bank.secondary_color};">
<h1 style="color:white;margin:0;font-size:28px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;">{bank.name}</h1>
</div>
<div style="background:#c62828;padding:15px;text-align:center;">
<h1 style="color:white;margin:0;font-size:20px;">Transaction Rejetée</h1>
</div>
<div style="padding:20px;">
<p style="font-size:15px;color:#333;">Bonjour <strong>{user.get_full_name()}</strong>,</p>
<p style="background:#ffebee;padding:12px;border-left:4px solid #c62828;font-size:14px;">⚠️ Transaction de <strong>{transaction.amount} {symbol}</strong> rejetée par <strong>{bank.name}</strong></p>
<p style="font-size:14px;"><strong>Motif:</strong> {transaction.rejection_reason or 'Non spécifié'}</p>
{f'<p style="font-size:14px;">Frais: {transaction.rejection_fee} {symbol}</p>' if transaction.rejection_fee > 0 else ''}
<p style="font-size:13px;color:#666;">Le montant a été remboursé.</p>
</div>
<div style="background:#f8f9fa;padding:15px;text-align:center;">
<p style="font-size:11px;color:#999;">Ceci est un mail automatique merci de ne pas y répondre</p>
<p style="font-size:12px;color:{bank.primary_color};font-weight:bold;margin:5px 0 0 0;">{bank.name} - Tous droits réservés</p>
</div>
</div>
</body>
</html>"""
    
    email = EmailMultiAlternatives(subject=subject, body=f"Rejeté: {transaction.amount} {symbol}", from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>', to=[user.email])
    email.attach_alternative(html, "text/html")
    
    try:
        from .pdf_generator import generate_transaction_receipt_pdf
        pdf = generate_transaction_receipt_pdf(transaction)
        email.attach(f'bordereau_rejet_T{str(transaction.id).zfill(6)}.pdf', pdf, 'application/pdf')
    except:
        pass
    
    email.send(fail_silently=False)


def send_otp_email(user, otp_code, otp_type):
    """Email OTP"""
    account = user.bank_accounts.first()
    bank = account.bank if account and account.bank else None
    bank_name = bank.name if bank else "Banque"
    bank_color = bank.primary_color if bank else "#009464"
    
    subject = f'{bank_name} - Code de connexion'
    
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background-color:#f5f5f5;">
<div style="max-width:600px;margin:20px auto;background:white;border-radius:8px;overflow:hidden;">
<div style="background:{bank_color};padding:25px;text-align:center;">
<h2 style="color:white;margin:0;font-size:24px;">{bank_name}</h2>
</div>
<div style="padding:25px;">
<p style="font-size:15px;color:#333;">Bonjour <strong>{user.get_full_name() or user.username}</strong>,</p>
<p style="font-size:14px;color:#666;">Votre code de vérification:</p>
<div style="background:#f8f9fa;border:2px solid {bank_color};border-radius:8px;padding:20px;text-align:center;margin:20px 0;">
<div style="font-size:32px;font-weight:bold;color:{bank_color};letter-spacing:6px;">{otp_code}</div>
<p style="font-size:11px;color:#999;margin:8px 0 0 0;">Valable 10 minutes</p>
</div>
</div>
<div style="background:#f8f9fa;padding:15px;text-align:center;">
<p style="font-size:11px;color:#999;">Ceci est un mail automatique merci de ne pas y répondre</p>
<p style="font-size:12px;color:{bank_color};font-weight:bold;margin:5px 0 0 0;">{bank_name} - Tous droits réservés</p>
</div>
</div>
</body>
</html>"""
    
    email = EmailMultiAlternatives(subject=subject, body=f"Code: {otp_code}", from_email=f'{bank_name} <{settings.EMAIL_HOST_USER}>', to=[user.email])
    email.attach_alternative(html, "text/html")
    email.send(fail_silently=False)


def send_welcome_email(user, bank, temp_password):
    """Email de bienvenue avec lien de connexion"""
    login_url = f"https://flashcompte.onrender.com/login/{bank.slug}/"
    
    subject = f"{bank.name} - Bienvenue sur votre espace client"
    
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background-color:#f5f5f5;">
<div style="max-width:600px;margin:20px auto;background:white;border-radius:8px;overflow:hidden;">
<div style="background:linear-gradient(135deg,{bank.primary_color} 0%,{bank.secondary_color} 100%);padding:28px;text-align:center;border-bottom:4px solid {bank.secondary_color};">
<h1 style="color:white;margin:0;font-size:28px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;">{bank.name}</h1>
</div>
<div style="background:#2e7d32;padding:15px;text-align:center;">
<h1 style="color:white;margin:0;font-size:20px;">Bienvenue sur votre espace client</h1>
</div>
<div style="padding:25px;">
<p style="font-size:15px;color:#333;">Bonjour <strong>{user.get_full_name() or user.username}</strong>,</p>
<p style="font-size:14px;color:#666;line-height:1.6;">Votre compte {bank.name} a été créé avec succès!</p>
<p style="font-size:14px;color:#666;margin:20px 0 10px 0;"><strong>Vos identifiants de connexion:</strong></p>
<div style="background:#f8f9fa;border-left:4px solid {bank.primary_color};padding:15px;margin:15px 0;">
<p style="margin:0 0 8px 0;"><strong>Nom d'utilisateur:</strong> {user.username}</p>
<p style="margin:0;"><strong>Mot de passe:</strong> {temp_password}</p>
</div>
<p style="font-size:13px;color:#f57c00;background:#fff8e1;padding:12px;border-radius:6px;margin:15px 0;">⚠️ Changez ce mot de passe dès votre première connexion</p>
<div style="text-align:center;margin:25px 0;">
<a href="{login_url}" style="display:inline-block;background:linear-gradient(135deg,{bank.primary_color},{bank.secondary_color});color:white;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:15px;">Se connecter à {bank.name}</a>
</div>
<p style="font-size:12px;color:#999;background:#f0f7ff;padding:12px;border-left:3px solid #2196f3;border-radius:4px;margin-top:20px;">
ℹ️ Conservez ce lien de connexion: <br><strong>{login_url}</strong>
</p>
</div>
<div style="background:#f8f9fa;padding:15px;text-align:center;">
<p style="font-size:11px;color:#999;">Ceci est un mail automatique merci de ne pas y répondre</p>
<p style="font-size:12px;color:{bank.primary_color};font-weight:bold;margin:5px 0 0 0;">{bank.name} - Tous droits réservés</p>
</div>
</div>
</body>
</html>"""
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=f"Bienvenue sur {bank.name}!\n\nUsername: {user.username}\nPassword: {temp_password}\n\nConnectez-vous: {login_url}",
        from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>',
        to=[user.email]
    )
    email.attach_alternative(html, "text/html")
    email.send(fail_silently=True)
