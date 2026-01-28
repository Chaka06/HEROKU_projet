from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime
from .utils import get_currency_symbol


def format_date_fr(date):
    """Formate une date en français"""
    months_fr = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
        5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
        9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }
    return f"{months_fr[date.month]} {date.day}, {date.year}"


def generate_rejection_document_pdf(transaction):
    """Génère un document de rejet de transaction - Version simplifiée"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=50,
        bottomMargin=50,
        leftMargin=50,
        rightMargin=50
    )
    
    elements = []
    
    # === EN-TÊTE ===
    title_style = ParagraphStyle(
        'Title',
        fontSize=28,
        textColor=colors.HexColor('#d32f2f'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    bank_style = ParagraphStyle(
        'Bank',
        fontSize=24,
        textColor=colors.HexColor(transaction.account.bank.primary_color),
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT
    )
    
    header = Table([[Paragraph("REJET", title_style), Paragraph(transaction.account.bank.name, bank_style)]], colWidths=[250, 245])
    header.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(header)
    elements.append(Spacer(1, 25))
    
    # === INFORMATIONS ===
    info_style = ParagraphStyle('Info', fontSize=10, textColor=colors.HexColor('#1a1a1a'))
    label_style = ParagraphStyle('Label', fontSize=10, textColor=colors.HexColor('#666666'))
    
    info_items = [
        ['Numéro', f'T{str(transaction.id).zfill(6)}'],
        ['Date rejet', format_date_fr(transaction.rejected_at) if transaction.rejected_at else format_date_fr(datetime.now())],
        ['Client', transaction.account.user.get_full_name()],
        ['Type', transaction.get_transaction_type_display()],
    ]
    
    info_table = Table([[Paragraph(l, label_style), Paragraph(v, info_style)] for l, v in info_items], colWidths=[120, 180])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 25))
    
    # === MONTANT ===
    currency = get_currency_symbol(transaction.account.currency)
    amount_style = ParagraphStyle('Amount', fontSize=22, textColor=colors.HexColor('#d32f2f'), fontName='Helvetica-Bold')
    elements.append(Paragraph(f"Montant rejeté: {transaction.amount} {currency}", amount_style))
    elements.append(Spacer(1, 20))
    
    # === MOTIF ===
    reason_title = ParagraphStyle('Title2', fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a1a1a'))
    elements.append(Paragraph("MOTIF DU REJET", reason_title))
    elements.append(Spacer(1, 8))
    
    reason_style = ParagraphStyle('Reason', fontSize=10, textColor=colors.HexColor('#1a1a1a'), leading=14)
    reason_box = Table([[Paragraph(transaction.rejection_reason, reason_style)]], colWidths=[495])
    reason_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffebee')),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#ef5350')),
    ]))
    elements.append(reason_box)
    elements.append(Spacer(1, 20))
    
    # === IMPACT FINANCIER ===
    financial_style = ParagraphStyle('Financial', fontSize=10, textColor=colors.HexColor('#1a1a1a'), alignment=TA_RIGHT)
    
    financial_data = [
        ['', 'Remboursement', f'+{transaction.amount} {currency}'],
    ]
    
    if transaction.rejection_fee > 0:
        financial_data.append(['', 'Frais de rejet', f'-{transaction.rejection_fee} {currency}'])
        financial_data.append(['', '', ''])
        net_amount = transaction.amount - transaction.rejection_fee
        financial_data.append(['', 'IMPACT NET', f'{net_amount} {currency}'])
    
    financial = Table(financial_data, colWidths=[170, 200, 125])
    financial.setStyle(TableStyle([
        ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (1, -1), (2, -1), 1.5, colors.HexColor('#1a1a1a')),
        ('FONTNAME', (1, -1), (2, -1), 'Helvetica-Bold'),
    ]))
    elements.append(financial)
    elements.append(Spacer(1, 40))
    
    # === FOOTER ===
    footer_style = ParagraphStyle('Footer', fontSize=8, textColor=colors.HexColor('#999999'), alignment=TA_LEFT, leading=11)
    footer = f"Document de rejet de transaction.<br/>Généré le {format_date_fr(datetime.now())} par {transaction.account.bank.name}"
    elements.append(Paragraph(footer, footer_style))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_transaction_receipt_pdf(transaction):
    """Génère un bordereau de transaction professionnel"""
    # Si la transaction est rejetée, générer le document de rejet
    if transaction.status == 'REJECTED':
        return generate_rejection_document_pdf(transaction)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=50, 
        bottomMargin=50, 
        leftMargin=50, 
        rightMargin=50
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # === EN-TÊTE ===
    title_style = ParagraphStyle(
        'Title',
        fontSize=32,
        textColor=colors.HexColor('#1a1a1a'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    bank_style = ParagraphStyle(
        'Bank',
        fontSize=28,
        textColor=colors.HexColor(transaction.account.bank.primary_color),
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT
    )
    
    header = Table(
        [[Paragraph("Bordereau", title_style), Paragraph(transaction.account.bank.name, bank_style)]],
        colWidths=[250, 245]
    )
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 25))
    
    # === INFORMATIONS TRANSACTION ===
    info_style = ParagraphStyle('Info', fontSize=10, textColor=colors.HexColor('#1a1a1a'), alignment=TA_LEFT)
    label_style = ParagraphStyle('Label', fontSize=10, textColor=colors.HexColor('#666666'), alignment=TA_LEFT)
    
    # Déterminer le statut avec icône
    status_display = transaction.get_status_display()
    if transaction.status == 'PENDING':
        status_display = '⏳ ' + status_display
    elif transaction.status == 'COMPLETED':
        status_display = '✅ ' + status_display
    elif transaction.status == 'REJECTED':
        status_display = '❌ ' + status_display
    
    info_items = [
        ['Numéro transaction', f'T{str(transaction.id).zfill(6)}'],
        ['Date émission', format_date_fr(transaction.created_at)],
        ['Heure', transaction.created_at.strftime('%H:%M:%S')],
        ['Statut', status_display],
        ['Type', transaction.get_transaction_type_display()],
    ]
    
    info_table_data = [[Paragraph(label, label_style), Paragraph(value, info_style)] for label, value in info_items]
    
    info_table = Table(info_table_data, colWidths=[150, 150])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 25))
    
    # === PARTIES (BANQUE ET CLIENT) ===
    party_title = ParagraphStyle('PartyTitle', fontSize=10, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a1a1a'))
    party_text = ParagraphStyle('PartyText', fontSize=9, textColor=colors.HexColor('#1a1a1a'), leading=12)
    
    bank_info = [
        Paragraph(transaction.account.bank.name, party_title),
        Paragraph(transaction.account.bank.headquarters, party_text),
        Paragraph(transaction.account.bank.country, party_text),
        Paragraph(f'BIC: {transaction.account.bic}', party_text),
    ]
    
    client_info = [
        Paragraph('Client', party_title),
        Paragraph(transaction.account.user.get_full_name(), party_text),
        Paragraph(transaction.account.user.email, party_text),
    ]
    
    parties = Table([[bank_info, client_info]], colWidths=[247, 248])
    parties.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(parties)
    elements.append(Spacer(1, 30))
    
    # === MONTANT PRINCIPAL ===
    currency = get_currency_symbol(transaction.account.currency)
    amount_style = ParagraphStyle(
        'Amount',
        fontSize=22,
        textColor=colors.HexColor('#1a1a1a'),
        fontName='Helvetica-Bold'
    )
    
    elements.append(Paragraph(f"{transaction.amount} {currency} - {format_date_fr(transaction.created_at)}", amount_style))
    elements.append(Spacer(1, 20))
    
    # === TABLEAU DÉTAILS ===
    header_style = ParagraphStyle('Header', fontSize=10, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a1a1a'))
    cell_style = ParagraphStyle('Cell', fontSize=10, textColor=colors.HexColor('#1a1a1a'), leading=14)
    
    # Déterminer débiteur et bénéficiaire
    if transaction.transaction_type == 'DEPOSIT' or transaction.is_positive():
        debiteur = transaction.recipient if transaction.recipient else 'Expéditeur'
        beneficiaire = transaction.account.user.get_full_name()
    else:
        debiteur = transaction.account.user.get_full_name()
        beneficiaire = transaction.recipient if transaction.recipient else 'Bénéficiaire'
    
    table_data = [
        [
            Paragraph('<b>Description</b>', header_style),
            Paragraph('<b>Débiteur</b>', header_style),
            Paragraph('<b>Bénéficiaire</b>', header_style),
            Paragraph('<b>Montant</b>', header_style)
        ],
        [
            Paragraph(transaction.description[:80], cell_style),
            Paragraph(f'{debiteur}<br/>-{transaction.amount} {currency}', cell_style),
            Paragraph(f'{beneficiaire}<br/>+{transaction.amount} {currency}', cell_style),
            Paragraph(f'{transaction.amount} {currency}', cell_style)
        ]
    ]
    
    details = Table(table_data, colWidths=[170, 120, 120, 85])
    details.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e0e0e0')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#e0e0e0')),
    ]))
    elements.append(details)
    elements.append(Spacer(1, 20))
    
    # === TOTAUX ===
    total_style = ParagraphStyle('Total', fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a1a1a'), alignment=TA_RIGHT)
    
    totals_data = [
        ['', '', 'Total', f'{transaction.amount} {currency}'],
    ]
    
    totals = Table(totals_data, colWidths=[170, 120, 120, 85])
    totals.setStyle(TableStyle([
        ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (2, 0), (3, 0), 1.5, colors.HexColor('#1a1a1a')),
    ]))
    elements.append(totals)
    elements.append(Spacer(1, 40))
    
    # === FOOTER ===
    footer_style = ParagraphStyle(
        'Footer',
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_LEFT,
        leading=11
    )
    
    footer = f"Ce document est un bordereau de transaction officiel.<br/>Généré le {format_date_fr(datetime.now())} par {transaction.account.bank.name}"
    elements.append(Paragraph(footer, footer_style))
    
    # Générer
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf
