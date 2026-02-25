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


# ─────────────────────────────────────────────
#  HELPER : logo encodé en base64
# ─────────────────────────────────────────────

def _get_logo_html(bank):
    """Retourne le tag <img> du logo en base64 ou un texte fallback."""
    try:
        if bank.logo and hasattr(bank.logo, 'path') and os.path.exists(bank.logo.path):
            with open(bank.logo.path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')
            ext = os.path.splitext(bank.logo.path)[1].lower().lstrip('.')
            mime = 'jpeg' if ext in ('jpg', 'jpeg') else ext
            return (
                f'<img src="data:image/{mime};base64,{data}" '
                f'alt="{bank.name}" '
                f'style="max-height:60px;max-width:180px;object-fit:contain;display:block;margin:0 auto 12px;" />'
            )
    except Exception:
        pass
    return ''


# ─────────────────────────────────────────────
#  HELPER : constructeur HTML commun
# ─────────────────────────────────────────────

def _build_email_html(
    bank,
    status_color,
    status_label,
    status_icon,
    greeting_name,
    intro_text,
    amount_display,
    primary_color,
    rows_html,
    extra_block='',
):
    """Construit le HTML complet d'un email style bancaire professionnel."""
    from datetime import datetime
    year = datetime.now().year
    logo_html = _get_logo_html(bank)
    bank_secondary = getattr(bank, 'secondary_color', primary_color)

    # Bloc montant construit en dehors du f-string (interdit d'utiliser \' dans une expression f-string Python <3.12)
    if amount_display:
        amount_label = "Montant de l\u2019op\u00e9ration"
        amount_card_html = (
            '<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            ' style="background:linear-gradient(135deg,#f8f9fa 0%,#eef0f3 100%);'
            'border-radius:12px;border:1px solid #e2e5ea;margin-bottom:28px;">'
            '<tr><td style="padding:28px;text-align:center;">'
            '<p style="margin:0 0 6px;font-size:11px;color:#888888;'
            'text-transform:uppercase;letter-spacing:1.5px;font-weight:600;">'
            + amount_label +
            '</p>'
            '<p style="margin:0;font-size:40px;font-weight:800;color:' + primary_color + ';letter-spacing:-1px;">'
            + amount_display +
            '</p></td></tr></table>'
        )
    else:
        amount_card_html = ''

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1.0" />
  <title>{bank.name}</title>
</head>
<body style="margin:0;padding:0;background-color:#f0f0f0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">

  <!-- Wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f0f0f0;padding:32px 16px;">
    <tr>
      <td align="center">

        <!-- Email card -->
        <table width="600" cellpadding="0" cellspacing="0" border="0"
               style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;
                      overflow:hidden;box-shadow:0 6px 32px rgba(0,0,0,0.10);">

          <!-- ── HEADER ── -->
          <tr>
            <td style="background:linear-gradient(135deg,{primary_color} 0%,{bank_secondary} 100%);
                        padding:36px 40px 28px;text-align:center;">
              {logo_html}
              <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;
                          letter-spacing:0.5px;text-transform:uppercase;
                          text-shadow:0 1px 3px rgba(0,0,0,0.25);">
                {bank.name}
              </h1>
              <p style="margin:6px 0 0;color:rgba(255,255,255,0.80);font-size:13px;">
                Service Client en ligne
              </p>
            </td>
          </tr>

          <!-- ── STATUS BANNER ── -->
          <tr>
            <td style="background:{status_color};padding:18px 40px;text-align:center;">
              <span style="color:#ffffff;font-size:17px;font-weight:700;letter-spacing:0.3px;">
                {status_icon}&nbsp;&nbsp;{status_label}
              </span>
            </td>
          </tr>

          <!-- ── BODY ── -->
          <tr>
            <td style="padding:36px 40px 28px;">

              <!-- Greeting -->
              <p style="margin:0 0 18px;font-size:16px;color:#1a1a2e;font-weight:600;">
                Bonjour {greeting_name},
              </p>

              <!-- Intro -->
              <p style="margin:0 0 28px;font-size:14px;color:#555555;line-height:1.7;">
                {intro_text}
              </p>

              <!-- Amount card (masqué si vide) -->
              {amount_card_html}

              <!-- Details table -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="border-collapse:collapse;border-radius:10px;overflow:hidden;
                             border:1px solid #e8eaed;">
                {rows_html}
              </table>

              {extra_block}

              <!-- Security notice -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="margin-top:28px;">
                <tr>
                  <td style="background:#f8f9fa;border-left:4px solid {primary_color};
                               padding:14px 16px;border-radius:0 8px 8px 0;">
                    <p style="margin:0;font-size:12px;color:#777777;line-height:1.6;">
                      🔒 <strong>Sécurité :</strong> Si vous n'êtes pas à l'origine de cette opération,
                      contactez immédiatement votre conseiller bancaire.
                    </p>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- ── DIVIDER ── -->
          <tr>
            <td style="padding:0 40px;">
              <div style="height:1px;background:#eeeeee;"></div>
            </td>
          </tr>

          <!-- ── FOOTER ── -->
          <tr>
            <td style="padding:24px 40px;text-align:center;background:#fafafa;">
              <p style="margin:0 0 6px;font-size:12px;color:#aaaaaa;">
                Ce message est généré automatiquement &mdash; merci de ne pas y répondre.
              </p>
              <p style="margin:0;font-size:12px;font-weight:700;color:{primary_color};">
                &copy; {year} {bank.name} &mdash; Tous droits réservés
              </p>
            </td>
          </tr>

        </table>

        <!-- Below-card notice -->
        <p style="margin:20px 0 0;font-size:11px;color:#bbbbbb;text-align:center;">
          Vous recevez cet e-mail car vous êtes titulaire d'un compte {bank.name}.
        </p>

      </td>
    </tr>
  </table>

</body>
</html>"""


def _row(label, value, zebra=False):
    """Génère une ligne du tableau de détails."""
    bg = '#f8f9fa' if zebra else '#ffffff'
    return f"""
    <tr>
      <td style="padding:13px 18px;background:{bg};border-bottom:1px solid #e8eaed;
                  font-size:13px;color:#888888;font-weight:600;width:40%;
                  white-space:nowrap;">
        {label}
      </td>
      <td style="padding:13px 18px;background:{bg};border-bottom:1px solid #e8eaed;
                  font-size:13px;color:#1a1a2e;font-weight:500;">
        {value}
      </td>
    </tr>"""


# ─────────────────────────────────────────────
#  EMAIL 1 — Virement émis (vers le titulaire)
# ─────────────────────────────────────────────

def send_transaction_email_to_sender(transaction):
    """Email au titulaire lors d'un virement."""
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    primary = bank.primary_color

    status_map = {
        'PENDING':   ('#F59E0B', 'Virement en attente de validation', '⏳'),
        'COMPLETED': ('#16A34A', 'Virement confirmé',                 '✅'),
        'REJECTED':  ('#DC2626', 'Virement rejeté',                   '❌'),
    }
    status_color, status_label, status_icon = status_map.get(
        transaction.status, ('#6B7280', transaction.status, 'ℹ️')
    )

    rows = (
        _row('Donneur d\'ordre',   f'<strong>{user.get_full_name() or user.username}</strong>', False) +
        _row('Compte débité',      f'{transaction.account.get_account_type_display()} &bull; {transaction.account.account_number}', True) +
        _row('Bénéficiaire',       transaction.recipient or '—',                 False) +
        _row('IBAN destinataire',  f'<code style="font-size:12px;">{transaction.recipient_iban or "—"}</code>', True) +
        _row('Référence',          transaction.reference or '—',                 False) +
        _row('Motif',              transaction.description or '—',               True) +
        _row('Date',               transaction.created_at.strftime('%d %B %Y à %H:%M'), False) +
        _row('Référence interne',  f'T{str(transaction.id).zfill(6)}',           True)
    )

    html = _build_email_html(
        bank=bank,
        status_color=status_color,
        status_label=status_label,
        status_icon=status_icon,
        greeting_name=user.get_full_name() or user.username,
        intro_text=(
            f'Nous vous informons qu\'un virement d\'un montant de '
            f'<strong>{transaction.amount} {symbol}</strong> a été initié depuis votre '
            f'compte <strong>{transaction.account.get_account_type_display()}</strong>. '
            f'Vous recevrez le statut final sous 48&nbsp;h maximum.'
        ),
        amount_display=f'{transaction.amount} {symbol}',
        primary_color=primary,
        rows_html=rows,
    )

    plain = (
        f'{bank.name} — {status_label}\n\n'
        f'Bonjour {user.get_full_name() or user.username},\n\n'
        f'Virement de {transaction.amount} {symbol} depuis votre compte.\n'
        f'Référence : T{str(transaction.id).zfill(6)}\n\n{bank.name}'
    )

    msg = EmailMultiAlternatives(
        subject=f'{bank.name} — {status_label}',
        body=plain,
        from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>',
        to=[user.email],
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
#  EMAIL 2 — Virement reçu (vers le bénéficiaire)
# ─────────────────────────────────────────────

def send_transaction_email_to_beneficiary(transaction, beneficiary_email, beneficiary_name):
    """Email au bénéficiaire lors de la réception d'un virement."""
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    primary = bank.primary_color

    rows = (
        _row('Émetteur',          f'<strong>{user.get_full_name() or user.username}</strong>', False) +
        _row('Banque émettrice',  bank.name,                                                   True) +
        _row('Motif',             transaction.description or '—',                              False) +
        _row('Date de réception', transaction.created_at.strftime('%d %B %Y à %H:%M'),        True) +
        _row('Référence',         f'T{str(transaction.id).zfill(6)}',                         False)
    )

    html = _build_email_html(
        bank=bank,
        status_color='#16A34A',
        status_label='Virement reçu',
        status_icon='💳',
        greeting_name=beneficiary_name,
        intro_text=(
            f'<strong>{user.get_full_name() or user.username}</strong> vous a envoyé un virement '
            f'd\'un montant de <strong>{transaction.amount} {symbol}</strong> via <strong>{bank.name}</strong>. '
            f'Les fonds sont disponibles sur votre compte.'
        ),
        amount_display=f'{transaction.amount} {symbol}',
        primary_color=primary,
        rows_html=rows,
    )

    plain = f'Virement reçu de {user.get_full_name() or user.username} : {transaction.amount} {symbol}'

    msg = EmailMultiAlternatives(
        subject=f'{bank.name} — Virement reçu de {user.get_full_name() or user.username}',
        body=plain,
        from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>',
        to=[beneficiary_email],
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
    """Email de confirmation de transaction."""
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    primary = bank.primary_color

    rows = (
        _row('Type',             transaction.get_transaction_type_display(), False) +
        _row('Compte',           f'{transaction.account.get_account_type_display()} &bull; {transaction.account.account_number}', True) +
        _row('Bénéficiaire',     transaction.recipient or '—',              False) +
        _row('Solde après op.',  f'{transaction.balance_after} {symbol}',   True) +
        _row('Date confirmation', transaction.confirmed_at.strftime('%d %B %Y à %H:%M') if transaction.confirmed_at else '—', False) +
        _row('Référence',        f'T{str(transaction.id).zfill(6)}',        True)
    )

    html = _build_email_html(
        bank=bank,
        status_color='#16A34A',
        status_label='Transaction confirmée',
        status_icon='✅',
        greeting_name=user.get_full_name() or user.username,
        intro_text=(
            f'Votre transaction de <strong>{transaction.amount} {symbol}</strong> a été '
            f'<strong>confirmée avec succès</strong>. Le bordereau est joint en pièce jointe.'
        ),
        amount_display=f'{transaction.amount} {symbol}',
        primary_color=primary,
        rows_html=rows,
    )

    plain = f'{bank.name} — Transaction confirmée : {transaction.amount} {symbol}'

    msg = EmailMultiAlternatives(
        subject=f'{bank.name} — Transaction confirmée',
        body=plain,
        from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>',
        to=[user.email],
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
    """Email de rejet de transaction."""
    user = transaction.account.user
    bank = transaction.account.bank
    from .utils import get_currency_symbol
    symbol = get_currency_symbol(transaction.account.currency)
    primary = bank.primary_color

    rows = (
        _row('Type',           transaction.get_transaction_type_display(), False) +
        _row('Montant rejeté', f'{transaction.amount} {symbol}',           True) +
        _row('Motif du rejet', transaction.rejection_reason or '—',        False) +
        _row('Frais de rejet', f'{transaction.rejection_fee} {symbol}' if transaction.rejection_fee and transaction.rejection_fee > 0 else 'Aucun', True) +
        _row('Solde après op.', f'{transaction.balance_after} {symbol}',   False) +
        _row('Date du rejet',  transaction.rejected_at.strftime('%d %B %Y à %H:%M') if transaction.rejected_at else '—', True) +
        _row('Référence',      f'T{str(transaction.id).zfill(6)}',         False)
    )

    refund_block = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:24px;">
      <tr>
        <td style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:18px 20px;">
          <p style="margin:0 0 6px;font-size:13px;font-weight:700;color:#DC2626;">
            ⚠️ Remboursement effectué
          </p>
          <p style="margin:0;font-size:13px;color:#6B7280;line-height:1.6;">
            Le montant de <strong>{transaction.amount} {symbol}</strong> a été
            recrédité sur votre compte.
            {"Des frais de rejet de <strong>" + str(transaction.rejection_fee) + " " + symbol + "</strong> ont été prélevés." if transaction.rejection_fee and transaction.rejection_fee > 0 else ""}
          </p>
        </td>
      </tr>
    </table>"""

    html = _build_email_html(
        bank=bank,
        status_color='#DC2626',
        status_label='Transaction rejetée',
        status_icon='❌',
        greeting_name=user.get_full_name() or user.username,
        intro_text=(
            f'Nous vous informons que votre transaction de '
            f'<strong>{transaction.amount} {symbol}</strong> a été '
            f'<strong>rejetée par {bank.name}</strong>. Le montant a été remboursé sur votre compte.'
        ),
        amount_display=f'{transaction.amount} {symbol}',
        primary_color=primary,
        rows_html=rows,
        extra_block=refund_block,
    )

    plain = f'{bank.name} — Transaction rejetée : {transaction.amount} {symbol}. Motif : {transaction.rejection_reason}'

    msg = EmailMultiAlternatives(
        subject=f'{bank.name} — Transaction rejetée',
        body=plain,
        from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>',
        to=[user.email],
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
    """Email avec code OTP."""
    account = user.bank_accounts.first()
    bank = account.bank if account and account.bank else None
    bank_name = bank.name if bank else 'Banque'
    primary = bank.primary_color if bank else '#1A56DB'
    bank_secondary = getattr(bank, 'secondary_color', primary) if bank else primary
    logo_html = _get_logo_html(bank) if bank else ''

    otp_label_map = {
        'LOGIN':           ('Connexion à votre espace', '🔑'),
        'CHANGE_PASSWORD': ('Changement de mot de passe', '🔒'),
        'EDIT_PROFILE':    ('Modification de profil', '👤'),
    }
    otp_label, otp_icon = otp_label_map.get(otp_type, ('Vérification', '🔐'))

    from datetime import datetime
    year = datetime.now().year

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1.0" />
</head>
<body style="margin:0;padding:0;background:#f0f0f0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f0f0f0;padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="520" cellpadding="0" cellspacing="0" border="0"
               style="max-width:520px;width:100%;background:#ffffff;border-radius:14px;
                      overflow:hidden;box-shadow:0 6px 32px rgba(0,0,0,0.10);">

          <!-- HEADER -->
          <tr>
            <td style="background:linear-gradient(135deg,{primary} 0%,{bank_secondary} 100%);
                        padding:32px 40px 24px;text-align:center;">
              {logo_html}
              <h1 style="margin:0;color:#ffffff;font-size:20px;font-weight:700;
                          text-transform:uppercase;letter-spacing:0.5px;">
                {bank_name}
              </h1>
              <p style="margin:6px 0 0;color:rgba(255,255,255,0.80);font-size:12px;">
                Service de sécurité
              </p>
            </td>
          </tr>

          <!-- STATUS -->
          <tr>
            <td style="background:#1E3A5F;padding:16px 40px;text-align:center;">
              <span style="color:#ffffff;font-size:16px;font-weight:700;">
                {otp_icon}&nbsp;&nbsp;{otp_label}
              </span>
            </td>
          </tr>

          <!-- BODY -->
          <tr>
            <td style="padding:36px 40px 28px;text-align:center;">
              <p style="margin:0 0 10px;font-size:16px;color:#1a1a2e;font-weight:600;text-align:left;">
                Bonjour {user.get_full_name() or user.username},
              </p>
              <p style="margin:0 0 28px;font-size:14px;color:#555555;line-height:1.7;text-align:left;">
                Voici votre code de vérification à usage unique. Il est valable pendant
                <strong>10 minutes</strong>.
              </p>

              <!-- Code OTP -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="background:linear-gradient(135deg,#f8f9fa 0%,#eef0f3 100%);
                             border-radius:14px;border:2px solid {primary};margin-bottom:28px;">
                <tr>
                  <td style="padding:30px 20px;text-align:center;">
                    <p style="margin:0 0 10px;font-size:11px;color:#888888;
                               text-transform:uppercase;letter-spacing:2px;font-weight:600;">
                      Code de vérification
                    </p>
                    <p style="margin:0;font-size:48px;font-weight:800;color:{primary};
                               letter-spacing:12px;font-variant-numeric:tabular-nums;">
                      {otp_code}
                    </p>
                    <p style="margin:12px 0 0;font-size:12px;color:#DC2626;font-weight:600;">
                      ⏱ Expire dans 10 minutes
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Warning -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="background:#FEF3C7;border-left:4px solid #F59E0B;
                               padding:14px 16px;border-radius:0 8px 8px 0;text-align:left;">
                    <p style="margin:0;font-size:12px;color:#92400E;line-height:1.6;">
                      ⚠️ <strong>Ne partagez jamais ce code.</strong> {bank_name} ne vous
                      demandera jamais ce code par téléphone ou par e-mail.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- DIVIDER -->
          <tr>
            <td style="padding:0 40px;">
              <div style="height:1px;background:#eeeeee;"></div>
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="padding:22px 40px;text-align:center;background:#fafafa;">
              <p style="margin:0 0 5px;font-size:12px;color:#aaaaaa;">
                Message automatique — ne pas répondre.
              </p>
              <p style="margin:0;font-size:12px;font-weight:700;color:{primary};">
                &copy; {year} {bank_name} &mdash; Tous droits réservés
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    plain = f'Code de vérification {bank_name}: {otp_code} (valable 10 min)'

    msg = EmailMultiAlternatives(
        subject=f'{bank_name} — Votre code de vérification',
        body=plain,
        from_email=f'{bank_name} <{settings.EMAIL_HOST_USER}>',
        to=[user.email],
    )
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=False)


# ─────────────────────────────────────────────
#  EMAIL 6 — Bienvenue
# ─────────────────────────────────────────────

def send_welcome_email(user, bank, temp_password):
    """Email de bienvenue avec lien de connexion."""
    domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
    login_url = f'https://{domain}/login/{bank.slug}/'
    primary = bank.primary_color
    bank_secondary = getattr(bank, 'secondary_color', primary)

    rows = (
        _row("Nom d'utilisateur", f'<strong>{user.username}</strong>',           False) +
        _row('Mot de passe',      f'<code style="font-size:14px;">{temp_password}</code>', True) +
        _row('Banque',            bank.name,                                     False) +
        _row('Titulaire',         user.get_full_name() or user.username,         True)
    )

    cta_block = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:28px;">
      <tr>
        <td align="center">
          <a href="{login_url}"
             style="display:inline-block;background:linear-gradient(135deg,{primary} 0%,{bank_secondary} 100%);
                    color:#ffffff;padding:16px 40px;border-radius:10px;text-decoration:none;
                    font-weight:700;font-size:15px;letter-spacing:0.3px;
                    box-shadow:0 4px 12px rgba(0,0,0,0.15);">
            Se connecter à {bank.name}
          </a>
        </td>
      </tr>
      <tr>
        <td style="padding-top:16px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="background:#EFF6FF;border-left:4px solid #3B82F6;
                           padding:14px 16px;border-radius:0 8px 8px 0;">
                <p style="margin:0;font-size:12px;color:#1E40AF;line-height:1.6;">
                  ℹ️ Conservez ce lien de connexion :<br/>
                  <strong>{login_url}</strong>
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding-top:14px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="background:#FEF3C7;border-left:4px solid #F59E0B;
                           padding:14px 16px;border-radius:0 8px 8px 0;">
                <p style="margin:0;font-size:12px;color:#92400E;line-height:1.6;">
                  ⚠️ <strong>Changez votre mot de passe</strong> dès votre première connexion.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>"""

    html = _build_email_html(
        bank=bank,
        status_color='#16A34A',
        status_label='Bienvenue sur votre espace client',
        status_icon='🎉',
        greeting_name=user.get_full_name() or user.username,
        intro_text=(
            f'Votre compte <strong>{bank.name}</strong> a été créé avec succès. '
            f'Retrouvez ci-dessous vos identifiants de connexion. '
            f'Nous vous recommandons de modifier votre mot de passe à la première connexion.'
        ),
        amount_display='',
        primary_color=primary,
        rows_html=rows,
        extra_block=cta_block,
    )

    plain = (
        f'Bienvenue sur {bank.name}!\n\n'
        f'Nom d\'utilisateur: {user.username}\n'
        f'Mot de passe: {temp_password}\n\n'
        f'Connectez-vous: {login_url}'
    )

    msg = EmailMultiAlternatives(
        subject=f'{bank.name} — Bienvenue sur votre espace client',
        body=plain,
        from_email=f'{bank.name} <{settings.EMAIL_HOST_USER}>',
        to=[user.email],
    )
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=True)
