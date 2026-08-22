from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from parties.models import Party, PartyType
from .models import Transaction


class TransactionsAppTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owneruser",
            email="owner@example.com",
            password="ownerpassword123",
            phone="9876543210"
        )
        self.client.force_login(self.owner)

        self.party_type = PartyType.objects.create(name="Customer")
        self.party1 = Party.objects.create(
            name="Alice",
            party_type=self.party_type,
            balance=Decimal("1000.00")
        )
        self.party2 = Party.objects.create(
            name="Bob",
            party_type=self.party_type,
            balance=Decimal("500.00")
        )

    def test_transaction_list_view(self):
        url = reverse("transaction_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_receipt_transaction_adjusts_balances(self):
        url = reverse("transaction_create")
        response = self.client.post(url, {
            "transaction_type": "receipt",
            "from_party": self.party1.id,
            "to_party": self.party2.id,
            "amount": "200.00",
            "reason": "Payment for invoice #101",
            "date_time": "2026-08-11T12:00",
        })
        self.assertEqual(response.status_code, 302)

        self.party1.refresh_from_db()
        self.party2.refresh_from_db()

        # party1 balance should decrease by 200 (1000 - 200 = 800)
        self.assertEqual(self.party1.balance, Decimal("800.00"))
        # party2 balance should increase by 200 (500 + 200 = 700)
        self.assertEqual(self.party2.balance, Decimal("700.00"))

        txn = Transaction.objects.first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, Decimal("200.00"))
        self.assertEqual(txn.from_party, self.party1)
        self.assertEqual(txn.to_party, self.party2)

    def test_create_payment_transaction_adjusts_balances(self):
        url = reverse("transaction_create")
        response = self.client.post(url, {
            "transaction_type": "payment",
            "from_party": self.party2.id,
            "to_party": self.party1.id,
            "amount": "300.00",
            "reason": "Vendor payout",
            "date_time": "2026-08-11T12:00",
        })
        self.assertEqual(response.status_code, 302)

        self.party1.refresh_from_db()
        self.party2.refresh_from_db()

        # party2 balance decreases by 300 (500 - 300 = 200)
        self.assertEqual(self.party2.balance, Decimal("200.00"))
        # party1 balance increases by 300 (1000 + 300 = 1300)
        self.assertEqual(self.party1.balance, Decimal("1300.00"))

    def test_delete_transaction_reverses_party_balances(self):
        txn = Transaction.objects.create(
            transaction_type="receipt",
            from_party=self.party1,
            to_party=self.party2,
            amount=Decimal("150.00"),
            reason="Test Voucher",
            created_by=self.owner
        )
        # Apply initial balance changes
        self.party1.balance -= Decimal("150.00")
        self.party1.save()
        self.party2.balance += Decimal("150.00")
        self.party2.save()

        url = reverse("transaction_delete", kwargs={"pk": txn.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.party1.refresh_from_db()
        self.party2.refresh_from_db()

        # Balances should be restored to initial 1000 and 500
        self.assertEqual(self.party1.balance, Decimal("1000.00"))
        self.assertEqual(self.party2.balance, Decimal("500.00"))
        self.assertFalse(Transaction.objects.filter(pk=txn.pk).exists())
