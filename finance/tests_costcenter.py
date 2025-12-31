from django.test import TestCase
from django.contrib.auth.models import User
from finance.treasury_models import Treasury, TreasuryTransaction, ExpenseVoucher, ReceiptVoucher, TreasuryTransfer
from finance.models import Account, FinanceSettings, JournalEntry, CostCenter, LedgerEntry
from decimal import Decimal
from django.utils import timezone

class CostCenterIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        
        # Setup Chart of Accounts
        self.cash_acc = Account.objects.create(code="101", name="Cash Account", account_type="asset")
        self.revenue_acc = Account.objects.create(code="401", name="Sales Revenue", account_type="revenue")
        self.expense_acc = Account.objects.create(code="501", name="General Expenses", account_type="expense")
        
        # Setup Finance Settings
        FinanceSettings.objects.create(
            cash_account=self.cash_acc,
            sales_revenue_account=self.revenue_acc,
            cost_of_gold_account=self.expense_acc 
        )

        # Create Treasury
        self.treasury = Treasury.objects.create(
            name="Main Treasury",
            code="TR-001",
            cash_balance=Decimal('10000.00'),
            linked_account=self.cash_acc,
            responsible_user=self.user
        )

        # Create Cost Center
        self.cost_center = CostCenter.objects.create(
            code="CC-001",
            name="Sales Department"
        )

    def test_expense_voucher_automation(self):
        """Test that paying an expense voucher creates a transaction and journal entry with cost center"""
        voucher = ExpenseVoucher.objects.create(
            voucher_type='expense',
            status='draft',
            treasury=self.treasury,
            beneficiary_name="John Doe",
            amount=Decimal('500.00'),
            cost_center=self.cost_center,
            description="Office Supplies",
            requested_by=self.user,
            paid_by=self.user
        )

        # Mark as paid
        voucher.status = 'paid'
        voucher.save()

        # 1. Check Treasury Transaction
        trx = TreasuryTransaction.objects.filter(reference_type='expense_voucher', reference_id=voucher.id).first()
        self.assertIsNotNone(trx)
        self.assertEqual(trx.cash_amount, Decimal('500.00'))
        self.assertEqual(trx.cost_center, self.cost_center)
        self.assertEqual(trx.transaction_type, 'cash_out')

        # 2. Check Journal Entry and Ledger Entries
        journal = JournalEntry.objects.filter(reference=f"TRX-{trx.id}").first()
        self.assertIsNotNone(journal)
        
        ledger_entries = journal.ledger_entries.all()
        self.assertEqual(ledger_entries.count(), 2)
        
        for entry in ledger_entries:
            self.assertEqual(entry.cost_center, self.cost_center)

    def test_receipt_voucher_automation(self):
        """Test that confirming a receipt voucher creates a transaction and journal entry with cost center"""
        voucher = ReceiptVoucher.objects.create(
            voucher_type='collection',
            status='draft',
            treasury=self.treasury,
            payer_name="Customer A",
            cash_amount=Decimal('1000.00'),
            cost_center=self.cost_center,
            description="Payment received",
            received_by=self.user
        )

        # Confirm voucher
        voucher.status = 'confirmed'
        voucher.save()

        # 1. Check Treasury Transaction
        trx = TreasuryTransaction.objects.filter(reference_type='receipt_voucher', reference_id=voucher.id).first()
        self.assertIsNotNone(trx)
        self.assertEqual(trx.cash_amount, Decimal('1000.00'))
        self.assertEqual(trx.cost_center, self.cost_center)
        self.assertEqual(trx.transaction_type, 'cash_in')

        # 2. Check Journal Entry and Ledger Entries
        journal = JournalEntry.objects.filter(reference=f"TRX-{trx.id}").first()
        self.assertIsNotNone(journal)
        
        ledger_entries = journal.ledger_entries.all()
        self.assertEqual(ledger_entries.count(), 2)
        
        for entry in ledger_entries:
            self.assertEqual(entry.cost_center, self.cost_center)

    def test_treasury_transfer_automation(self):
        """Test that completing a treasury transfer creates two transactions and one journal entry with cost center"""
        # Create second treasury
        other_acc = Account.objects.create(code="102", name="Secondary Cash", account_type="asset")
        other_treasury = Treasury.objects.create(
            name="Secondary Treasury",
            code="TR-002",
            cash_balance=Decimal('5000.00'),
            linked_account=other_acc,
            responsible_user=self.user
        )

        transfer = TreasuryTransfer.objects.create(
            from_treasury=self.treasury,
            to_treasury=other_treasury,
            cash_amount=Decimal('1000.00'),
            cost_center=self.cost_center,
            initiated_by=self.user,
            status='pending'
        )

        # Complete transfer
        transfer.status = 'completed'
        transfer.save()

        # 1. Check Treasury Transactions
        # Should have 2 transactions (out and in)
        out_trx = TreasuryTransaction.objects.filter(reference_type='treasury_transfer', reference_id=transfer.id, transaction_type='transfer_out').first()
        in_trx = TreasuryTransaction.objects.filter(reference_type='treasury_transfer', reference_id=transfer.id, transaction_type='transfer_in').first()
        
        self.assertIsNotNone(out_trx)
        self.assertIsNotNone(in_trx)
        self.assertEqual(out_trx.cost_center, self.cost_center)
        self.assertEqual(in_trx.cost_center, self.cost_center)

        # 2. Check Journal Entry (Only 1 should exist for this transfer)
        transfer_journals = JournalEntry.objects.filter(reference=f"TRX-{out_trx.id}").all()
        self.assertEqual(transfer_journals.count(), 1)
        
        journal = transfer_journals.first()
        self.assertEqual(journal.ledger_entries.count(), 2)
        
        # Verify legs
        debit_leg = journal.ledger_entries.get(account=other_acc)
        credit_leg = journal.ledger_entries.get(account=self.cash_acc)
        
        self.assertEqual(debit_leg.debit, Decimal('1000.00'))
        self.assertEqual(credit_leg.credit, Decimal('1000.00'))
        self.assertEqual(debit_leg.cost_center, self.cost_center)
        self.assertEqual(credit_leg.cost_center, self.cost_center)

        # 3. Check Treasury Balances
        self.treasury.refresh_from_db()
        other_treasury.refresh_from_db()
        self.assertEqual(self.treasury.cash_balance, Decimal('9000.00'))
        self.assertEqual(other_treasury.cash_balance, Decimal('6000.00'))
