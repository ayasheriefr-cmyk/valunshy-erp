from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .treasury_models import (
    TreasuryTransaction, ExpenseVoucher, ReceiptVoucher, TreasuryTransfer,
    TreasuryTool, ToolTransfer, CustodyTool
)
from .models import JournalEntry, LedgerEntry, FinanceSettings, Account

@receiver(post_save, sender=TreasuryTransaction)
def create_journal_entry_for_transaction(sender, instance, created, **kwargs):
    """
    Automated Journal Entry Creation
    --------------------------------
    Triggered when a Treasury Transaction is created.
    It automatically posts Debit/Credit entries to the General Ledger.
    """
    if not created: 
        return # Only on creation for now to avoid duplications on updates

    # For Transfers, we only want ONE Journal Entry to avoid duplication in GL.
    # We choose to post it from the 'transfer_out' side.
    if instance.transaction_type == 'transfer_in':
        return

    treasury = instance.treasury
    if not treasury.linked_account:
        # If Treasury isn't linked to a GL account, we cannot post automated entries.
        # Ideally, we should log a warning here.
        return

    # Get Default Accounts from Settings
    settings = FinanceSettings.objects.first()
    if not settings:
        return

    # Define the Counter Account (The other side of the entry)
    counter_account = None
    
    if instance.transaction_type == 'cash_in' or instance.transaction_type == 'finished_goods_in':
        counter_account = settings.sales_revenue_account
    elif instance.transaction_type == 'cash_out':
        counter_account = settings.cost_of_gold_account
    elif instance.transaction_type in ['transfer_in', 'transfer_out']:
        # For transfers, we need the OTHER treasury's account
        if instance.reference_type == 'treasury_transfer':
            transfer = TreasuryTransfer.objects.filter(id=instance.reference_id).first()
            if transfer:
                if instance.transaction_type == 'transfer_in':
                    counter_account = transfer.from_treasury.linked_account
                else:
                    counter_account = transfer.to_treasury.linked_account
    
    if not counter_account:
        return 

    # Prepare Entry Data
    description = f"Auto: {instance.get_transaction_type_display()} - {instance.description}"
    
    with transaction.atomic():
        # 1. Create Journal Header
        journal = JournalEntry.objects.create(
            reference=f"TRX-{instance.id}",
            description=description,
            date=instance.date
        )

        # 2. Create Ledger Entries (Debits & Credits)
        if instance.transaction_type in ['cash_in', 'transfer_in']:
            # Debit Treasury (Increase Asset)
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=treasury.linked_account,
                cost_center=instance.cost_center,
                debit=instance.cash_amount,
                credit=0
            )
            # Credit Source (Revenue/Other)
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=counter_account,
                cost_center=instance.cost_center,
                debit=0,
                credit=instance.cash_amount
            )

        elif instance.transaction_type in ['cash_out', 'transfer_out']:
            # Debit Destination (Expense/Asset)
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=counter_account,
                cost_center=instance.cost_center,
                debit=instance.cash_amount,
                credit=0
            )
            # Credit Treasury (Decrease Asset)
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=treasury.linked_account,
                cost_center=instance.cost_center,
                debit=0,
                credit=instance.cash_amount
            )

@receiver(post_save, sender=TreasuryTransaction)
def update_treasury_balance(sender, instance, created, **kwargs):
    """
    Update Treasury current balances when a transaction is saved.
    """
    if not created:
        return

    treasury = instance.treasury
    
    with transaction.atomic():
        # 1. Update Cash Balance
        if instance.transaction_type in ['cash_in', 'transfer_in', 'adjustment', 'finished_goods_in']:
            treasury.cash_balance += instance.cash_amount
        elif instance.transaction_type in ['cash_out', 'transfer_out']:
            treasury.cash_balance -= instance.cash_amount

        # 2. Update Gold Balance
        if instance.gold_weight and instance.gold_carat:
            carat_name = instance.gold_carat.name
            if '18' in carat_name:
                if instance.transaction_type in ['gold_in', 'transfer_in', 'adjustment', 'finished_goods_in']:
                    treasury.gold_balance_18 += instance.gold_weight
                elif instance.transaction_type in ['gold_out', 'transfer_out']:
                    treasury.gold_balance_18 -= instance.gold_weight
            elif '21' in carat_name:
                if instance.transaction_type in ['gold_in', 'transfer_in', 'adjustment', 'finished_goods_in']:
                    treasury.gold_balance_21 += instance.gold_weight
                elif instance.transaction_type in ['gold_out', 'transfer_out']:
                    treasury.gold_balance_21 -= instance.gold_weight
            elif '24' in carat_name:
                if instance.transaction_type in ['gold_in', 'transfer_in', 'adjustment', 'finished_goods_in']:
                    treasury.gold_balance_24 += instance.gold_weight
                elif instance.transaction_type in ['gold_out', 'transfer_out']:
                    treasury.gold_balance_24 -= instance.gold_weight

        # 3. Update Casting Gold Balance
        if instance.gold_casting_weight:
            if instance.transaction_type in ['gold_in', 'transfer_in', 'adjustment']:
                treasury.gold_casting_balance += instance.gold_casting_weight
            elif instance.transaction_type in ['gold_out', 'transfer_out']:
                treasury.gold_casting_balance -= instance.gold_casting_weight
                
        # 4. Update Stones Balance
        if instance.stones_weight:
            if instance.transaction_type in ['gold_in', 'transfer_in', 'adjustment']:
                treasury.stones_balance += instance.stones_weight
            elif instance.transaction_type in ['gold_out', 'transfer_out']:
                treasury.stones_balance -= instance.stones_weight

        treasury.save()

        # 3. Update the transaction record with the "Balance After"
        # We use .update() to avoid triggering post_save again
        current_gold_balance = 0
        if instance.gold_carat:
            if '18' in instance.gold_carat.name: current_gold_balance = treasury.gold_balance_18
            elif '21' in instance.gold_carat.name: current_gold_balance = treasury.gold_balance_21
            elif '24' in instance.gold_carat.name: current_gold_balance = treasury.gold_balance_24

        TreasuryTransaction.objects.filter(pk=instance.pk).update(
            balance_after_cash=treasury.cash_balance,
            balance_after_gold=current_gold_balance,
            balance_after_gold_casting=treasury.gold_casting_balance,
            balance_after_stones=treasury.stones_balance
        )


@receiver(post_save, sender=ExpenseVoucher)
def process_expense_voucher_payment(sender, instance, created, **kwargs):
    """
    Automatically create a Treasury Transaction when an Expense Voucher is marked as 'paid'.
    """
    if instance.status == 'paid':
        # Check if a transaction already exists for this voucher to avoid duplicates
        existing_trx = TreasuryTransaction.objects.filter(
            reference_type='expense_voucher',
            reference_id=instance.id
        ).exists()
        
        if not existing_trx:
            with transaction.atomic():
                TreasuryTransaction.objects.create(
                    treasury=instance.treasury,
                    transaction_type='cash_out',
                    cash_amount=instance.amount,
                    cost_center=instance.cost_center,
                    reference_type='expense_voucher',
                    reference_id=instance.id,
                    description=f"صرف {instance.get_voucher_type_display()}: {instance.voucher_number} - {instance.beneficiary_name}",
                    date=instance.paid_date or instance.date,
                    created_by=instance.paid_by or instance.requested_by
                )

@receiver(post_save, sender=ReceiptVoucher)
def process_receipt_voucher_confirmation(sender, instance, created, **kwargs):
    """
    Automatically create a Treasury Transaction when a Receipt Voucher is marked as 'confirmed'.
    """
    if instance.status == 'confirmed':
        # Check if a transaction already exists for this voucher to avoid duplicates
        existing_trx = TreasuryTransaction.objects.filter(
            reference_type='receipt_voucher',
            reference_id=instance.id
        ).exists()
        
        if not existing_trx:
            with transaction.atomic():
                TreasuryTransaction.objects.create(
                    treasury=instance.treasury,
                    transaction_type='cash_in',
                    cash_amount=instance.cash_amount,
                    gold_weight=instance.gold_weight,
                    gold_carat=instance.gold_carat,
                    cost_center=instance.cost_center,
                    reference_type='receipt_voucher',
                    reference_id=instance.id,
                    description=f"قبض {instance.get_voucher_type_display()}: {instance.voucher_number} - {instance.payer_name}",
                    date=instance.date,
                    created_by=instance.received_by
                )

@receiver(post_save, sender=TreasuryTransfer)
def process_treasury_transfer_completion(sender, instance, created, **kwargs):
    """
    Automatically create two Treasury Transactions (Out and In) when a Transfer is 'completed'.
    """
    if instance.status == 'completed':
        # Check if transactions already exist for this transfer
        existing_trx = TreasuryTransaction.objects.filter(
            reference_type='treasury_transfer',
            reference_id=instance.id
        ).exists()
        
        if not existing_trx:
            with transaction.atomic():
                # 1. Transaction OUT from Source Treasury
                TreasuryTransaction.objects.create(
                    treasury=instance.from_treasury,
                    transaction_type='transfer_out',
                    cash_amount=instance.cash_amount,
                    gold_weight=instance.gold_weight,
                    stones_weight=instance.stones_weight,
                    gold_carat=instance.gold_carat,
                    cost_center=instance.cost_center,
                    reference_type='treasury_transfer',
                    reference_id=instance.id,
                    description=f"تحويل صادر: {instance.transfer_number} إلى {instance.to_treasury.name}",
                    date=instance.date,
                    created_by=instance.initiated_by
                )
                
                # 2. Transaction IN to Destination Treasury
                TreasuryTransaction.objects.create(
                    treasury=instance.to_treasury,
                    transaction_type='transfer_in',
                    cash_amount=instance.cash_amount,
                    gold_weight=instance.gold_weight,
                    stones_weight=instance.stones_weight,
                    gold_carat=instance.gold_carat,
                    cost_center=instance.cost_center,
                    reference_type='treasury_transfer',
                    reference_id=instance.id,
                    description=f"تحويل وارد: {instance.transfer_number} من {instance.from_treasury.name}",
                    date=instance.date,
                    created_by=instance.confirmed_by or instance.initiated_by
                )


@receiver(post_save, sender=ToolTransfer)
def process_tool_transfer_completion(sender, instance, created, **kwargs):
    """تحريك أرصدة المستلزمات عند اكتمال التحويل"""
    if instance.status == 'completed':
        with transaction.atomic():
            # 1. خصم من الخزينة المحول منها
            from_stock, _ = TreasuryTool.objects.get_or_create(
                treasury=instance.from_treasury,
                tool=instance.tool
            )
            from_stock.quantity -= instance.quantity
            from_stock.weight -= instance.weight
            from_stock.save()
            
            # 2. إضافة للخزينة المحول إليها
            to_stock, _ = TreasuryTool.objects.get_or_create(
                treasury=instance.to_treasury,
                tool=instance.tool
            )
            to_stock.quantity += instance.quantity
            to_stock.weight += instance.weight
            to_stock.save()

            # 3. مزامنة رصيد الذهب في الورشة (إذا كان المستلزم ذهبي)
            if hasattr(instance.tool, 'is_gold_tool') and instance.tool.is_gold_tool and instance.weight > 0:
                carat_name = instance.tool.carat.name if instance.tool.carat else "18"
                field_map = {'18': 'gold_balance_18', '21': 'gold_balance_21', '24': 'gold_balance_24'}
                field = next((f for k, f in field_map.items() if k in carat_name), 'gold_balance_18')

                # الخصم من ورشة الخزينة المصدر
                if instance.from_treasury.workshop:
                    current_bal = getattr(instance.from_treasury.workshop, field)
                    setattr(instance.from_treasury.workshop, field, current_bal - instance.weight)
                    instance.from_treasury.workshop.save(update_fields=[field])

                # الإضافة لورشة الخزينة الوجهة
                if instance.to_treasury.workshop:
                    current_bal = getattr(instance.to_treasury.workshop, field)
                    setattr(instance.to_treasury.workshop, field, current_bal + instance.weight)
                    instance.to_treasury.workshop.save(update_fields=[field])


@receiver(post_save, sender=CustodyTool)
def process_custody_tool_issuance(sender, instance, created, **kwargs):
    """تحديث أرصدة الخزينة عند صرف عهدة مستلزمات"""
    if created and instance.custody.status in ['pending', 'active']:
        with transaction.atomic():
            # خصم من الخزينة المحددة في سند العهدة
            treasury_stock, _ = TreasuryTool.objects.get_or_create(
                treasury=instance.custody.treasury,
                tool=instance.tool
            )
            treasury_stock.quantity -= instance.quantity
            treasury_stock.weight -= instance.weight
            treasury_stock.save()

            # مزامنة رصيد الذهب في الورشة (إذا كان المستلزم ذهبي ومرتبط بورشة)
            if hasattr(instance.tool, 'is_gold_tool') and instance.tool.is_gold_tool and instance.weight > 0:
                if instance.custody.treasury.workshop:
                    carat_name = instance.tool.carat.name if instance.tool.carat else "18"
                    field_map = {'18': 'gold_balance_18', '21': 'gold_balance_21', '24': 'gold_balance_24'}
                    field = next((f for k, f in field_map.items() if k in carat_name), 'gold_balance_18')
                    
                    workshop = instance.custody.treasury.workshop
                    current_bal = getattr(workshop, field)
                    setattr(workshop, field, current_bal - instance.weight)
                    workshop.save(update_fields=[field])
