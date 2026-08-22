from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Party, PartyType


class PartiesAppTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owneruser",
            email="owner@example.com",
            password="ownerpassword123",
            phone="9876543210"
        )
        self.client.force_login(self.owner)

        self.type_customer = PartyType.objects.create(name="Customer")
        self.type_supplier = PartyType.objects.create(name="Supplier")

        self.party1 = Party.objects.create(
            name="John Doe",
            party_type=self.type_customer,
            email="john@example.com",
            phone_1="9998887770",
            company_name="John Enterprises",
            pincode="682001",
            locality="Ernakulam",
            district="Ernakulam",
            state="Kerala",
            balance=1500.00
        )

    def test_party_list_view(self):
        url = reverse("party_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Customer")

    def test_party_list_filtering(self):
        url = reverse("party_list") + f"?type={self.type_customer.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

        url_supplier = reverse("party_list") + f"?type={self.type_supplier.id}"
        response2 = self.client.get(url_supplier)
        self.assertEqual(response2.status_code, 200)
        self.assertNotContains(response2, "John Doe")

    def test_party_create_view(self):
        url = reverse("party_create")
        response = self.client.post(url, {
            "name": "Jane Smith",
            "party_type": self.type_supplier.id,
            "email": "jane@supplier.com",
            "phone_1": "8887776660",
            "balance": "5000.00",
        })
        self.assertEqual(response.status_code, 302)
        new_party = Party.objects.get(name="Jane Smith")
        self.assertEqual(new_party.party_type, self.type_supplier)
        self.assertEqual(float(new_party.balance), 5000.00)

    def test_party_edit_view(self):
        url = reverse("party_edit", kwargs={"pk": self.party1.pk})
        response = self.client.post(url, {
            "name": "John Doe Updated",
            "party_type": self.type_customer.id,
            "email": "john@example.com",
            "phone_1": "9998887770",
            "balance": "2000.00",
        })
        self.assertEqual(response.status_code, 302)
        self.party1.refresh_from_db()
        self.assertEqual(self.party1.name, "John Doe Updated")
        self.assertEqual(float(self.party1.balance), 2000.00)

    def test_party_delete_view(self):
        url = reverse("party_delete", kwargs={"pk": self.party1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Party.objects.filter(pk=self.party1.pk).exists())

    def test_create_party_type_api(self):
        url = reverse("create_party_type_api")
        response = self.client.post(
            url,
            data={"name": "Wholesaler"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["name"], "Wholesaler")
        self.assertTrue(PartyType.objects.filter(name="Wholesaler").exists())

    def test_edit_party_type_api(self):
        url = reverse("edit_party_type_api", kwargs={"pk": self.type_supplier.pk})
        response = self.client.post(
            url,
            data={"name": "Vendor / Supplier"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.type_supplier.refresh_from_db()
        self.assertEqual(self.type_supplier.name, "Vendor / Supplier")

    def test_delete_party_type_api_assigned_fails(self):
        # type_customer is assigned to party1
        url = reverse("delete_party_type_api", kwargs={"pk": self.type_customer.pk})
        response = self.client.post(url, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertTrue(PartyType.objects.filter(pk=self.type_customer.pk).exists())

    def test_delete_party_type_api_unassigned_succeeds(self):
        # type_supplier has 0 parties assigned
        url = reverse("delete_party_type_api", kwargs={"pk": self.type_supplier.pk})
        response = self.client.post(url, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertFalse(PartyType.objects.filter(pk=self.type_supplier.pk).exists())

    @patch("urllib.request.urlopen")
    def test_pincode_lookup_api(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"""[
            {
                "Status": "Success",
                "PostOffice": [
                    {"Name": "Kochi", "District": "Ernakulam", "State": "Kerala"}
                ]
            }
        ]"""
        mock_urlopen.return_value.__enter__.return_value = mock_response

        url = reverse("pincode_lookup_api", kwargs={"pincode": "682001"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("Kochi", data["localities"])
        self.assertEqual(data["district"], "Ernakulam")
        self.assertEqual(data["state"], "Kerala")

    def test_avatar_properties(self):
        self.assertEqual(self.party1.avatar_initial, "J")
        self.assertTrue(self.party1.avatar_bg_color.startswith("#"))
