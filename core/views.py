import re
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from accounts.decorators import owner_required
from accounts.models import User
from weasyprint import HTML
from django.template.loader import render_to_string
from django.core.cache import cache
from .context_processors import clear_system_settings_cache
from .forms import CompanyForm, SystemSettingsForm
from .models import Company, SystemSettings, Color, ActionHistory, TrashItem
from .utils import log_action
from .trash_utils import restore_trash_item


HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")



@login_required
def dashboard(request):
    return render(request, "core/dashbord.html", {"current_profile": request.user.staff_profile})


def get_system_theme_colors():
    cached = cache.get("flymen_theme_colors")
    if cached:
        return cached

    settings_obj = SystemSettings.objects.select_related("primary_color", "secondary_color").first()
    primary = "#7c5cff"
    secondary = "#00d4c8"
    if settings_obj:
        if settings_obj.primary_color and settings_obj.primary_color.hex_code:
            primary = settings_obj.primary_color.hex_code
        if settings_obj.secondary_color and settings_obj.secondary_color.hex_code:
            secondary = settings_obj.secondary_color.hex_code

    result = (primary, secondary)
    cache.set("flymen_theme_colors", result, 600)
    return result


@owner_required
def company_profile(request):
    company = Company.objects.select_related("owner", "owner__staff_profile", "settings").first()
    if company and not company.owner:
        owner_user = User.objects.filter(user_type=User.UserType.OWNER).first() or request.user
        company.owner = owner_user
        company.save(update_fields=["owner"])
        company = Company.objects.select_related("owner", "owner__staff_profile", "settings").first()
    primary_hex, secondary_hex = get_system_theme_colors()
    context = {
        "company": company,
        "settings": getattr(company, "settings", None),
        "primary_color_hex": primary_hex,
        "secondary_color_hex": secondary_hex,
    }
    return render(request, "core/company_profile.html", context)


@owner_required
def export_company_pdf(request):
    company = Company.objects.select_related("owner", "owner__staff_profile", "settings").first()
    if not company:
        raise Http404("Company not found")
    if not company.owner:
        owner_user = User.objects.filter(user_type=User.UserType.OWNER).first() or request.user
        company.owner = owner_user
        company.save(update_fields=["owner"])
        company = Company.objects.select_related("owner", "owner__staff_profile", "settings").first()
    primary_hex, secondary_hex = get_system_theme_colors()
    context = {
        "company": company,
        "settings": getattr(company, "settings", None),
        "primary_color_hex": primary_hex,
        "secondary_color_hex": secondary_hex,
    }
    html_string = render_to_string("core/company_export.html", context, request=request)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()
    filename = f"{company.company_name.replace(' ', '_')}_Profile.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@owner_required
def export_company_card_pdf(request):
    company = Company.objects.select_related("owner", "owner__staff_profile", "settings").first()
    if not company:
        raise Http404("Company not found")
    if not company.owner:
        owner_user = User.objects.filter(user_type=User.UserType.OWNER).first() or request.user
        company.owner = owner_user
        company.save(update_fields=["owner"])
        company = Company.objects.select_related("owner", "owner__staff_profile", "settings").first()

    primary_hex, secondary_hex = get_system_theme_colors()
    website_url = "www.flyman.com"
    owner = company.owner
    owner_phone = owner.phone if (owner and owner.phone) else company.phone
    owner_email = owner.email if (owner and owner.email) else company.email
    owner_name = owner.full_name if owner else "Owner"

    qr_data = f"BEGIN:VCARD\nVERSION:3.0\nFN:{owner_name}\nORG:{company.company_name}\nTITLE:Owner & Director\nTEL;TYPE=CELL:{owner_phone}\nEMAIL:{owner_email}\nURL:https://{website_url}\nEND:VCARD"
    
    qr_base64 = ""
    try:
        import qrcode
        import io
        import base64
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=1,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=primary_hex, back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_base64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        pass

    context = {
        "company": company,
        "website": website_url,
        "qr_code_base64": qr_base64,
        "settings": getattr(company, "settings", None),
        "primary_color_hex": primary_hex,
        "secondary_color_hex": secondary_hex,
    }
    html_string = render_to_string("core/company_card_export.html", context, request=request)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()
    filename = f"{company.company_name.replace(' ', '_')}_Business_Card.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@owner_required
def edit_company(request):
    company = Company.objects.select_related("owner", "owner__staff_profile", "settings").first()
    if not company:
        return redirect("dashboard")
    if not company.owner:
        company.owner = request.user
        company.save(update_fields=["owner"])

    if request.method == "POST":
        old_logo = company.logo
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            company = form.save()
            if request.FILES.get("logo") and old_logo and old_logo.name != company.logo.name:
                old_logo.delete(save=False)
            clear_system_settings_cache()
            messages.success(request, "Company profile updated successfully.")
            log_action(user=request.user, action=f"Updated company profile for '{company.company_name}'", action_type="UPDATE", request=request)
            return redirect("company_profile")
    else:
        form = CompanyForm(instance=company)
    return render(request, "core/company_edit.html", {"form": form, "company": company})


@owner_required
def settings(request):
    system_settings = get_object_or_404(SystemSettings)
    if request.method == "POST":
        form = SystemSettingsForm(request.POST, instance=system_settings)
        if form.is_valid():
            form.save()
            clear_system_settings_cache()
            messages.success(request, "System settings updated successfully.")
            log_action(user=request.user, action="Updated system settings", action_type="UPDATE", request=request)
            return redirect("settings")

    else:
        form = SystemSettingsForm(instance=system_settings)
    return render(request, "core/systemsettings.html", {"form": form})


@owner_required
@require_GET
def color_search_api(request):
    query = request.GET.get("q", "").strip()
    colors = Color.objects.all()
    if query:
        colors = colors.filter(name__icontains=query)
    colors = colors.order_by("name")[:30]
    results = [
        {"id": c.id, "name": c.name, "hex_code": c.hex_code, "category": c.category}
        for c in colors
    ]
    return JsonResponse({"results": results})


@owner_required
@require_POST
def color_create_api(request):
    name = (request.POST.get("name") or "").strip()
    hex_code = (request.POST.get("hex_code") or "").strip()
    category = (request.POST.get("category") or "").strip()

    if not name:
        return JsonResponse({"error": "Color name is required."}, status=400)
    if len(name) < 2:
        return JsonResponse({"error": "Color name is too short."}, status=400)
    if not HEX_COLOR_RE.match(hex_code):
        return JsonResponse({"error": "Enter a valid hex color, e.g. #FF5733."}, status=400)
    if Color.objects.filter(name__iexact=name).exists():
        return JsonResponse({"error": "A color with this name already exists."}, status=400)

    color = Color.objects.create(name=name, hex_code=hex_code.upper(), category=category)
    log_action(user=request.user, action=f"Created custom color '{color.name}' ({color.hex_code})", action_type="CREATE", request=request)
    return JsonResponse(
        {"id": color.id, "name": color.name, "hex_code": color.hex_code, "category": color.category}
    )


@owner_required
def action_history_list(request):
    query = request.GET.get("q", "").strip()
    action_type = request.GET.get("type", "").strip()

    histories = ActionHistory.objects.all()

    if query:
        histories = histories.filter(
            Q(action__icontains=query) |
            Q(user_name__icontains=query) |
            Q(details__icontains=query) |
            Q(ip_address__icontains=query)
        )

    if action_type:
        histories = histories.filter(action_type=action_type.upper())

    paginator = Paginator(histories, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    total_count = ActionHistory.objects.count()
    latest_item = ActionHistory.objects.order_by("-created_at").first()

    context = {
        "page_obj": page_obj,
        "query": query,
        "action_type": action_type,
        "total_count": total_count,
        "latest_item": latest_item,
        "action_types": ActionHistory.ACTION_TYPE_CHOICES,
    }
    return render(request, "core/history_list.html", context)


@owner_required
@require_POST
def action_history_delete_item(request, pk):
    item = get_object_or_404(ActionHistory, pk=pk)
    action_desc = item.action
    item.delete()
    messages.success(request, f"History record deleted: '{action_desc}'.")
    return redirect("action_history_list")


@owner_required
@require_POST
def action_history_clear_all(request):
    count = ActionHistory.objects.count()
    ActionHistory.objects.all().delete()
    messages.success(request, f"All history records ({count}) have been cleared.")
    log_action(user=request.user, action="Cleared all action history", action_type="CLEAR", request=request)
    return redirect("action_history_list")


@owner_required
def trash_bin_list(request):
    query = request.GET.get("q", "").strip()
    item_type = request.GET.get("type", "").strip()

    trash_items = TrashItem.objects.all()

    if query:
        trash_items = trash_items.filter(
            Q(title__icontains=query) |
            Q(deleted_by_name__icontains=query)
        )

    if item_type:
        trash_items = trash_items.filter(item_type=item_type.upper())

    paginator = Paginator(trash_items, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    total_count = TrashItem.objects.count()

    context = {
        "page_obj": page_obj,
        "query": query,
        "item_type": item_type,
        "total_count": total_count,
        "item_types": TrashItem.ITEM_TYPE_CHOICES,
    }
    return render(request, "core/trash_bin.html", context)


@owner_required
@require_POST
def trash_bin_restore(request, pk):
    item = get_object_or_404(TrashItem, pk=pk)
    title = item.title
    try:
        restore_trash_item(item, user=request.user, request=request)
        messages.success(request, f"Item successfully recovered: '{title}'.")
    except Exception as e:
        messages.error(request, f"Failed to restore '{title}': {str(e)}")

    return redirect("trash_bin_list")


@owner_required
@require_POST
def trash_bin_delete_permanent(request, pk):
    item = get_object_or_404(TrashItem, pk=pk)
    title = item.title
    item.delete()
    messages.success(request, f"Item permanently deleted from Trash Bin: '{title}'.")
    log_action(user=request.user, action=f"Permanently deleted '{title}' from Trash Bin", action_type="DELETE", request=request)
    return redirect("trash_bin_list")


@owner_required
@require_POST
def trash_bin_clear_all(request):
    count = TrashItem.objects.count()
    TrashItem.objects.all().delete()
    messages.success(request, f"Trash Bin emptied. Permanently deleted {count} items.")
    log_action(user=request.user, action=f"Emptied Trash Bin ({count} items deleted)", action_type="CLEAR", request=request)
    return redirect("trash_bin_list")


