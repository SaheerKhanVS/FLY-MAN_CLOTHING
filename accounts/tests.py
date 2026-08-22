from django.test import TestCase
from django.urls import reverse
from accounts.models import User, StaffProfile


class ProfileAndStaffPermissionsTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owneruser",
            email="owner@example.com",
            password="ownerpassword123",
            phone="9876543210"
        )
        self.owner.raw_password = "ownerpassword123"
        self.owner.save()

        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="staffpassword123",
            phone="9876543211",
            user_type=User.UserType.STAFF
        )
        self.staff_user.raw_password = "staffpassword123"
        self.staff_user.save()
        self.staff_profile, _ = StaffProfile.objects.get_or_create(user=self.staff_user, defaults={"staff_code": "STF00001"})

    def test_owner_profile_view_shows_credentials(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "owneruser")
        self.assertContains(response, "ownerpassword123")

    def test_staff_profile_view_does_not_show_password(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "staffpassword123")

    def test_owner_can_edit_own_username_and_password(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("profile"), {
            "first_name": "NewOwner",
            "last_name": "Name",
            "email": "owner@example.com",
            "phone": "9876543210",
            "username": "newownerusername",
            "password": "newownerpassword123",
        })
        self.assertEqual(response.status_code, 302)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.username, "newownerusername")
        self.assertEqual(self.owner.raw_password, "newownerpassword123")
        self.assertTrue(self.owner.check_password("newownerpassword123"))

    def test_owner_can_view_and_edit_staff_credentials(self):
        self.client.force_login(self.owner)
        # View staff profile
        url_profile = reverse("staff_profile", kwargs={"pk": self.staff_profile.pk})
        response = self.client.get(url_profile)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "staffuser")
        self.assertContains(response, "staffpassword123")

        # Edit staff credentials
        url_edit = reverse("staff_edit", kwargs={"pk": self.staff_profile.pk})
        response = self.client.post(url_edit, {
            "username": "updatedstaffuser",
            "password": "updatedstaffpassword123",
            "first_name": "Updated",
            "last_name": "Staff",
            "phone": "9876543211",
            "email": "staff@example.com",
            "is_active": True,
            "joining_date": "2026-01-01",
            "salary": "30000.00",
        })
        self.assertEqual(response.status_code, 302)
        self.staff_user.refresh_from_db()
        self.assertEqual(self.staff_user.username, "updatedstaffuser")
        self.assertEqual(self.staff_user.raw_password, "updatedstaffpassword123")
        self.assertTrue(self.staff_user.check_password("updatedstaffpassword123"))

    def test_auto_creates_staff_party_on_staff_creation(self):
        from parties.models import Party
        self.client.force_login(self.owner)
        url_create = reverse("staff_create")
        response = self.client.post(url_create, {
            "username": "newstaffmember",
            "password": "staffpassword123",
            "first_name": "Alex",
            "last_name": "Taylor",
            "phone": "9876543299",
            "email": "alex@example.com",
            "joining_date": "2026-01-15",
            "salary": "25000.00",
            "notes": "Head tailor",
        })
        self.assertEqual(response.status_code, 302)
        staff_party = Party.objects.filter(phone_1="9876543299").first()
        self.assertIsNotNone(staff_party)
        self.assertEqual(staff_party.name, "Alex Taylor")
        self.assertEqual(staff_party.party_type.name, "Staff")
        self.assertEqual(staff_party.email, "alex@example.com")
        self.assertEqual(staff_party.manual_address, "Head tailor")
