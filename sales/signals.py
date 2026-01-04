from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Invoice, SalesRepresentative, SalesRepTransaction, OldGoldReturn
from finance.models import JournalEntry, LedgerEntry, FinanceSettings, Account
from crm.models import CustomerTransaction
from django.db import transaction
from decimal import Decimal

@receiver(post_save, sender=Invoice)
def create_invoice_journal_entry(sender, instance, created, **kwargs):
    """
    Automatically creates a Journal Entry when an Invoice is saved.
    Debit: Cash/Bank (Net Amount)
    Debit: Old Gold Inventory (Exchange Value)
    Credit: Sales Revenue (Gold + Labor)
    Credit: VAT Payable
    """
    # Only process confirmed invoices
    if instance.status != 'confirmed':
        return
        
    # Wait for totals to be calculated (Prevent early signal on create)
    if instance.grand_total <= 0:
        return

    # Prevent double entry (Check if reference exists)
    if JournalEntry.objects.filter(reference=instance.invoice_number).exists():
        return

    # Get Default Accounts from Settings
    settings = FinanceSettings.objects.first()
    if not settings:
        return

    # Determine Debit Account (Payment Method)
    cash_account = None
    if instance.payment_method == 'cash':
        cash_account = settings.cash_account
    elif instance.payment_method == 'card':
        cash_account = settings.bank_account # Fixed: use bank account for cards
    else:
         cash_account = settings.cash_account

    if not cash_account or not settings.sales_revenue_account or not settings.vat_account:
        return

    with transaction.atomic():
        # 1. Create Journal Header
        journal = JournalEntry.objects.create(
            reference=instance.invoice_number,
            description=f"قيد مبيعات تلقائي - فاتورة {instance.invoice_number}",
            date=instance.created_at.date()
        )
        
        # Calculate Splits
        exchange_value = instance.exchange_value_deducted if instance.is_exchange else Decimal('0')
        net_cash = instance.grand_total - exchange_value

        # 2. Debit: Cash/Bank (Net Amount to Collect)
        if net_cash > 0:
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=cash_account,
                debit=net_cash,
                credit=0,
                gold_debit=0,
                gold_credit=0
            )

        # 3. Debit: Old Gold Inventory (Exchange Value)
        if exchange_value > 0:
            # Try to get a specific account for Old Gold, or fallback to Inventory
            old_gold_account = getattr(settings, 'old_gold_account', settings.inventory_gold_account) 
            # If no inventory account in settings, we can't record this leg correctly, 
            # but we will default to cash_account to balance the books temporarily (or raise error in strict mode)
            target_acc = old_gold_account if old_gold_account else cash_account
            
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=target_acc,
                debit=exchange_value,
                credit=0,
                gold_debit=instance.exchange_gold_weight, # Track gold weight too
                gold_credit=0
            )

        # 4. Credit: VAT
        if instance.total_tax > 0:
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=settings.vat_account,
                debit=0,
                credit=instance.total_tax,
                gold_debit=0,
                gold_credit=0
            )

        # 5. Credit: Sales Revenue (Remaining Amount excluding Tax)
        # Revenue is typically Net of Tax. 
        # Grand Total = Revenue + Tax.
        # So Revenue = Grand Total - Tax.
        revenue_amount = instance.grand_total - instance.total_tax
        
        LedgerEntry.objects.create(
            journal_entry=journal,
            account=settings.sales_revenue_account,
            debit=0,
            credit=revenue_amount,
            gold_debit=0,
            gold_credit=0
        )

        # 6. Debit: COGS & Credit: Inventory
        if settings.cost_of_gold_account and settings.inventory_gold_account:
            total_cogs = sum(item.total_cost for item in instance.items.all())
            total_weight = sum(item.sold_weight for item in instance.items.all())

            if total_cogs > 0:
                # Debit: COGS
                LedgerEntry.objects.create(
                    journal_entry=journal,
                    account=settings.cost_of_gold_account,
                    debit=total_cogs,
                    credit=0,
                    gold_debit=0,
                    gold_credit=0
                )
                
                # Credit: Inventory
                LedgerEntry.objects.create(
                    journal_entry=journal,
                    account=settings.inventory_gold_account,
                    debit=0,
                    credit=total_cogs,
                    gold_debit=0,
                    gold_credit=total_weight
                )


@receiver(post_save, sender=Invoice)
def calculate_sales_rep_commission(sender, instance, created, **kwargs):
    """
    Automatically calculate and record commission for the sales representative
    when an invoice is created.
    """
    # Only process confirmed invoices
    if instance.status != 'confirmed':
        return
    
    if not instance.sales_rep:
        return  # No sales rep assigned
    
    sales_rep = instance.sales_rep
    
    # Check if commission already recorded for this invoice
    if SalesRepTransaction.objects.filter(sales_rep=sales_rep, invoice=instance).exists():
        return
    
    # Calculate commission
    commission_amount = sales_rep.calculate_commission(instance.grand_total)
    
    if commission_amount <= 0:
        return
    
    with transaction.atomic():
        # 1. Create commission transaction
        SalesRepTransaction.objects.create(
            sales_rep=sales_rep,
            invoice=instance,
            transaction_type='commission',
            amount=commission_amount,
            notes=f"عمولة فاتورة رقم {instance.invoice_number} - قيمة الفاتورة: {instance.grand_total}"
        )

        # 2. Update sales rep totals
        sales_rep.total_sales = (sales_rep.total_sales or Decimal('0')) + instance.grand_total
        sales_rep.total_commission = (sales_rep.total_commission or Decimal('0')) + commission_amount
        sales_rep.save(update_fields=['total_sales', 'total_commission'])

        # 3. FINANCIAL IMPACT: Record Accrued Commission in General Ledger
        # Debit: Commission Expense (5303)
        # Credit: Accrued Liabilities / Commissions Payable (2102)
        try:
            expense_acc = Account.objects.get(code='5303')
            payable_acc = Account.objects.get(code='2102')
            
            journal = JournalEntry.objects.create(
                reference=f"COMM-{instance.invoice_number}",
                description=f"استحقاق عمولة مندوب - {sales_rep.name} - فاتورة {instance.invoice_number}",
                date=instance.created_at.date()
            )
            
            # Debit: Expense
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=expense_acc,
                debit=commission_amount,
                credit=0
            )
            
            # Credit: Payable
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=payable_acc,
                debit=0,
                credit=commission_amount
            )
        except Account.DoesNotExist:
            pass # Should log this in production


@receiver(post_save, sender=Invoice)
def record_customer_ledger_on_confirmation(sender, instance, created, **kwargs):
    """
    Automatically record the invoice and any gold barter/exchange in the customer ledger.
    """
    if instance.status != 'confirmed' or not instance.customer:
        return

    # Prevent duplicate ledger entries for the same invoice
    if CustomerTransaction.objects.filter(invoice=instance, transaction_type='sale').exists():
        return

    with transaction.atomic():
        # 1. Record the Sale (Full Invoice Debt)
        CustomerTransaction.objects.create(
            customer=instance.customer,
            invoice=instance,
            transaction_type='sale',
            cash_debit=instance.grand_total,
            date=instance.created_at.date(),
            description=f"فاتورة مبيعات رقم {instance.invoice_number}"
        )

        # 2. Record Gold Barter (Exchange)
        if instance.is_exchange:
            exchanges = instance.returned_gold.all()
            for exchange in exchanges:
                CustomerTransaction.objects.create(
                    customer=instance.customer,
                    invoice=instance,
                    transaction_type='barter',
                    cash_credit=exchange.value,
                    gold_credit=exchange.weight,
                    carat=exchange.carat,
                    date=instance.created_at.date(),
                    description=f"مقايضة ذهب عيار {exchange.carat.name} - فاتورة {instance.invoice_number}"
                )

        # 3. Record Payment if paid immediately (Not mixed or debt)
        # Note: If payment_method is cash/card, we assume it's paid.
        if instance.payment_method in ['cash', 'card']:
            exchange_val = instance.exchange_value_deducted if instance.is_exchange else Decimal('0')
            net_cash = instance.grand_total - exchange_val
            
            if net_cash > 0:
                CustomerTransaction.objects.create(
                    customer=instance.customer,
                    invoice=instance,
                    transaction_type='payment',
                    cash_credit=net_cash,
                    date=instance.created_at.date(),
                    description=f"سداد نقدي/بطاقة - فاتورة {instance.invoice_number}"
                )

