from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Bank(models.Model):
    """Banque"""
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=100)
    headquarters = models.CharField(max_length=200)
    capital = models.CharField(max_length=100, blank=True)
    
    # Palette de couleurs complète de la banque
    primary_color = models.CharField(max_length=7, default="#e63946", help_text="Couleur principale")
    secondary_color = models.CharField(max_length=7, default="#d62828", help_text="Couleur secondaire")
    accent_color = models.CharField(max_length=7, default="#f4a261", help_text="Couleur d'accent")
    background_color = models.CharField(max_length=7, default="#f8f9fa", help_text="Couleur de fond")
    text_color = models.CharField(max_length=7, default="#ffffff", help_text="Couleur du texte sur fond primaire")
    text_dark = models.CharField(max_length=7, default="#1a1a1a", help_text="Couleur du texte principal")
    
    # Logo
    logo = models.ImageField(upload_to='bank_logos/', null=True, blank=True)
    
    # Informations supplémentaires
    website = models.URLField(blank=True)
    swift_code = models.CharField(max_length=11, blank=True)
    description = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.country})"
    
    class Meta:
        verbose_name = "Banque"
        verbose_name_plural = "Banques"
        ordering = ['name']


class UserProfile(models.Model):
    """Profil utilisateur étendu"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)
    biometric_enabled = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='fr')
    rewards_points = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profil de {self.user.get_full_name() or self.user.username}"
    
    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"


class BankAccount(models.Model):
    """Compte bancaire"""
    ACCOUNT_TYPES = [
        ('CHECKING', 'Compte Courant'),
        ('SAVINGS', 'Compte Épargne'),
    ]
    
    ACCOUNT_STATUS = [
        ('ACTIVE', 'Actif'),
        ('SUSPENDED', 'Suspendu'),
        ('CLOSED', 'Fermé'),
    ]
    
    CURRENCIES = [
        ('EUR', '€ Euro'),
        ('USD', '$ Dollar US'),
        ('GBP', '£ Livre Sterling'),
        ('CHF', 'CHF Franc Suisse'),
        ('JPY', '¥ Yen Japonais'),
        ('CNY', '¥ Yuan Chinois'),
        ('CAD', '$ Dollar Canadien'),
        ('AUD', '$ Dollar Australien'),
        ('INR', '₹ Roupie Indienne'),
        ('BRL', 'R$ Real Brésilien'),
        ('SAR', 'ر.س Riyal Saoudien'),
        ('AED', 'د.إ Dirham Émirati'),
        ('SGD', '$ Dollar Singapourien'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    bank = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name='accounts')
    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='CHECKING')
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='EUR')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    iban = models.CharField(max_length=34, unique=True)
    bic = models.CharField(max_length=11, default='MABANFRPPXXX')
    
    # Statut du compte
    status = models.CharField(max_length=20, choices=ACCOUNT_STATUS, default='ACTIVE')
    suspension_reason = models.TextField(blank=True, help_text="Motif de la suspension du compte")
    unblock_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Frais de déblocage en €")
    
    is_active = models.BooleanField(default=True)
    overdraft_limit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_account_type_display()} - {self.account_number}"
    
    def get_masked_number(self):
        """Retourne le numéro de compte masqué"""
        return f"•••• {self.account_number[-4:]}"
    
    class Meta:
        verbose_name = "Compte bancaire"
        verbose_name_plural = "Comptes bancaires"
        ordering = ['-created_at']


class Card(models.Model):
    """Carte bancaire"""
    CARD_TYPES = [
        ('DEBIT', 'Débit'),
        ('CREDIT', 'Crédit'),
    ]
    
    CARD_NETWORKS = [
        ('MASTERCARD', 'Mastercard'),
        ('VISA', 'Visa'),
    ]
    
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=16)
    card_holder_name = models.CharField(max_length=100)
    card_type = models.CharField(max_length=10, choices=CARD_TYPES, default='DEBIT')
    card_network = models.CharField(max_length=20, choices=CARD_NETWORKS, default='MASTERCARD')
    expiry_date = models.CharField(max_length=5)  # Format: MM/YY
    cvv = models.CharField(max_length=3)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_card_type_display()} - {self.get_masked_number()}"
    
    def get_masked_number(self):
        """Retourne le numéro de carte masqué"""
        first_four = self.card_number[:4]
        last_four = self.card_number[-4:]
        return f"{first_four} •••• •••• {last_four}"
    
    class Meta:
        verbose_name = "Carte bancaire"
        verbose_name_plural = "Cartes bancaires"


class Transaction(models.Model):
    """Transaction bancaire"""
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Dépôt'),
        ('WITHDRAWAL', 'Retrait'),
        ('TRANSFER', 'Virement'),
        ('PAYMENT', 'Paiement de facture'),
        ('PURCHASE', 'Achat TPV'),
        ('ONLINE_PURCHASE', 'Achat en ligne'),
    ]
    
    TRANSACTION_STATUS = [
        ('PENDING', 'En attente'),
        ('COMPLETED', 'Confirmée'),
        ('REJECTED', 'Rejetée'),
        ('FAILED', 'Échouée'),
        ('CANCELLED', 'Annulée'),
    ]
    
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=200)
    reference = models.CharField(max_length=100, blank=True)
    recipient = models.CharField(max_length=200, blank=True)
    recipient_iban = models.CharField(max_length=34, blank=True)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='PENDING')
    
    # Informations de rejet
    rejection_reason = models.TextField(blank=True, help_text="Motif du rejet de la transaction")
    rejection_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Frais de rejet en devise du compte")
    rejected_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}€ - {self.created_at.strftime('%d/%m/%Y')}"
    
    def is_positive(self):
        """Retourne True si la transaction augmente le solde"""
        return self.transaction_type in ['DEPOSIT']
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-created_at']


class Beneficiary(models.Model):
    """Bénéficiaire pour les virements"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='beneficiaries')
    name = models.CharField(max_length=100)
    iban = models.CharField(max_length=34)
    bic = models.CharField(max_length=11, blank=True)
    email = models.EmailField(blank=True)
    is_favorite = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.iban}"
    
    def get_initials(self):
        """Retourne les initiales du bénéficiaire"""
        parts = self.name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return self.name[:2].upper()
    
    class Meta:
        verbose_name = "Bénéficiaire"
        verbose_name_plural = "Bénéficiaires"
        ordering = ['-is_favorite', 'name']


class Notification(models.Model):
    """Notifications utilisateur"""
    NOTIFICATION_TYPES = [
        ('ACCOUNT_SUSPENDED', 'Compte Suspendu'),
        ('ACCOUNT_UNBLOCKED', 'Compte Débloqué'),
        ('TRANSACTION', 'Transaction'),
        ('SECURITY', 'Sécurité'),
        ('INFO', 'Information'),
        ('ALERT', 'Alerte'),
        ('ADMIN', 'Message Admin'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']


class SupportMessage(models.Model):
    """Messages du chat support"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_messages')
    sender_is_staff = models.BooleanField(default=False, help_text="True si envoyé par l'admin")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        sender = "Admin" if self.sender_is_staff else self.user.username
        return f"{sender}: {self.message[:50]}"
    
    class Meta:
        verbose_name = "Message Support"
        verbose_name_plural = "Messages Support"
        ordering = ['created_at']


class DocumentPDF(models.Model):
    """Documents PDF générés (bordereaux, RIB, etc.)"""
    DOCUMENT_TYPES = [
        ('RECEIPT', 'Bordereau de Transaction'),
        ('REJECTION', 'Document de Rejet'),
        ('RIB', 'Relevé d\'Identité Bancaire'),
        ('STATEMENT', 'Relevé de Compte'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents_pdf/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.user.username} - {self.created_at.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = "Document PDF"
        verbose_name_plural = "Documents PDF"
        ordering = ['-created_at']
