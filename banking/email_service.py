"""
Service d'envoi d'emails pour les transactions bancaires
"""
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
import random
import base64
import os
from datetime import timedelta


# ─────────────────────────────────────────────
#  OTP
# ─────────────────────────────────────────────

def generate_otp_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(5)])


def create_otp(user, otp_type):
    from .models import OTPCode
    OTPCode.objects.filter(user=user, otp_type=otp_type, is_used=False).delete()
    code = generate_otp_code()
    expires_at = timezone.now() + timedelta(minutes=10)
    return OTPCode.objects.create(user=user, code=code, otp_type=otp_type, expires_at=expires_at)


def verify_otp(user, code, otp_type):
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


# ─────────────────────────────────────────────
#  LOGO — pièce jointe CID (compatible Gmail/Outlook)
# ─────────────────────────────────────────────

def _attach_logo(msg, bank):
    """
    Attache le logo de la banque en pièce jointe inline (CID).
    Retourne le tag <img> à insérer dans le HTML, ou '' si pas de logo.
    """
    try:
        if bank and bank.logo and hasattr(bank.logo, 'path') and os.path.exists(bank.logo.path):
            from email.mime.image import MIMEImage
            with open(bank.logo.path, 'rb') as f:
                logo_data = f.read()
            ext = os.path.splitext(bank.logo.path)[1].lower().lstrip('.')
            mime_sub = 'jpeg' if ext in ('jpg', 'jpeg') else ext
            img = MIMEImage(logo_data, _subtype=mime_sub)
            img.add_header('Content-ID', '<bank_logo>')
            img.add_header('Content-Disposition', 'inline', filename=f'logo.{ext}')
            msg.attach(img)
            return (
                '<img src="cid:bank_logo" alt="' + bank.name + '" '
                'style="max-height:48px;max-width:140px;object-fit:contain;display:block;" />'
            )
    except Exception as e:
        print(f'Logo attach error: {e}')
    return ''


# ─────────────────────────────────────────────
#  HELPERS HTML
# ─────────────────────────────────────────────

def _row(label, value, zebra=False):
    bg = '#f7f8fa' if zebra else '#ffffff'
    return (
        '<tr>'
        '<td style="padding:11px 16px;background:' + bg + ';border-bottom:1px solid #e8eaed;'
        'font-size:12px;color:#888;font-weight:600;width:38%;white-space:nowrap;">'
        + label +
        '</td>'
        '<td style="padding:11px 16px;background:' + bg + ';border-bottom:1px solid #e8eaed;'
        'font-size:13px;color:#1a1a2e;">'
        + str(value) +
        '</td>'
        '</tr>'
    )


def _build_email_html(bank, status_color, status_label, status_icon,
                      greeting_name, intro_text, amount_display,
                      primary_color, rows_html, extra_block='', logo_tag=''):
    from datetime import datetime
    year = datetime.now().year
    bank_secondary = getattr(bank, 'secondary_color', primary_color)

    # Bloc montant (optionnel)
    if amount_display:
        amount_block = (
            '<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            ' style="background:#f7f8fa;border:1px solid #e2e5ea;border-radius:4px;margin-bottom:20px;">'
            '<tr><td style="padding:20px;text-align:center;">'
            '<p style="margin:0 0 4px;font-size:10px;color:#999;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;">'
            'Montant de l\'op\u00e9ration'
            '</p>'
            '<p style="margin:0;font-size:36px;font-weight:800;color:' + primary_color + ';letter-spacing:-1px;">'
            + amount_display +
            '</p>'
            '</td></tr></table>'
        )
    else:
        amount_block = ''

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
</head>
<body style="margin:0;padding:0;background:#e9ebee;font-family:Arial,Helvetica,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#e9ebee;padding:20px 12px;">
  <tr><td align="center">

    <table width="580" cellpadding="0" cellspacing="0" border="0"
           style="max-width:580px;width:100%;background:#ffffff;border-radius:4px;
                  border:1px solid #dde1e7;">

      <!-- HEADER -->
      <tr>
        <td style="background:linear-gradient(135deg,{primary_color} 0%,{bank_secondary} 100%);
                    padding:18px 24px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="vertical-align:middle;">
                {logo_tag}
              </td>
              <td style="vertical-align:middle;padding-left:12px;">
                <span style="color:#ffffff;font-size:18px;font-weight:700;
                              letter-spacing:0.3px;text-transform:uppercase;">
                  {bank.name}
                </span><br/>
                <span style="color:rgba(255,255,255,0.75);font-size:11px;">
                  Service Client
                </span>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- STATUS BANNER -->
      <tr>
        <td style="background:{status_color};padding:12px 24px;">
          <span style="color:#ffffff;font-size:15px;font-weight:700;">
            {status_icon}&nbsp; {status_label}
          </span>
        </td>
      </tr>

      <!-- BODY -->
      <tr>
        <td style="padding:24px 24px 16px;">

          <p style="margin:0 0 14px;font-size:15px;color:#1a1a2e;font-weight:600;">
            Bonjour {greeting_name},
          </p>
          <p style="margin:0 0 20px;font-size:13px;color:#555;line-height:1.6;">
            {intro_text}
          </p>

          {amount_block}

          <!-- Tableau de détails -->
          <table width="100%" cellpadding="0" cellspacing="0" border="0"
                 style="border-collapse:collapse;border:1px solid #e8eaed;border-radius:4px;
                         overflow:hidden;margin-bottom:20px;">
            {rows_html}
          </table>

          {extra_block}

          <!-- Avertissement sécurité -->
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="background:#f7f8fa;border-left:3px solid {primary_color};
                           padding:10px 14px;">
                <p style="margin:0;font-size:11px;color:#777;line-height:1.5;">
                  &#128274; Si vous n'êtes pas à l'origine de cette opération,
                  contactez immédiatement votre conseiller bancaire.
                </p>
              </td>
            </tr>
          </table>

        </td>
      </tr>

      <!-- FOOTER -->
      <tr>
        <td style="border-top:1px solid #e8eaed;background:#f7f8fa;
                    padding:14px 24px;text-align:center;">
          <p style="margin:0 0 4px;font-size:11px;color:#aaa;">
            Ce message est généré automatiquement — merci de ne pas y répondre.
          </p>
          <p style="margin:0;font-size:11px;font-weight:700;color:{primary_color};">
            &copy; {year} {bank.name} &mdash; Tous droits réservés
          </p>
        </td>
      </tr>

    </table>

    <p style="margin:10px 0 0;font-size:10px;color:#bbb;text-align:center;">
      Vous recevez cet e-mail car vous êtes titulaire d'un compte {bank.name}.
    </p>

  </td></tr>
</table>

</body>
</html>"""


# ─────────────────────────────────────────────
#  EMAIL 1 — Virement émis (titulaire)
# ─────────────────────────────────────────────

def send_transaction_email_to_sender(transaction):
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    primary = bank.primary_color

    status_map = {
        'PENDING':   ('#D97706', 'Virement en attente de validation', '&#9203;'),
        'COMPLETED': ('#16A34A', 'Virement confirm&#233;',            '&#10003;'),
        'REJECTED':  ('#DC2626', 'Virement rejet&#233;',              '&#10007;'),
    }
    status_color, status_label, status_icon = status_map.get(
        transaction.status, ('#6B7280', transaction.status, '&#8505;')
    )

    rows = (
        _row("Donneur d'ordre",   user.get_full_name() or user.username,             False) +
        _row('Compte d&#233;bit&#233;',
             transaction.account.get_account_type_display() + ' &bull; ' + transaction.account.account_number, True) +
        _row('B&#233;n&#233;ficiaire', transaction.recipient or '&#8212;',           False) +
        _row('IBAN destinataire',
             '<span style="font-family:monospace;font-size:12px;">' + (transaction.recipient_iban or '&#8212;') + '</span>', True) +
        _row('R&#233;f&#233;rence',   transaction.reference or '&#8212;',            False) +
        _row('Motif',                 transaction.description or '&#8212;',          True) +
        _row('Date',                  transaction.created_at.strftime('%d/%m/%Y &#224; %H:%M'), False) +
        _row('N&#176; bordereau',     'T' + str(transaction.id).zfill(6),            True)
    )

    plain = (
        f'{bank.name} — {status_label}\n\n'
        f'Bonjour {user.get_full_name() or user.username},\n\n'
        f'Virement de {transaction.amount} {symbol}.\n'
        f'Référence : T{str(transaction.id).zfill(6)}\n\n{bank.name}'
    )

    msg = EmailMultiAlternatives(
        subject=f'{bank.name} — {status_label}',
        body=plain,
        from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>',
        to=[user.email],
    )
    msg.mixed_subtype = 'related'
    logo_tag = _attach_logo(msg, bank)

    html = _build_email_html(
        bank=bank,
        status_color=status_color,
        status_label=status_label,
        status_icon=status_icon,
        greeting_name=user.get_full_name() or user.username,
        intro_text=(
            f'Nous vous informons qu\'un virement de <strong>{transaction.amount} {symbol}</strong> '
            f'a &#233;t&#233; initié depuis votre compte '
            f'<strong>{transaction.account.get_account_type_display()}</strong>. '
            f'Vous recevrez le statut final sous 48&nbsp;h maximum.'
        ),
        amount_display=f'{transaction.amount} {symbol}',
        primary_color=primary,
        rows_html=rows,
        logo_tag=logo_tag,
    )
    msg.attach_alternative(html, 'text/html')

    try:
        from .pdf_generator import generate_transaction_receipt_pdf
        pdf = generate_transaction_receipt_pdf(transaction)
        msg.attach(f'bordereau_T{str(transaction.id).zfill(6)}.pdf', pdf, 'application/pdf')
    except Exception as e:
        print(f'Erreur PDF: {e}')

    msg.send(fail_silently=False)


# ─────────────────────────────────────────────
#  EMAIL 2 — Virement reçu (bénéficiaire)
# ─────────────────────────────────────────────

def send_transaction_email_to_beneficiary(transaction, beneficiary_email, beneficiary_name):
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    primary = bank.primary_color

    rows = (
        _row('&#201;metteur',        user.get_full_name() or user.username, False) +
        _row('Banque &#233;mettrice', bank.name,                            True) +
        _row('Motif',                transaction.description or '&#8212;',  False) +
        _row('Date de r&#233;ception', transaction.created_at.strftime('%d/%m/%Y &#224; %H:%M'), True) +
        _row('R&#233;f&#233;rence',  'T' + str(transaction.id).zfill(6),    False)
    )

    plain = f'Virement reçu de {user.get_full_name() or user.username} : {transaction.amount} {symbol}'

    msg = EmailMultiAlternatives(
        subject=f'{bank.name} — Virement reçu de {user.get_full_name() or user.username}',
        body=plain,
        from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>',
        to=[beneficiary_email],
    )
    msg.mixed_subtype = 'related'
    logo_tag = _attach_logo(msg, bank)

    html = _build_email_html(
        bank=bank,
        status_color='#16A34A',
        status_label='Virement re&#231;u',
        status_icon='&#128176;',
        greeting_name=beneficiary_name,
        intro_text=(
            f'<strong>{user.get_full_name() or user.username}</strong> vous a envoy&#233; un virement '
            f'de <strong>{transaction.amount} {symbol}</strong> via <strong>{bank.name}</strong>. '
            f'Les fonds sont disponibles sur votre compte.'
        ),
        amount_display=f'{transaction.amount} {symbol}',
        primary_color=primary,
        rows_html=rows,
        logo_tag=logo_tag,
    )
    msg.attach_alternative(html, 'text/html')

    try:
        from .pdf_generator import generate_transaction_receipt_pdf
        pdf = generate_transaction_receipt_pdf(transaction)
        msg.attach(f'bordereau_T{str(transaction.id).zfill(6)}.pdf', pdf, 'application/pdf')
    except Exception:
        pass

    msg.send(fail_silently=False)


# ─────────────────────────────────────────────
#  EMAIL 3 — Transaction confirmée
# ─────────────────────────────────────────────

def send_transaction_confirmation_email(transaction):
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    primary = bank.primary_color

    confirmed_at = (
        transaction.confirmed_at.strftime('%d/%m/%Y &#224; %H:%M')
        if transaction.confirmed_at else '&#8212;'
    )

    rows = (
        _row('Type',                transaction.get_transaction_type_display(), False) +
        _row('Compte',
             transaction.account.get_account_type_display() + ' &bull; ' + transaction.account.account_number, True) +
        _row('B&#233;n&#233;ficiaire', transaction.recipient or '&#8212;',     False) +
        _row('Solde apr&#232;s op.', str(transaction.balance_after) + ' ' + symbol, True) +
        _row('Date confirmation',   confirmed_at,                               False) +
        _row('N&#176; bordereau',   'T' + str(transaction.id).zfill(6),         True)
    )

    plain = f'{bank.name} — Transaction confirmée : {transaction.amount} {symbol}'

    msg = EmailMultiAlternatives(
        subject=f'{bank.name} — Transaction confirmée',
        body=plain,
        from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>',
        to=[user.email],
    )
    msg.mixed_subtype = 'related'
    logo_tag = _attach_logo(msg, bank)

    html = _build_email_html(
        bank=bank,
        status_color='#16A34A',
        status_label='Transaction confirm&#233;e',
        status_icon='&#10003;',
        greeting_name=user.get_full_name() or user.username,
        intro_text=(
            f'Votre transaction de <strong>{transaction.amount} {symbol}</strong> '
            f'a &#233;t&#233; <strong>confirm&#233;e avec succ&#232;s</strong>. '
            f'Le bordereau est joint en pi&#232;ce jointe.'
        ),
        amount_display=f'{transaction.amount} {symbol}',
        primary_color=primary,
        rows_html=rows,
        logo_tag=logo_tag,
    )
    msg.attach_alternative(html, 'text/html')

    try:
        from .pdf_generator import generate_transaction_receipt_pdf
        pdf = generate_transaction_receipt_pdf(transaction)
        msg.attach(f'bordereau_T{str(transaction.id).zfill(6)}.pdf', pdf, 'application/pdf')
    except Exception:
        pass

    msg.send(fail_silently=False)


# ─────────────────────────────────────────────
#  EMAIL 4 — Transaction rejetée
# ─────────────────────────────────────────────

def send_transaction_rejection_email(transaction):
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    primary = bank.primary_color

    rejected_at = (
        transaction.rejected_at.strftime('%d/%m/%Y &#224; %H:%M')
        if transaction.rejected_at else '&#8212;'
    )
    frais = (
        str(transaction.rejection_fee) + ' ' + symbol
        if transaction.rejection_fee and transaction.rejection_fee > 0
        else 'Aucun'
    )

    rows = (
        _row('Type',              transaction.get_transaction_type_display(), False) +
        _row('Montant rejet&#233;', str(transaction.amount) + ' ' + symbol,  True) +
        _row('Motif du rejet',    transaction.rejection_reason or '&#8212;',  False) +
        _row('Frais de rejet',    frais,                                       True) +
        _row('Solde apr&#232;s op.', str(transaction.balance_after) + ' ' + symbol, False) +
        _row('Date du rejet',     rejected_at,                                True) +
        _row('N&#176; bordereau', 'T' + str(transaction.id).zfill(6),         False)
    )

    refund_block = (
        '<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:16px;">'
        '<tr><td style="background:#FEF2F2;border-left:3px solid #DC2626;padding:12px 14px;">'
        '<p style="margin:0 0 4px;font-size:12px;font-weight:700;color:#DC2626;">&#9888; Remboursement effectué</p>'
        '<p style="margin:0;font-size:12px;color:#666;line-height:1.5;">'
        'Le montant de <strong>' + str(transaction.amount) + ' ' + symbol + '</strong> '
        'a été recrédité sur votre compte.'
        + (' Des frais de <strong>' + str(transaction.rejection_fee) + ' ' + symbol + '</strong> ont été prélevés.'
           if transaction.rejection_fee and transaction.rejection_fee > 0 else '') +
        '</p></td></tr></table>'
    )

    plain = f'{bank.name} — Transaction rejetée : {transaction.amount} {symbol}'

    msg = EmailMultiAlternatives(
        subject=f'{bank.name} — Transaction rejetée',
        body=plain,
        from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>',
        to=[user.email],
    )
    msg.mixed_subtype = 'related'
    logo_tag = _attach_logo(msg, bank)

    html = _build_email_html(
        bank=bank,
        status_color='#DC2626',
        status_label='Transaction rejet&#233;e',
        status_icon='&#10007;',
        greeting_name=user.get_full_name() or user.username,
        intro_text=(
            f'Votre transaction de <strong>{transaction.amount} {symbol}</strong> a &#233;t&#233; '
            f'<strong>rejet&#233;e par {bank.name}</strong>. '
            f'Le montant a &#233;t&#233; rembours&#233; sur votre compte.'
        ),
        amount_display=f'{transaction.amount} {symbol}',
        primary_color=primary,
        rows_html=rows,
        extra_block=refund_block,
        logo_tag=logo_tag,
    )
    msg.attach_alternative(html, 'text/html')

    try:
        from .pdf_generator import generate_transaction_receipt_pdf
        pdf = generate_transaction_receipt_pdf(transaction)
        msg.attach(f'bordereau_rejet_T{str(transaction.id).zfill(6)}.pdf', pdf, 'application/pdf')
    except Exception:
        pass

    msg.send(fail_silently=False)


# ─────────────────────────────────────────────
#  EMAIL 5 — Code OTP
# ─────────────────────────────────────────────

def send_otp_email(user, otp_code, otp_type):
    account = user.bank_accounts.first()
    bank = account.bank if account and account.bank else None
    bank_name = bank.name if bank else 'Banque'
    primary = bank.primary_color if bank else '#1A56DB'
    bank_secondary = getattr(bank, 'secondary_color', primary) if bank else primary

    otp_label_map = {
        'LOGIN':           'Connexion &#224; votre espace',
        'CHANGE_PASSWORD': 'Changement de mot de passe',
        'EDIT_PROFILE':    'Modification de profil',
    }
    otp_label = otp_label_map.get(otp_type, 'V&#233;rification')

    from datetime import datetime
    year = datetime.now().year

    plain = f'Code de vérification {bank_name}: {otp_code} (valable 10 min)'

    msg = EmailMultiAlternatives(
        subject=f'{bank_name} — Votre code de vérification',
        body=plain,
        from_email=f'{bank_name} <{settings.EMAIL_HOST_USER}>',
        to=[user.email],
    )
    msg.mixed_subtype = 'related'
    logo_tag = _attach_logo(msg, bank) if bank else ''

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#e9ebee;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#e9ebee;padding:20px 12px;">
  <tr><td align="center">
    <table width="500" cellpadding="0" cellspacing="0" border="0"
           style="max-width:500px;width:100%;background:#ffffff;border-radius:4px;border:1px solid #dde1e7;">

      <!-- HEADER -->
      <tr>
        <td style="background:linear-gradient(135deg,{primary} 0%,{bank_secondary} 100%);padding:16px 20px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="vertical-align:middle;">{logo_tag}</td>
              <td style="vertical-align:middle;padding-left:10px;">
                <span style="color:#fff;font-size:17px;font-weight:700;text-transform:uppercase;">{bank_name}</span><br/>
                <span style="color:rgba(255,255,255,0.75);font-size:11px;">S&#233;curit&#233; &amp; Acc&#232;s</span>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- STATUS -->
      <tr>
        <td style="background:#1E3A5F;padding:11px 20px;">
          <span style="color:#fff;font-size:14px;font-weight:700;">&#128272; {otp_label}</span>
        </td>
      </tr>

      <!-- BODY -->
      <tr>
        <td style="padding:24px 20px;">
          <p style="margin:0 0 12px;font-size:15px;color:#1a1a2e;font-weight:600;">
            Bonjour {user.get_full_name() or user.username},
          </p>
          <p style="margin:0 0 20px;font-size:13px;color:#555;line-height:1.6;">
            Voici votre code de v&#233;rification &#224; usage unique,
            valable <strong>10 minutes</strong>.
          </p>

          <!-- Code -->
          <table width="100%" cellpadding="0" cellspacing="0" border="0"
                 style="background:#f7f8fa;border:2px solid {primary};border-radius:4px;margin-bottom:20px;">
            <tr>
              <td style="padding:22px 16px;text-align:center;">
                <p style="margin:0 0 6px;font-size:10px;color:#999;text-transform:uppercase;letter-spacing:2px;font-weight:600;">
                  Code de v&#233;rification
                </p>
                <p style="margin:0;font-size:44px;font-weight:800;color:{primary};letter-spacing:14px;font-variant-numeric:tabular-nums;">
                  {otp_code}
                </p>
                <p style="margin:10px 0 0;font-size:11px;color:#DC2626;font-weight:600;">
                  &#9200; Expire dans 10 minutes
                </p>
              </td>
            </tr>
          </table>

          <!-- Warning -->
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="background:#FFFBEB;border-left:3px solid #D97706;padding:10px 14px;">
                <p style="margin:0;font-size:11px;color:#92400E;line-height:1.5;">
                  &#9888; <strong>Ne partagez jamais ce code.</strong>
                  {bank_name} ne vous demandera jamais ce code par t&#233;l&#233;phone.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- FOOTER -->
      <tr>
        <td style="border-top:1px solid #e8eaed;background:#f7f8fa;padding:12px 20px;text-align:center;">
          <p style="margin:0 0 3px;font-size:10px;color:#aaa;">Message automatique — ne pas r&#233;pondre.</p>
          <p style="margin:0;font-size:11px;font-weight:700;color:{primary};">&copy; {year} {bank_name}</p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=False)


# ─────────────────────────────────────────────
#  EMAIL 6 — Bienvenue
# ─────────────────────────────────────────────

def send_welcome_email(user, bank, temp_password):
    from django.conf import settings as djsettings
    domain = djsettings.ALLOWED_HOSTS[0] if djsettings.ALLOWED_HOSTS else 'localhost:8000'
    login_url = f'https://{domain}/login/{bank.slug}/'
    primary = bank.primary_color
    bank_secondary = getattr(bank, 'secondary_color', primary)

    rows = (
        _row("Nom d'utilisateur", '<strong>' + user.username + '</strong>',                False) +
        _row('Mot de passe',      '<span style="font-family:monospace;">' + temp_password + '</span>', True) +
        _row('Banque',            bank.name,                                               False) +
        _row('Titulaire',         user.get_full_name() or user.username,                  True)
    )

    cta_block = (
        '<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:20px;">'
        '<tr><td align="center" style="padding-bottom:14px;">'
        '<a href="' + login_url + '" style="display:inline-block;'
        'background:linear-gradient(135deg,' + primary + ' 0%,' + bank_secondary + ' 100%);'
        'color:#ffffff;padding:13px 32px;border-radius:4px;text-decoration:none;'
        'font-weight:700;font-size:14px;">Se connecter &#224; ' + bank.name + '</a>'
        '</td></tr>'
        '<tr><td style="background:#EFF6FF;border-left:3px solid #3B82F6;padding:10px 14px;">'
        '<p style="margin:0;font-size:11px;color:#1E40AF;line-height:1.5;">'
        '&#8505; Conservez ce lien : <strong>' + login_url + '</strong></p>'
        '</td></tr>'
        '<tr><td style="padding-top:10px;">'
        '<table width="100%" cellpadding="0" cellspacing="0" border="0">'
        '<tr><td style="background:#FFFBEB;border-left:3px solid #D97706;padding:10px 14px;">'
        '<p style="margin:0;font-size:11px;color:#92400E;line-height:1.5;">'
        '&#9888; <strong>Changez votre mot de passe</strong> d&#232;s votre premi&#232;re connexion.</p>'
        '</td></tr></table>'
        '</td></tr></table>'
    )

    plain = (
        f'Bienvenue sur {bank.name}!\n\n'
        f"Nom d'utilisateur: {user.username}\n"
        f'Mot de passe: {temp_password}\n\n'
        f'Connectez-vous: {login_url}'
    )

    msg = EmailMultiAlternatives(
        subject=f'{bank.name} — Bienvenue sur votre espace client',
        body=plain,
        from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>',
        to=[user.email],
    )
    msg.mixed_subtype = 'related'
    logo_tag = _attach_logo(msg, bank)

    html = _build_email_html(
        bank=bank,
        status_color='#16A34A',
        status_label='Bienvenue sur votre espace client',
        status_icon='&#127881;',
        greeting_name=user.get_full_name() or user.username,
        intro_text=(
            f'Votre compte <strong>{bank.name}</strong> a &#233;t&#233; cr&#233;&#233; avec succ&#232;s. '
            f'Retrouvez ci-dessous vos identifiants de connexion.'
        ),
        amount_display='',
        primary_color=primary,
        rows_html=rows,
        extra_block=cta_block,
        logo_tag=logo_tag,
    )
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=False)
