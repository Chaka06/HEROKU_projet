from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime
from .utils import get_currency_symbol
import os


def format_date_fr(date):
    """Formate une date en français"""
    return date.strftime("%d/%m/%Y")


def get_bank_logo_image(bank):
    """Retourne une image du logo de la banque"""
    if bank.logo:
        try:
            from django.conf import settings
            logo_path = os.path.join(settings.MEDIA_ROOT, str(bank.logo))
            if os.path.exists(logo_path):
                return Image(logo_path, width=70, height=32)
        except:
            pass
    return None


def generate_transaction_receipt_pdf(transaction):
    """Génère un bordereau bancaire professionnel - Style réel des banques"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=25, bottomMargin=25, leftMargin=35, rightMargin=35)
    
    elements = []
    bank = transaction.account.bank
    user = transaction.account.user
    currency = get_currency_symbol(transaction.account.currency)
    
    # === HEADER: Logo + Info banque (style professionnel) ===
    logo = get_bank_logo_image(bank)
    
    header_left = ParagraphStyle('HeaderLeft', fontSize=10, textColor=colors.HexColor('#1a1a1a'), leading=12)
    header_right = ParagraphStyle('HeaderRight', fontSize=8, textColor=colors.HexColor('#666'), alignment=TA_RIGHT, leading=10)
    
    if logo:
        logo_cell = logo
    else:
        logo_style = ParagraphStyle('Logo', fontSize=14, fontName='Helvetica-Bold', textColor=colors.HexColor(bank.primary_color))
        logo_cell = Paragraph(bank.name, logo_style)
    
    bank_info_text = f"""
    {bank.headquarters}<br/>
    {bank.country}<br/>
    BIC: {transaction.account.bic}
    """
    
    doc_info_text = f"""
    Document N° T{str(transaction.id).zfill(6)}<br/>
    Édité le {format_date_fr(datetime.now())}<br/>
    Page 1/1
    """
    
    header_table = Table([
        [logo_cell, Paragraph(bank_info_text, header_left), Paragraph(doc_info_text, header_right)]
    ], colWidths=[100, 240, 185])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    # === TITRE DOCUMENT ===
    if transaction.status == 'REJECTED':
        doc_title = "AVIS DE REJET D'OPÉRATION"
        title_color = '#c62828'
    elif transaction.status == 'COMPLETED':
        doc_title = "BORDEREAU D'OPÉRATION BANCAIRE"
        title_color = '#1a1a1a'
    else:
        doc_title = "AVIS D'OPÉRATION EN COURS"
        title_color = '#f57c00'
    
    title = ParagraphStyle('DocTitle', fontSize=16, fontName='Helvetica-Bold', textColor=colors.HexColor(title_color), alignment=TA_CENTER, leading=20)
    elements.append(Paragraph(doc_title, title))
    elements.append(Spacer(1, 12))
    
    # === SECTION CLIENT ===
    section_style = ParagraphStyle('Section', fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#fff'), leading=12)
    content_style = ParagraphStyle('Content', fontSize=9, textColor=colors.HexColor('#1a1a1a'), leading=14)
    
    client_header = Table([[Paragraph("DONNEUR D'ORDRE", section_style)]], colWidths=[525])
    client_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bank.primary_color)),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(client_header)
    
    client_data = [
        ["Titulaire", f"{user.get_full_name().upper()}"],
        ["Email", user.email],
        ["Compte", f"{transaction.account.get_account_type_display()} - N° {transaction.account.account_number}"],
        ["IBAN", transaction.account.iban],
    ]
    
    client_table = Table([[Paragraph(l, content_style), Paragraph(v, content_style)] for l, v in client_data], colWidths=[100, 425])
    client_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f0f0f0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 10))
    
    # === SECTION BÉNÉFICIAIRE ===
    beneficiary_header = Table([[Paragraph("BÉNÉFICIAIRE", section_style)]], colWidths=[525])
    beneficiary_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bank.primary_color)),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(beneficiary_header)
    
    benef_name = transaction.recipient if transaction.recipient else "Non spécifié"
    benef_iban = transaction.recipient_iban if transaction.recipient_iban else "Non spécifié"
    
    beneficiary_data = [
        ["Nom", benef_name.upper()],
        ["IBAN", benef_iban],
    ]
    
    beneficiary_table = Table([[Paragraph(l, content_style), Paragraph(v, content_style)] for l, v in beneficiary_data], colWidths=[100, 425])
    beneficiary_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f0f0f0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(beneficiary_table)
    elements.append(Spacer(1, 10))
    
    # === DÉTAILS TRANSACTION ===
    details_header = Table([[Paragraph("DÉTAILS DE L'OPÉRATION", section_style)]], colWidths=[525])
    details_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bank.primary_color)),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(details_header)
    
    details_data = [
        ["Montant", f"{transaction.amount} {currency}"],
        ["Type", transaction.get_transaction_type_display()],
        ["Motif", transaction.description or "Non spécifié"],
        ["Référence", transaction.reference or "-"],
        ["Date opération", f"{format_date_fr(transaction.created_at)} à {transaction.created_at.strftime('%H:%M')}"],
        ["Statut", transaction.get_status_display()],
    ]
    
    details_table = Table([[Paragraph(l, content_style), Paragraph(v, content_style)] for l, v in details_data], colWidths=[100, 425])
    details_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f0f0f0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f8f9fa')),
    ]))
    elements.append(details_table)
    
    # === SI REJETÉ: AFFICHER LE MOTIF EN ROUGE ===
    if transaction.status == 'REJECTED':
        elements.append(Spacer(1, 12))
        
        rejection_style = ParagraphStyle('Rejection', fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#c62828'), alignment=TA_CENTER, leading=20)
        rejection_text = f"Virement rejeté pour: {transaction.rejection_reason or 'Motif non spécifié'}"
        
        rejection_box = Table([[Paragraph(rejection_text, rejection_style)]], colWidths=[525])
        rejection_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffebee')),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#c62828')),
            ('PADDING', (0, 0), (-1, -1), 15),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(rejection_box)
        
        # Frais si applicable
        if transaction.rejection_fee > 0:
            elements.append(Spacer(1, 8))
            fee_style = ParagraphStyle('Fee', fontSize=9, textColor=colors.HexColor('#c62828'), alignment=TA_CENTER, leading=14)
            fee_text = f"Frais de rejet: {transaction.rejection_fee} {currency}"
            elements.append(Paragraph(fee_text, fee_style))
    
    elements.append(Spacer(1, 15))
    
    # === MENTIONS LÉGALES (petit) ===
    footer_style = ParagraphStyle('Footer', fontSize=7, textColor=colors.HexColor('#999'), alignment=TA_CENTER, leading=10)
    footer_text = f"Document édité le {format_date_fr(datetime.now())} | {bank.name} - Tous droits réservés | Ce document fait foi"
    elements.append(Paragraph(footer_text, footer_style))
    
    # Logo en bas (très petit)
    if logo:
        elements.append(Spacer(1, 8))
        small_logo = get_bank_logo_image(bank)
        if small_logo:
            small_logo.drawWidth = 60
            small_logo.drawHeight = 27
            logo_table = Table([[small_logo]], colWidths=[525])
            logo_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
            elements.append(logo_table)
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_rejection_document_pdf(transaction):
    """Document de rejet - même format"""
    return generate_transaction_receipt_pdf(transaction)


def generate_rib_pdf(account):
    """Génère un RIB en PDF - Style officiel bancaire"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, bottomMargin=30, leftMargin=40, rightMargin=40)
    
    elements = []
    bank = account.bank
    user = account.user
    
    # === HEADER ===
    logo = get_bank_logo_image(bank)
    
    if logo:
        logo_cell = logo
    else:
        logo_style = ParagraphStyle('Logo', fontSize=16, fontName='Helvetica-Bold', textColor=colors.HexColor(bank.primary_color))
        logo_cell = Paragraph(bank.name, logo_style)
    
    header_info = ParagraphStyle('HeaderInfo', fontSize=9, textColor=colors.HexColor('#666'), leading=11)
    bank_info = f"{bank.headquarters}<br/>{bank.country}<br/>BIC: {account.bic}"
    
    header = Table([[logo_cell, Paragraph(bank_info, header_info)]], colWidths=[200, 325])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor(bank.primary_color)),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 20))
    
    # === TITRE ===
    title_style = ParagraphStyle('Title', fontSize=18, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a1a1a'), alignment=TA_CENTER, leading=24)
    elements.append(Paragraph("RELEVÉ D'IDENTITÉ BANCAIRE", title_style))
    elements.append(Spacer(1, 5))
    
    subtitle_style = ParagraphStyle('Subtitle', fontSize=9, textColor=colors.HexColor('#757575'), alignment=TA_CENTER, leading=12)
    elements.append(Paragraph(f"RIB - {account.get_account_type_display()}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # === TITULAIRE ===
    section_style = ParagraphStyle('Section', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, leading=14)
    content_style = ParagraphStyle('Content', fontSize=9, textColor=colors.HexColor('#1a1a1a'), leading=14)
    
    titulaire_header = Table([[Paragraph("TITULAIRE DU COMPTE", section_style)]], colWidths=[525])
    titulaire_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bank.primary_color)),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(titulaire_header)
    
    titulaire_data = [
        ["Nom et prénom", user.get_full_name().upper()],
        ["Email", user.email],
        ["Adresse", user.profile.address if hasattr(user, 'profile') and user.profile.address else "Non renseignée"],
        ["Ville", f"{user.profile.city}, {user.profile.country}" if hasattr(user, 'profile') else "Non renseignée"],
    ]
    
    titulaire_table = Table([[Paragraph(l, content_style), Paragraph(v, content_style)] for l, v in titulaire_data], colWidths=[120, 405])
    titulaire_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f0f0f0')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(titulaire_table)
    elements.append(Spacer(1, 15))
    
    # === COORDONNÉES BANCAIRES ===
    coord_header = Table([[Paragraph("COORDONNÉES BANCAIRES", section_style)]], colWidths=[525])
    coord_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bank.primary_color)),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(coord_header)
    
    coord_data = [
        ["Banque", bank.name],
        ["Code BIC/SWIFT", account.bic],
        ["IBAN", account.iban],
        ["Numéro de compte", account.account_number],
        ["Type de compte", account.get_account_type_display()],
        ["Devise", account.currency],
    ]
    
    coord_table = Table([[Paragraph(l, content_style), Paragraph(v, content_style)] for l, v in coord_data], colWidths=[120, 405])
    coord_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f0f0f0')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#fffef7')),  # IBAN en surbrillance
    ]))
    elements.append(coord_table)
    elements.append(Spacer(1, 30))
    
    # === FOOTER ===
    footer_style = ParagraphStyle('Footer', fontSize=8, textColor=colors.HexColor('#9e9e9e'), alignment=TA_CENTER, leading=11)
    footer = f"Document officiel - Édité le {format_date_fr(datetime.now())}<br/>{bank.name} - Tous droits réservés"
    elements.append(Paragraph(footer, footer_style))
    
    # Logo en bas
    if logo:
        elements.append(Spacer(1, 10))
        small_logo = get_bank_logo_image(bank)
        if small_logo:
            small_logo.drawWidth = 60
            small_logo.drawHeight = 27
            logo_table = Table([[small_logo]], colWidths=[525])
            logo_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
            elements.append(logo_table)
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

