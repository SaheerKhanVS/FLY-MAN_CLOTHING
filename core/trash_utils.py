from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from core.models import TrashItem
from core.utils import log_action


def move_party_to_trash(party, user=None, request=None):
    """
    Serializes a Party and moves it to TrashItem before deleting.
    """
    serialized = {
        "name": party.name,
        "party_type_id": party.party_type_id,
        "party_type_name": party.party_type.name if party.party_type else "Party",
        "email": party.email,
        "phone_1": party.phone_1,
        "phone_2": party.phone_2,
        "pincode": party.pincode,
        "locality": party.locality,
        "district": party.district,
        "state": party.state,
        "manual_address": party.manual_address,
        "company_name": party.company_name,
        "owner_name": party.owner_name,
        "balance": str(party.balance),
    }

    user_name = "System"
    actual_user = user
    if not actual_user and request and getattr(request, "user", None) and request.user.is_authenticated:
        actual_user = request.user
    if actual_user:
        user_name = getattr(actual_user, "full_name", None) or actual_user.username

    trash_item = TrashItem.objects.create(
        item_type="PARTY",
        title=f"Party: {party.name}",
        deleted_by=actual_user,
        deleted_by_name=user_name,
        serialized_data=serialized,
    )

    party.delete()

    log_action(
        user=actual_user,
        action=f"Moved party '{party.name}' to Trash Bin",
        action_type="DELETE",
        request=request
    )
    return trash_item


def move_transaction_to_trash(txn, user=None, request=None):
    """
    Serializes a Transaction, reverses party balances, and moves it to TrashItem before deleting.
    """
    from transactions.views import adjust_party_balances

    serialized = {
        "transaction_type": txn.transaction_type,
        "transaction_type_display": txn.get_transaction_type_display(),
        "from_party_id": txn.from_party_id,
        "from_party_name": txn.from_party.name if txn.from_party else "—",
        "to_party_id": txn.to_party_id,
        "to_party_name": txn.to_party.name if txn.to_party else "—",
        "amount": str(txn.amount),
        "reason": txn.reason,
        "date_time": txn.date_time.isoformat() if txn.date_time else timezone.now().isoformat(),
        "created_by_id": txn.created_by_id,
    }

    user_name = "System"
    actual_user = user
    if not actual_user and request and getattr(request, "user", None) and request.user.is_authenticated:
        actual_user = request.user
    if actual_user:
        user_name = getattr(actual_user, "full_name", None) or actual_user.username

    with transaction.atomic():
        # Revert party balances
        adjust_party_balances(txn.from_party, txn.to_party, txn.amount, reverse=True)

        trash_item = TrashItem.objects.create(
            item_type="TRANSACTION",
            title=f"{txn.get_transaction_type_display()} #{txn.id} - ₹{txn.amount} ({serialized['from_party_name']} ➔ {serialized['to_party_name']})",
            deleted_by=actual_user,
            deleted_by_name=user_name,
            serialized_data=serialized,
        )

        txn.delete()

    log_action(
        user=actual_user,
        action=f"Moved {serialized['transaction_type_display']} #{trash_item.pk} (₹{serialized['amount']}) to Trash Bin",
        action_type="DELETE",
        request=request
    )
    return trash_item


def move_staff_to_trash(profile_obj, user=None, request=None):
    """
    Serializes a StaffProfile and its User object, moving it to TrashItem before deleting.
    """
    stf_user = profile_obj.user
    serialized = {
        "username": stf_user.username,
        "first_name": stf_user.first_name,
        "last_name": stf_user.last_name,
        "email": stf_user.email,
        "phone": stf_user.phone,
        "raw_password": stf_user.raw_password,
        "staff_code": profile_obj.staff_code,
        "joining_date": profile_obj.joining_date.isoformat() if profile_obj.joining_date else None,
        "salary": str(profile_obj.salary),
        "commission_enabled": profile_obj.commission_enabled,
        "notes": profile_obj.notes,
    }

    user_name = "System"
    actual_user = user
    if not actual_user and request and getattr(request, "user", None) and request.user.is_authenticated:
        actual_user = request.user
    if actual_user:
        user_name = getattr(actual_user, "full_name", None) or actual_user.username

    trash_item = TrashItem.objects.create(
        item_type="STAFF",
        title=f"Staff: {stf_user.full_name} ({profile_obj.staff_code})",
        deleted_by=actual_user,
        deleted_by_name=user_name,
        serialized_data=serialized,
    )

    stf_user.delete()

    log_action(
        user=actual_user,
        action=f"Moved staff member '{stf_user.full_name}' to Trash Bin",
        action_type="DELETE",
        request=request
    )
    return trash_item


def restore_trash_item(trash_item, user=None, request=None):
    """
    Restores a trash item back into the active database system.
    """
    from parties.models import Party, PartyType
    from transactions.models import Transaction
    from transactions.views import adjust_party_balances
    from accounts.models import User, StaffProfile
    from datetime import datetime

    data = trash_item.serialized_data
    item_type = trash_item.item_type
    restored_obj = None

    actual_user = user
    if not actual_user and request and getattr(request, "user", None) and request.user.is_authenticated:
        actual_user = request.user

    if item_type == "PARTY":
        party_type = None
        if data.get("party_type_id"):
            party_type = PartyType.objects.filter(pk=data["party_type_id"]).first()
        if not party_type:
            party_type, _ = PartyType.objects.get_or_create(name=data.get("party_type_name", "Customer"))

        restored_obj = Party.objects.create(
            name=data.get("name", "Restored Party"),
            party_type=party_type,
            email=data.get("email", ""),
            phone_1=data.get("phone_1", ""),
            phone_2=data.get("phone_2", ""),
            pincode=data.get("pincode", ""),
            locality=data.get("locality", ""),
            district=data.get("district", ""),
            state=data.get("state", ""),
            manual_address=data.get("manual_address", ""),
            company_name=data.get("company_name", ""),
            owner_name=data.get("owner_name", ""),
            balance=Decimal(str(data.get("balance", "0.00"))),
        )

    elif item_type == "TRANSACTION":
        from_party = Party.objects.filter(pk=data.get("from_party_id")).first()
        to_party = Party.objects.filter(pk=data.get("to_party_id")).first()

        date_val = timezone.now()
        if data.get("date_time"):
            try:
                date_val = datetime.fromisoformat(data["date_time"])
            except Exception:
                pass

        created_by_user = User.objects.filter(pk=data.get("created_by_id")).first() or actual_user

        with transaction.atomic():
            restored_obj = Transaction.objects.create(
                transaction_type=data.get("transaction_type", "receipt"),
                from_party=from_party,
                to_party=to_party,
                amount=Decimal(str(data.get("amount", "0.00"))),
                reason=data.get("reason", ""),
                date_time=date_val,
                created_by=created_by_user,
            )
            # Re-adjust party balances for restored transaction
            adjust_party_balances(from_party, to_party, restored_obj.amount, reverse=False)

    elif item_type == "STAFF":
        username = data.get("username", "staff_restored")
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        phone = data.get("phone", "")
        if phone and User.objects.filter(phone=phone).exists():
            phone = f"{phone}_{counter}"

        joining_date = None
        if data.get("joining_date"):
            try:
                joining_date = datetime.fromisoformat(data["joining_date"]).date()
            except Exception:
                pass

        with transaction.atomic():
            user_obj = User.objects.create(
                username=username,
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                email=data.get("email", ""),
                phone=phone,
                user_type=User.UserType.STAFF,
                is_active=True,
                raw_password=data.get("raw_password", "staff123"),
            )
            user_obj.set_password(data.get("raw_password", "staff123"))
            user_obj.save()

            profile_obj, _ = StaffProfile.objects.get_or_create(user=user_obj)
            profile_obj.staff_code = data.get("staff_code") or f"STF{user_obj.pk:05d}"
            profile_obj.joining_date = joining_date
            profile_obj.salary = Decimal(str(data.get("salary", "0.00")))
            profile_obj.commission_enabled = data.get("commission_enabled", False)
            profile_obj.notes = data.get("notes", "")
            profile_obj.save()

            restored_obj = profile_obj

    # Remove item from trash and log restoration
    title = trash_item.title
    trash_item.delete()

    log_action(
        user=actual_user,
        action=f"Restored item '{title}' from Trash Bin",
        action_type="CREATE",
        request=request
    )

    return restored_obj
