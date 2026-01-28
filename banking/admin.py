from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.db import transaction as db_transaction
from decimal import Decimal
import random
from .models import Bank, UserProfile, BankAccount, Card, Transaction, Beneficiary, Notification, SupportMessage, DocumentPDF
from .utils import generate_account_number, generate_iban, generate_card_number, get_currency_for_country, get_currency_symbol


# Formulaire SIMPLIFIÉ pour créer un utilisateur
class CustomUserCreationForm(UserCreationForm):
    # Informations de base
    first_name = forms.CharField(max_length=150, required=True, label="Prénom")
    last_name = forms.CharField(max_length=150, required=True, label="Nom")
    email = forms.EmailField(required=True, label="Email")
    
    # Localisation
    country = forms.CharField(
        max_length=100, 
        required=True, 
        label="Pays",
        help_text="Le code IBAN sera généré selon le pays"
    )
    city = forms.CharField(max_length=100, required=True, label="Ville")
    
    # Banque
    bank = forms.ModelChoiceField(
        queryset=Bank.objects.filter(is_active=True).order_by('name'),
        required=True,
        label="Banque",
        help_text="⚠️ Les couleurs de l'interface et le BIC seront ceux de cette banque"
    )
    
    # Type de compte
    create_checking = forms.BooleanField(
        required=False,
        initial=True,
        label="☑ Compte Courant"
    )
    initial_balance_checking = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        initial=Decimal('1000.00'),
        required=False,
        label="Solde initial"
    )
    
    create_savings = forms.BooleanField(
        required=False,
        initial=False,
        label="☑ Compte Épargne"
    )
    initial_balance_savings = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        initial=Decimal('5000.00'),
        required=False,
        label="Solde initial"
    )
    
    # Statut
    account_status = forms.ChoiceField(
        choices=BankAccount.ACCOUNT_STATUS,
        initial='ACTIVE',
        label="Statut du compte",
        widget=forms.RadioSelect
    )
    
    suspension_reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label="Motif de suspension (si suspendu)"
    )
    
    unblock_fee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=Decimal('0.00'),
        required=False,
        label="Frais de déblocage (€)"
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


# Inline pour MODIFICATION uniquement
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'
    fields = ['phone', 'address', 'city', 'country', 'date_of_birth']


class BankAccountInline(admin.TabularInline):
    model = BankAccount
    extra = 1
    fields = ['bank', 'account_type', 'currency', 'balance', 'status', 'suspension_reason', 'unblock_fee']
    
    def save_model(self, request, obj, form, change):
        # Générer automatiquement les infos bancaires si nouveau compte
        if not obj.pk:
            from .utils import generate_account_number, generate_iban, get_currency_for_country
            obj.account_number = generate_account_number()
            obj.iban = generate_iban(obj.user.profile.country if hasattr(obj.user, 'profile') else 'France')
            obj.bic = obj.bank.swift_code if obj.bank.swift_code else 'BANKXXXXXX'
            
            # Créer une carte pour ce nouveau compte
            Card.objects.create(
                account=obj,
                card_number=generate_card_number(),
                card_holder_name=f"{obj.user.first_name.upper()} {obj.user.last_name.upper()}",
                card_type='DEBIT',
                card_network='MASTERCARD',
                expiry_date='12/28',
                cvv=str(random.randint(100, 999))
            )
        
        super().save_model(request, obj, form, change)


class BeneficiaryInline(admin.TabularInline):
    model = Beneficiary
    extra = 1
    fields = ['name', 'iban', 'bic', 'email', 'is_favorite']


# Admin User personnalisé
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    
    # Inlines seulement pour la modification
    def get_inlines(self, request, obj):
        if obj:  # Si on modifie un utilisateur existant
            return [UserProfileInline, BankAccountInline, BeneficiaryInline]
        return []  # Pas d'inline à la création
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_bank', 'get_balance', 'get_status']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_bank(self, obj):
        if not obj.is_superuser and obj.bank_accounts.exists():
            account = obj.bank_accounts.first()
            return f"{account.bank.name}"
        return "—"
    get_bank.short_description = 'Banque'
    
    def get_balance(self, obj):
        if not obj.is_superuser and obj.bank_accounts.exists():
            accounts = obj.bank_accounts.all()
            total = sum(acc.balance for acc in accounts)
            currency = accounts.first().currency if accounts else 'EUR'
            symbol = get_currency_symbol(currency)
            return f"{total} {symbol}"
        return "—"
    get_balance.short_description = 'Solde Total'
    
    def get_status(self, obj):
        if not obj.is_superuser and obj.bank_accounts.exists():
            statuses = set(acc.status for acc in obj.bank_accounts.all())
            if 'SUSPENDED' in statuses:
                return '⚠️ Suspendu'
            elif 'ACTIVE' in statuses:
                return '✅ Actif'
            else:
                return '❌ Fermé'
        return "—"
    get_status.short_description = 'Statut'
    
    # Fieldsets pour MODIFICATION
    fieldsets = (
        ('Identifiants', {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'classes': ('collapse',),
        }),
    )
    
    # Fieldsets pour CRÉATION (simplifié!)
    add_fieldsets = (
        ('🔐 Identifiants', {
            'fields': ('username', 'password1', 'password2'),
        }),
        ('👤 Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email'),
        }),
        ('📍 Localisation', {
            'fields': ('country', 'city'),
        }),
        ('🏦 Banque', {
            'fields': ('bank',),
        }),
        ('💳 Comptes à créer', {
            'fields': (
                ('create_checking', 'initial_balance_checking'),
                ('create_savings', 'initial_balance_savings')
            ),
            'description': '✓ IBAN généré selon le pays | ✓ BIC selon la banque | ✓ Carte créée | ✓ Devise selon le pays'
        }),
        ('⚠️ Statut', {
            'fields': ('account_status', 'suspension_reason', 'unblock_fee'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # CRÉATION
            with db_transaction.atomic():
                # Sauvegarder l'utilisateur
                obj.save()
                
                # Récupérer les données du formulaire
                country = form.cleaned_data.get('country')
                city = form.cleaned_data.get('city')
                bank = form.cleaned_data.get('bank')
                status = form.cleaned_data.get('account_status', 'ACTIVE')
                suspension_reason = form.cleaned_data.get('suspension_reason', '')
                unblock_fee = form.cleaned_data.get('unblock_fee', Decimal('0.00'))
                
                # Créer le profil
                UserProfile.objects.create(
                    user=obj,
                    country=country,
                    city=city,
                    rewards_points=random.randint(500, 1000)
                )
                
                # Déterminer la devise selon le pays
                currency = get_currency_for_country(country)
                
                # Créer les comptes demandés
                accounts_created = []
                
                if form.cleaned_data.get('create_checking'):
                    account = BankAccount.objects.create(
                        user=obj,
                        bank=bank,
                        account_number=generate_account_number(),
                        account_type='CHECKING',
                        currency=currency,
                        balance=form.cleaned_data.get('initial_balance_checking', Decimal('1000.00')),
                        iban=generate_iban(country, bank.swift_code),
                        bic=bank.swift_code if bank.swift_code else 'BANKXXXXXX',
                        status=status,
                        suspension_reason=suspension_reason,
                        unblock_fee=unblock_fee
                    )
                    accounts_created.append(('Compte Courant', account))
                
                if form.cleaned_data.get('create_savings'):
                    account = BankAccount.objects.create(
                        user=obj,
                        bank=bank,
                        account_number=generate_account_number(),
                        account_type='SAVINGS',
                        currency=currency,
                        balance=form.cleaned_data.get('initial_balance_savings', Decimal('5000.00')),
                        iban=generate_iban(country, bank.swift_code),
                        bic=bank.swift_code if bank.swift_code else 'BANKXXXXXX',
                        status=status,
                        suspension_reason=suspension_reason,
                        unblock_fee=unblock_fee
                    )
                    accounts_created.append(('Compte Épargne', account))
                
                # Créer une carte pour chaque compte
                for account_name, account in accounts_created:
                    Card.objects.create(
                        account=account,
                        card_number=generate_card_number(),
                        card_holder_name=f"{obj.first_name.upper()} {obj.last_name.upper()}",
                        card_type='DEBIT',
                        card_network='MASTERCARD',
                        expiry_date='12/28',
                        cvv=str(random.randint(100, 999))
                    )
                    
                    # Créer des transactions uniquement si le compte est actif
                    if status == 'ACTIVE':
                        current_balance = account.balance
                        transactions_data = [
                            ('DEPOSIT', 780.00, 'Virement électronique'),
                            ('PAYMENT', -50.00, 'Paiement de facture'),
                            ('PURCHASE', -25.50, 'Achat en magasin'),
                            ('PURCHASE', -15.00, 'Transaction d\'achat'),
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
                
                # Créer 3 bénéficiaires
                for i in range(3):
                    Beneficiary.objects.create(
                        user=obj,
                        name=f"Bénéficiaire {i+1}",
                        iban=generate_iban(country)
                    )
                
                # Message de succès
                from django.contrib import messages
                account_info = ' | '.join([f"{name}: {acc.balance} {get_currency_symbol(acc.currency)}" for name, acc in accounts_created])
                messages.success(request,
                    f"✅ Utilisateur {obj.username} créé avec succès! | "
                    f"Banque: {bank.name} | Comptes: {account_info} | "
                    f"IBAN: {accounts_created[0][1].iban if accounts_created else 'N/A'}"
                )
        else:
            super().save_model(request, obj, form, change)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)


# Admin pour les Banques
@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'headquarters', 'get_color_preview', 'is_active']
    list_filter = ['country', 'is_active']
    search_fields = ['name', 'country']
    
    def get_color_preview(self, obj):
        return f'🎨 {obj.primary_color}'
    get_color_preview.short_description = 'Couleur'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'country', 'headquarters', 'capital', 'website', 'swift_code', 'description')
        }),
        ('Identité visuelle', {
            'fields': ('primary_color', 'secondary_color', 'text_color', 'logo'),
            'description': 'Format hexadécimal: #RRGGBB'
        }),
        ('Statut', {
            'fields': ('is_active',),
        }),
    )


# Admin pour gérer les virements/transactions
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['get_user', 'get_bank', 'account', 'transaction_type', 'amount', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at', 'account__bank']
    search_fields = ['description', 'account__user__username', 'account__user__first_name', 'account__user__last_name']
    date_hierarchy = 'created_at'
    
    def get_user(self, obj):
        return f"{obj.account.user.get_full_name()} (@{obj.account.user.username})"
    get_user.short_description = 'Client'
    
    def get_bank(self, obj):
        return obj.account.bank.name
    get_bank.short_description = 'Banque'
    
    def get_pdf_button(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<a class="button" href="/admin/banking/transaction/{}/download-pdf/" style="background: #e63946; color: white; padding: 5px 12px; text-decoration: none; border-radius: 4px;">📄 PDF</a>',
            obj.id
        )
    get_pdf_button.short_description = 'Document'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:transaction_id>/download-pdf/', self.admin_site.admin_view(self.download_pdf_view), name='transaction_download_pdf'),
        ]
        return custom_urls + urls
    
    def download_pdf_view(self, request, transaction_id):
        from django.http import HttpResponse
        from .pdf_generator import generate_transaction_receipt_pdf
        
        transaction = Transaction.objects.get(id=transaction_id)
        pdf_content = generate_transaction_receipt_pdf(transaction)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="bordereau_T{str(transaction.id).zfill(6)}.pdf"'
        
        return response
    
    fieldsets = (
        ('Compte à débiter/créditer', {
            'fields': ('account',),
            'description': 'Sélectionnez le compte du client'
        }),
        ('Type de transaction', {
            'fields': ('transaction_type', 'status'),
            'description': 'DEPOSIT = Crédit (+) | Autres = Débit (-) | Statut par défaut: EN ATTENTE'
        }),
        ('Montant', {
            'fields': ('amount',),
            'description': '⚠️ Le solde sera calculé automatiquement'
        }),
        ('Détails', {
            'fields': ('description', 'reference', 'recipient', 'recipient_iban'),
            'classes': ('collapse',),
        }),
        ('Validation', {
            'fields': ('confirmed_at', 'rejected_at', 'rejection_reason', 'rejection_fee'),
            'classes': ('collapse',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            account = obj.account
            
            # Calculer le nouveau solde
            if obj.transaction_type == 'DEPOSIT':
                account.balance += obj.amount
            else:
                account.balance -= obj.amount
            
            obj.balance_after = account.balance
            obj.save()
            account.save()
            
            from django.contrib import messages
            sign = '+' if obj.transaction_type == 'DEPOSIT' else '-'
            symbol = get_currency_symbol(account.currency)
            messages.success(request,
                f"✅ Transaction enregistrée: {sign}{obj.amount} {symbol} | "
                f"Nouveau solde: {account.balance} {symbol} | "
                f"Statut: EN ATTENTE (le client doit confirmer)"
            )
        else:
            super().save_model(request, obj, form, change)


# Admin pour les Documents PDF
@admin.register(DocumentPDF)
class DocumentPDFAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_user', 'document_type', 'get_transaction', 'created_at', 'get_download_button']
    list_filter = ['document_type', 'created_at']
    search_fields = ['title', 'user__username', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'
    
    def get_user(self, obj):
        return f"{obj.user.get_full_name()} (@{obj.user.username})"
    get_user.short_description = 'Client'
    
    def get_transaction(self, obj):
        if obj.transaction:
            return f"T{str(obj.transaction.id).zfill(6)}"
        return '-'
    get_transaction.short_description = 'Transaction'
    
    def get_download_button(self, obj):
        from django.utils.html import format_html
        if obj.file:
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background: #117ACA; color: white; padding: 5px 12px; text-decoration: none; border-radius: 4px;">📥 Télécharger</a>',
                obj.file.url
            )
        return '-'
    get_download_button.short_description = 'Fichier'
    
    fieldsets = (
        ('Document', {
            'fields': ('user', 'document_type', 'title'),
        }),
        ('Transaction associée', {
            'fields': ('transaction',),
        }),
        ('Fichier', {
            'fields': ('file',),
        }),
    )


# Admin pour les bénéficiaires
@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_user', 'iban', 'is_favorite', 'created_at']
    list_filter = ['is_favorite', 'created_at']
    search_fields = ['name', 'iban', 'user__username', 'user__first_name', 'user__last_name']
    
    def get_user(self, obj):
        return f"{obj.user.get_full_name()} (@{obj.user.username})"
    get_user.short_description = 'Client'
    
    fieldsets = (
        ('Client', {
            'fields': ('user',),
        }),
        ('Informations du bénéficiaire', {
            'fields': ('name', 'iban', 'bic', 'email'),
        }),
        ('Options', {
            'fields': ('is_favorite',),
        }),
    )


# Admin pour les RIB (Comptes Bancaires)
@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['get_user', 'bank', 'account_type', 'account_number', 'iban', 'currency', 'balance', 'status']
    list_filter = ['bank', 'account_type', 'currency', 'status']
    search_fields = ['account_number', 'iban', 'user__username', 'user__first_name', 'user__last_name']
    
    def get_user(self, obj):
        return f"{obj.user.get_full_name()} (@{obj.user.username})"
    get_user.short_description = 'Client'
    
    fieldsets = (
        ('Client', {
            'fields': ('user',),
        }),
        ('Banque', {
            'fields': ('bank',),
        }),
        ('Informations du compte', {
            'fields': ('account_type', 'currency', 'account_number', 'iban', 'bic'),
        }),
        ('Solde', {
            'fields': ('balance', 'overdraft_limit'),
        }),
        ('Statut', {
            'fields': ('status', 'suspension_reason', 'unblock_fee', 'is_active'),
        }),
    )
    
    readonly_fields = []
    
    def save_model(self, request, obj, form, change):
        if change:  # Si c'est une modification
            old_obj = BankAccount.objects.get(pk=obj.pk)
            
            # Vérifier si le statut a changé
            if old_obj.status != obj.status:
                if obj.status == 'SUSPENDED':
                    # Créer une notification de suspension
                    Notification.objects.create(
                        user=obj.user,
                        notification_type='ACCOUNT_SUSPENDED',
                        title='Compte Suspendu',
                        message=f'Votre {obj.get_account_type_display()} a été suspendu. Motif: {obj.suspension_reason}'
                    )
                elif obj.status == 'ACTIVE' and old_obj.status == 'SUSPENDED':
                    # Créer une notification de déblocage
                    Notification.objects.create(
                        user=obj.user,
                        notification_type='ACCOUNT_UNBLOCKED',
                        title='Compte Débloqué',
                        message=f'Votre {obj.get_account_type_display()} a été débloqué. Vous pouvez à nouveau effectuer des opérations.'
                    )
        
        super().save_model(request, obj, form, change)


# Admin pour les Notifications
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'
    
    def get_user(self, obj):
        return f"{obj.user.get_full_name()} (@{obj.user.username})"
    get_user.short_description = 'Client'
    
    fieldsets = (
        ('Destinataire', {
            'fields': ('user',),
        }),
        ('Notification', {
            'fields': ('notification_type', 'title', 'message'),
        }),
        ('Statut', {
            'fields': ('is_read',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            from django.contrib import messages as django_messages
            django_messages.success(request, f"✅ Notification envoyée à {obj.user.username}")


# Admin pour le Support/Chat
@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['get_user', 'get_sender', 'get_message_preview', 'is_read', 'created_at', 'get_reply_button']
    list_filter = ['sender_is_staff', 'is_read', 'created_at']
    search_fields = ['message', 'user__username', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'
    change_list_template = 'admin/support_changelist.html'
    
    def get_user(self, obj):
        return f"{obj.user.get_full_name()} (@{obj.user.username})"
    get_user.short_description = 'Client'
    
    def get_sender(self, obj):
        return '👨‍💼 Support' if obj.sender_is_staff else '👤 Client'
    get_sender.short_description = 'Expéditeur'
    
    def get_message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    get_message_preview.short_description = 'Message'
    
    def get_reply_button(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<a class="button" href="{}" style="background: #117ACA; color: white; padding: 5px 12px; text-decoration: none; border-radius: 4px;">💬 Répondre</a>',
            f'/admin/banking/supportmessage/chat/{obj.user.id}/'
        )
    get_reply_button.short_description = 'Action'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('chat/<int:user_id>/', self.admin_site.admin_view(self.support_chat_view), name='banking_supportmessage_chat'),
        ]
        return custom_urls + urls
    
    def support_chat_view(self, request, user_id):
        from django.shortcuts import render, redirect
        from django.contrib.auth.models import User
        from django.contrib import messages as django_messages
        
        user_obj = User.objects.get(id=user_id)
        
        if request.method == 'POST':
            message_text = request.POST.get('message')
            if message_text:
                SupportMessage.objects.create(
                    user=user_obj,
                    sender_is_staff=True,
                    message=message_text
                )
                django_messages.success(request, f"✅ Réponse envoyée à {user_obj.username}")
                return redirect(f'/admin/banking/supportmessage/chat/{user_id}/')
        
        messages_list = SupportMessage.objects.filter(user=user_obj).order_by('created_at')
        
        context = {
            **self.admin_site.each_context(request),
            'user_obj': user_obj,
            'messages_list': messages_list,
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/support_chat.html', context)
    
    fieldsets = (
        ('Conversation', {
            'fields': ('user',),
        }),
        ('Message', {
            'fields': ('message', 'sender_is_staff'),
            'description': 'Cochez "Sender is staff" pour envoyer en tant que Support'
        }),
        ('Statut', {
            'fields': ('is_read',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and obj.sender_is_staff:
            from django.contrib import messages as django_messages
            django_messages.success(request, f"✅ Réponse envoyée à {obj.user.username}")


# Personnaliser les titres
admin.site.site_header = "Administration MaBanque"
admin.site.site_title = "MaBanque Admin"
admin.site.index_title = "Gestion Multi-Banques"
