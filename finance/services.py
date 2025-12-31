from django.db import transaction
from .models import JournalEntry, LedgerEntry, FinanceSettings, Account
from decimal import Decimal

class FinanceService:
    @staticmethod
    @transaction.atomic
    def process_sales_invoice(invoice):
        """
        Generates automatic journal entries for a sales invoice.
        Entries:
        1. Debit Cash/Bank (Full Amount)
        2. Credit Sales Revenue (Invoice Total - VAT - Gold Cost)
        3. Credit Gold Inventory (Gold Cost / Weight)
        4. Credit VAT Payable (VAT Amount)
        """
        settings = FinanceSettings.objects.get(pk=1)
        
        # 1. Create Journal Entry Header
        journal = JournalEntry.objects.create(
            reference=f"INV-{invoice.invoice_number}",
            description=f"Sales Invoice for customer {invoice.customer.name if invoice.customer else 'Guest'}"
        )

        # 2. Entry: Cash Debit
        LedgerEntry.objects.create(
            journal_entry=journal,
            account=settings.cash_account,
            debit=invoice.grand_total,
            credit=0
        )
        settings.cash_account.balance += invoice.grand_total
        settings.cash_account.save()

        # 3. Entry: Gold Inventory Credit (Cost of Gold)
        # Note: In gold ERP, we track weight too
        total_weight = sum(item.sold_weight for item in invoice.items.all())
        LedgerEntry.objects.create(
            journal_entry=journal,
            account=settings.inventory_gold_account,
            debit=0,
            credit=invoice.total_gold_value,
            gold_credit=total_weight
        )
        settings.inventory_gold_account.balance -= invoice.total_gold_value
        settings.inventory_gold_account.gold_balance -= total_weight
        settings.inventory_gold_account.save()

        # 4. Entry: Sales Revenue (Labor Fees + Markup)
        revenue_amount = invoice.total_labor_value # Simplified: Sales Revenue = Labor Fees
        LedgerEntry.objects.create(
            journal_entry=journal,
            account=settings.sales_revenue_account,
            debit=0,
            credit=revenue_amount
        )
        settings.sales_revenue_account.balance += revenue_amount
        settings.sales_revenue_account.save()

        # 5. Entry: VAT Credit
        if invoice.total_tax > 0:
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=settings.vat_account,
                debit=0,
                credit=invoice.total_tax
            )
            settings.vat_account.balance += invoice.total_tax
            settings.vat_account.save()

        return journal
