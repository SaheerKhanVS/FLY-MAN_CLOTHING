import re
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from accounts.decorators import owner_required
from accounts.models import User
from weasyprint import HTML
from django.template.loader import render_to_string
from .forms import CompanyForm, SystemSettingsForm
from .models import Company, SystemSettings, Color

HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")


@login_required
def dashboard(request):
    return render(request, "core/dashbord.html", {"current_profile": request.user.staff_profile})


@owner_required
def company_profile(request):
    company = Company.objects.first()
    if company and not company.owner:
        owner_user = User.objects.filter(user_type=User.UserType.OWNER).first() or request.user
        company.owner = owner_user
        company.save(update_fields=["owner"])
    context = {"company": company, "settings": company.settings if company else None}
    return render(request, "core/company_profile.html", context)


@owner_required
def export_company_pdf(request):
    company = Company.objects.first()
    if not company:
        raise Http404("Company not found")
    if not company.owner:
        company.owner = request.user
        company.save(update_fields=["owner"])
    context = {"company": company, "settings": company.settings}
    html_string = render_to_string("core/company_export.html", context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()
    filename = f"{company.company_name.replace(' ', '_')}_Profile.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@owner_required
def edit_company(request):
    company = Company.objects.first()
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
    return JsonResponse(
        {"id": color.id, "name": color.name, "hex_code": color.hex_code, "category": color.category}
    )
