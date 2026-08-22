from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from core.utils import log_action
from parties.models import Party
from .forms import TransactionForm
from .models import Transaction



def adjust_party_balances(from_party, to_party, amount, reverse=False):
    """
    Adjusts party balances atomically.
    Normally (reverse=False):
      from_party.balance -= amount
      to_party.balance += amount
    When reversing (reverse=True):
      from_party.balance += amount
      to_party.balance -= amount
    """
    multiplier = Decimal("-1") if reverse else Decimal("1")
    delta = Decimal(str(amount)) * multiplier

    if from_party:
        from_party.balance = Decimal(str(from_party.balance)) - delta
        from_party.save()

    if to_party:
        to_party.balance = Decimal(str(to_party.balance)) + delta
        to_party.save()


@login_required
def transaction_list(request):
    query = request.GET.get("q", "").strip()
    selected_type = request.GET.get("type", "").strip()
    selected_party_id = request.GET.get("party", "").strip()

    transactions_qs = Transaction.objects.select_related(
        "from_party", "to_party", "from_party__party_type", "to_party__party_type", "created_by"
    )

    if query:
        transactions_qs = transactions_qs.filter(
            Q(from_party__name__icontains=query) |
            Q(to_party__name__icontains=query) |
            Q(reason__icontains=query) |
            Q(amount__icontains=query)
        )

    if selected_type in ["receipt", "payment"]:
        transactions_qs = transactions_qs.filter(transaction_type=selected_type)

    if selected_party_id:
        transactions_qs = transactions_qs.filter(
            Q(from_party_id=selected_party_id) | Q(to_party_id=selected_party_id)
        )

    paginator = Paginator(transactions_qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    parties = Party.objects.all().select_related("party_type")

    return render(
        request,
        "transactions/transaction_list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "selected_type": selected_type,
            "selected_party_id": selected_party_id,
            "parties": parties,
        }
    )


@login_required
def transaction_detail(request, pk):
    txn = get_object_or_404(
        Transaction.objects.select_related("from_party", "to_party", "created_by"),
        pk=pk
    )
    return render(request, "transactions/transaction_detail.html", {"transaction": txn})


@login_required
def transaction_create(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                txn = form.save(commit=False)
                txn.created_by = request.user
                txn.save()

                # Update balances
                adjust_party_balances(txn.from_party, txn.to_party, txn.amount, reverse=False)

            messages.success(
                request,
                f"{txn.get_transaction_type_display()} of ₹{txn.amount} recorded successfully!"
            )
            log_action(
                user=request.user,
                action=f"Created {txn.get_transaction_type_display()} transaction #{txn.pk} of ₹{txn.amount}",
                action_type="CREATE",
                details=f"From: {txn.from_party.name if txn.from_party else 'N/A'}, To: {txn.to_party.name if txn.to_party else 'N/A'}",
                request=request
            )
            return redirect("transaction_detail", pk=txn.pk)
    else:
        initial_type = request.GET.get("type", "receipt")
        initial_from = request.GET.get("from_party")
        initial_to = request.GET.get("to_party")
        initial_data = {"transaction_type": initial_type}
        if initial_from:
            initial_data["from_party"] = initial_from
        if initial_to:
            initial_data["to_party"] = initial_to
        form = TransactionForm(initial=initial_data)

    return render(request, "transactions/transaction_form.html", {"form": form, "is_edit": False})


from core.trash_utils import move_transaction_to_trash


@login_required
def transaction_delete(request, pk):
    txn = get_object_or_404(
        Transaction.objects.select_related("from_party", "to_party"),
        pk=pk
    )
    if request.method == "POST":
        move_transaction_to_trash(txn, user=request.user, request=request)
        messages.success(request, f"Transaction #{pk} moved to Trash Bin and party balances updated.")
        return redirect("transaction_list")

    return render(request, "transactions/transaction_delete.html", {"transaction": txn})


