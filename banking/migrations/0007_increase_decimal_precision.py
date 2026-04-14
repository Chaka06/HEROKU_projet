from django.db import migrations, models
import decimal


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0006_alter_beneficiary_email'),
    ]

    operations = [
        # BankAccount.balance
        migrations.AlterField(
            model_name='bankaccount',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=decimal.Decimal('0.00'), max_digits=15),
        ),
        # BankAccount.unblock_fee
        migrations.AlterField(
            model_name='bankaccount',
            name='unblock_fee',
            field=models.DecimalField(decimal_places=2, default=decimal.Decimal('0.00'), help_text='Frais de déblocage en €', max_digits=15),
        ),
        # BankAccount.overdraft_limit
        migrations.AlterField(
            model_name='bankaccount',
            name='overdraft_limit',
            field=models.DecimalField(decimal_places=2, default=decimal.Decimal('0.00'), max_digits=15),
        ),
        # Transaction.amount
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=15),
        ),
        # Transaction.balance_after
        migrations.AlterField(
            model_name='transaction',
            name='balance_after',
            field=models.DecimalField(decimal_places=2, max_digits=15),
        ),
        # Transaction.rejection_fee
        migrations.AlterField(
            model_name='transaction',
            name='rejection_fee',
            field=models.DecimalField(decimal_places=2, default=decimal.Decimal('0.00'), help_text='Frais de rejet en devise du compte', max_digits=15),
        ),
    ]
