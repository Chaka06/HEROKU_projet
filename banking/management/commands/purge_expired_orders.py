"""
Management command : purge_expired_orders
Nettoie les commandes PENDING_PAYMENT créées il y a plus de 24h
(dont le lien de checkout GeniusPay a expiré).
Usage : python manage.py purge_expired_orders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Marque comme EXPIRED les commandes agent dont le paiement est en attente depuis + de 24h.'

    def handle(self, *args, **options):
        from banking.models import AccountCreationOrder

        cutoff = timezone.now() - timedelta(hours=24)
        qs = AccountCreationOrder.objects.filter(
            order_status='PENDING_PAYMENT',
            payment_status='PENDING',
            created_at__lt=cutoff,
        )
        count = qs.count()
        qs.update(
            order_status='FAILED',
            payment_status='EXPIRED',
        )
        self.stdout.write(
            self.style.SUCCESS(f'{count} commande(s) expirée(s) nettoyée(s).')
        )
