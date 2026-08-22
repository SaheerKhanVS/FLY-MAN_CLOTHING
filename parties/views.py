import json
import urllib.request
import urllib.error
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.utils import log_action
from .forms import PartyForm, PartyTypeForm
from .models import Party, PartyType


DEFAULT_PARTY_TYPES = ["Customer", "Supplier", "Company Under", "Staff"]


def ensure_default_party_types():
    for name in DEFAULT_PARTY_TYPES:
        PartyType.objects.get_or_create(name=name)


@login_required
def party_list(request):
    ensure_default_party_types()
    query = request.GET.get("q", "").strip()
    selected_type_id = request.GET.get("type", "").strip()

    parties = Party.objects.select_related("party_type").all()

    if selected_type_id and selected_type_id.isdigit():
        parties = parties.filter(party_type_id=int(selected_type_id))

    if query:
        parties = parties.filter(
            Q(name__icontains=query) |
            Q(phone_1__icontains=query) |
            Q(phone_2__icontains=query) |
            Q(company_name__icontains=query) |
            Q(owner_name__icontains=query) |
            Q(email__icontains=query) |
            Q(locality__icontains=query) |
            Q(pincode__icontains=query)
        )

    party_types = PartyType.objects.all()
    paginator = Paginator(parties, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "query": query,
        "selected_type_id": selected_type_id,
        "party_types": party_types,
        "total_count": paginator.count,
    }
    return render(request, "parties/party_list.html", context)


@login_required
def party_detail(request, pk):
    party = get_object_or_404(Party.objects.select_related("party_type"), pk=pk)
    return render(request, "parties/party_detail.html", {"party": party})


@login_required
def party_create(request):
    ensure_default_party_types()
    if request.method == "POST":
        form = PartyForm(request.POST, request.FILES)
        if form.is_valid():
            party = form.save()
            messages.success(request, f"Party '{party.name}' created successfully.")
            log_action(user=request.user, action=f"Created party '{party.name}' ({party.party_type.name if party.party_type else 'Party'})", action_type="CREATE", request=request)
            return redirect("party_detail", pk=party.pk)
        else:
            messages.error(request, "Please correct the errors below to save the party.")
    else:
        form = PartyForm()

    party_types = PartyType.objects.all()
    context = {"form": form, "party_types": party_types, "is_edit": False}
    return render(request, "parties/party_form.html", context)


@login_required
def party_edit(request, pk):
    ensure_default_party_types()
    party = get_object_or_404(Party, pk=pk)
    if request.method == "POST":
        form = PartyForm(request.POST, request.FILES, instance=party)
        if form.is_valid():
            party = form.save()
            messages.success(request, f"Party '{party.name}' updated successfully.")
            log_action(user=request.user, action=f"Updated details for party '{party.name}'", action_type="UPDATE", request=request)
            return redirect("party_detail", pk=party.pk)
        else:
            messages.error(request, "Please correct the errors below to update the party.")
    else:
        form = PartyForm(instance=party)

    party_types = PartyType.objects.all()
    context = {"form": form, "party": party, "party_types": party_types, "is_edit": True}
    return render(request, "parties/party_form.html", context)


from core.trash_utils import move_party_to_trash


@login_required
def party_delete(request, pk):
    party = get_object_or_404(Party, pk=pk)
    if request.method == "POST":
        name = party.name
        move_party_to_trash(party, user=request.user, request=request)
        messages.success(request, f"Party '{name}' was moved to Trash Bin.")
        return redirect("party_list")
    return render(request, "parties/party_delete.html", {"party": party})




@login_required
def pincode_lookup_api(request, pincode):
    pincode = str(pincode).strip()
    if not pincode.isdigit() or len(pincode) != 6:
        return JsonResponse({"success": False, "message": "Pincode must be 6 digits."})

    url = f"https://api.postalpincode.in/pincode/{pincode}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data and isinstance(data, list) and len(data) > 0:
                    result = data[0]
                    if result.get("Status") == "Success" and result.get("PostOffice"):
                        post_offices = result["PostOffice"]
                        localities = sorted(list({po["Name"] for po in post_offices if po.get("Name")}))
                        district = post_offices[0].get("District", "")
                        state = post_offices[0].get("State", "")
                        return JsonResponse({
                            "success": True,
                            "localities": localities,
                            "district": district,
                            "state": state
                        })
    except Exception as e:
        pass

    return JsonResponse({"success": False, "message": "No details found for this pincode."})


@login_required
@require_POST
def create_party_type_api(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        name = data.get("name", "").strip()
    except Exception:
        name = request.POST.get("name", "").strip()

    if not name:
        return JsonResponse({"success": False, "message": "Party type name is required."})

    party_type, created = PartyType.objects.get_or_create(name=name)
    return JsonResponse({
        "success": True,
        "id": party_type.id,
        "name": party_type.name,
        "created": created
    })


@login_required
def get_party_types_api(request):
    ensure_default_party_types()
    types = PartyType.objects.all()
    data = []
    for pt in types:
        data.append({
            "id": pt.id,
            "name": pt.name,
            "count": pt.parties.count()
        })
    return JsonResponse({"success": True, "types": data})


@login_required
@require_POST
def edit_party_type_api(request, pk):
    party_type = get_object_or_404(PartyType, pk=pk)
    try:
        data = json.loads(request.body.decode("utf-8"))
        name = data.get("name", "").strip()
    except Exception:
        name = request.POST.get("name", "").strip()

    if not name:
        return JsonResponse({"success": False, "message": "Party type name cannot be empty."})

    if PartyType.objects.filter(name__iexact=name).exclude(pk=pk).exists():
        return JsonResponse({"success": False, "message": "Another party type with this name already exists."})

    party_type.name = name
    party_type.save()
    return JsonResponse({"success": True, "id": party_type.id, "name": party_type.name})


@login_required
@require_POST
def delete_party_type_api(request, pk):
    party_type = get_object_or_404(PartyType, pk=pk)
    assigned_count = party_type.parties.count()
    if assigned_count > 0:
        return JsonResponse({
            "success": False,
            "message": f"Cannot delete '{party_type.name}' because it is assigned to {assigned_count} party account(s)."
        })

    party_type.delete()
    return JsonResponse({"success": True, "id": pk, "name": party_type.name})
