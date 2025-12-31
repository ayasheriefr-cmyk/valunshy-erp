from django.test import TestCase
from django.contrib.auth.models import User
from finance.treasury_models import Treasury, TreasuryTransaction
from decimal import Decimal
from django.utils import timezone
from finance.models import Account, FinanceSettings, JournalEntry
from core.models import Carat

class TreasuryTests(TestCase):
    def setUp(self):
        # Create a user for assigning responsibility
        self.user = User.objects.create_user(username='treasurer', password='password')
        
        # 1. Setup Chart of Accounts (Essential for Auto-Journal)
        self.treasury_acc = Account.objects.create(code="101", name="Treasury Account", account_type="asset")
        self.revenue_acc = Account.objects.create(code="401", name="Sales Revenue", account_type="revenue")
        
        # 2. Setup Finance Settings
        FinanceSettings.objects.create(
            cash_account=self.treasury_acc,
            sales_revenue_account=self.revenue_acc,
            cost_of_gold_account=self.revenue_acc
        )

        # 3. Setup Carat
        self.carat21 = Carat.objects.create(name="21K", purity=Decimal('0.875'))

        # 4. Create a Main Treasury LINKED to Account
        self.main_treasury = Treasury.objects.create(
            name="Main Vault",
            code="TR-001",
            treasury_type='main',
            responsible_user=self.user,
            cash_balance=Decimal('100000.00'),
            gold_balance_21=Decimal('500.000'),
            linked_account=self.treasury_acc # Link it!
        )

    def test_create_treasury(self):
        """Test that a treasury is created correctly with initial balances"""
        self.assertEqual(self.main_treasury.code, "TR-001")
        self.assertEqual(self.main_treasury.cash_balance, Decimal('100000.00'))
        self.assertEqual(self.main_treasury.gold_balance_21, Decimal('500.000'))

    def test_automated_journal_entry(self):
        """Test that a Journal Entry is automatically created on Cash In"""
        deposit_amount = Decimal('1000.00')
        
        # Create Transaction
        TreasuryTransaction.objects.create(
            treasury=self.main_treasury,
            transaction_type='cash_in',
            cash_amount=deposit_amount,
            description="Auto Journal Test",
            created_by=self.user
        )
        
        # Check if Journal Entry exists
        self.assertEqual(JournalEntry.objects.count(), 1, "Journal Entry should be auto-created")
        
        journal = JournalEntry.objects.first()
        self.assertEqual(journal.ledger_entries.count(), 2, "Should have Debit and Credit legs")
        
        # Check Debit (Treasury)
        debit_entry = journal.ledger_entries.get(account=self.treasury_acc)
        self.assertEqual(debit_entry.debit, deposit_amount)
        
        # Check Credit (Revenue)
        credit_entry = journal.ledger_entries.get(account=self.revenue_acc)
        self.assertEqual(credit_entry.credit, deposit_amount)

    def test_cash_deposit_transaction(self):
        """Test cash deposit increases balance via signal"""
        initial_balance = self.main_treasury.cash_balance
        deposit_amount = Decimal('50000.00')

        # Create Transaction
        TreasuryTransaction.objects.create(
            treasury=self.main_treasury,
            transaction_type='cash_in',
            cash_amount=deposit_amount,
            description="Sales Deposit",
            created_by=self.user
        )

        self.main_treasury.refresh_from_db()
        self.assertEqual(self.main_treasury.cash_balance, initial_balance + deposit_amount)

    def test_gold_withdrawal_transaction(self):
        """Test gold withdrawal decreases balance via signal"""
        initial_gold = self.main_treasury.gold_balance_21
        withdraw_weight = Decimal('50.000')

        # Create Transaction
        TreasuryTransaction.objects.create(
            treasury=self.main_treasury,
            transaction_type='gold_out',
            gold_weight=withdraw_weight,
            gold_carat=self.carat21,
            description="Workshop Supply",
            created_by=self.user
        )

        self.main_treasury.refresh_from_db()
        self.assertEqual(self.main_treasury.gold_balance_21, initial_gold - withdraw_weight)
        
    def test_insufficient_funds(self):
        """Test checking for insufficient funds logic (Manual Check)"""
        withdraw_amount = Decimal('200000.00') # More than 100k balance
        
        has_funds = self.main_treasury.cash_balance >= withdraw_amount
        self.assertFalse(has_funds, "Should not allow withdrawal of more than balance")
