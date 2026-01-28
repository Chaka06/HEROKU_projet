from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from decimal import Decimal
import random
import string
from .models import UserProfile, BankAccount, Card, Transaction, Beneficiary, Bank


def generate_account_number():
    """Génère un numéro de compte aléatoire"""
    return ''.join(random.choices(string.digits, k=11))


def generate_iban():
    """Génère un IBAN français aléatoire"""
    random_digits = ''.join(random.choices(string.digits, k=23))
    return f'FR76{random_digits}'


def generate_card_number():
    """Génère un numéro de carte aléatoire"""
    return ''.join(random.choices(string.digits, k=16))


@receiver(post_save, sender=User)
def create_user_banking_account(sender, instance, created, **kwargs):
    """
    Signal désactivé - La création des comptes se fait via l'admin personnalisé
    """
    # Ce signal ne fait plus rien, tout est géré par l'admin
    return
    
    if created and not instance.is_superuser:
        # Créer le profil utilisateur
        profile = UserProfile.objects.create(
            user=instance,
            rewards_points=random.randint(500, 1000)
        )
        
        # Récupérer une banque par défaut (la première disponible)
        default_bank = Bank.objects.filter(is_active=True).first()
        
        # Si aucune banque n'existe, créer une banque par défaut
        if not default_bank:
            default_bank = Bank.objects.create(
                name='MaBanque',
                country='France',
                headquarters='Paris',
                primary_color='#e63946',
                secondary_color='#d62828',
                text_color='#ffffff'
            )
        
        # Créer un compte courant
        account = BankAccount.objects.create(
            user=instance,
            bank=default_bank,
            account_number=generate_account_number(),
            account_type='CHECKING',
            balance=Decimal(str(random.uniform(1000, 5000))),
            iban=generate_iban(),
            bic=default_bank.swift_code if default_bank.swift_code else 'MABANFRPPXXX',
            status='ACTIVE'
        )
        
        # Créer une carte bancaire
        Card.objects.create(
            account=account,
            card_number=generate_card_number(),
            card_holder_name=f"{instance.first_name.upper()} {instance.last_name.upper()}" if instance.first_name and instance.last_name else instance.username.upper(),
            card_type='DEBIT',
            card_network='MASTERCARD',
            expiry_date='12/28',
            cvv=str(random.randint(100, 999))
        )
        
        # Créer des transactions d'exemple
        current_balance = account.balance
        transactions_data = [
            ('DEPOSIT', 780.00, 'Virement électronique Interac gratuit'),
            ('PAYMENT', -777.36, 'Paiement de facture'),
            ('PURCHASE', -8.95, 'Achat en magasin'),
            ('PURCHASE', -26.38, 'Transaction d\'achat'),
        ]
        
        for trans_type, amount, description in transactions_data:
            current_balance += Decimal(str(amount))
            Transaction.objects.create(
                account=account,
                transaction_type=trans_type,
                amount=abs(Decimal(str(amount))),
                balance_after=current_balance,
                description=description
            )
        
        # Créer des bénéficiaires d'exemple
        beneficiaries_data = [
            ('Marie Lambert', 'FR7612345678901234567890123'),
            ('Pierre Martin', 'FR7698765432109876543210987'),
            ('Sophie Dubois', 'FR7655556666777788889999000'),
        ]
        
        for name, iban in beneficiaries_data:
            Beneficiary.objects.create(
                user=instance,
                name=name,
                iban=iban
            )
