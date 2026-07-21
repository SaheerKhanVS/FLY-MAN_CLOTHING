import re
from cloudinary import models
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render,get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from .models import Company
from weasyprint import HTML
from django.template.loader import render_to_string
from .forms import CompanyForm, SystemSettingsForm
from .models import SystemSettings, Color

HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")



def dashboard(request):
    return render(request, "core/dashbord.html")

def company_profile(request):
    company = Company.objects.first()
    context = {"company": company,"settings": company.settings if company else None}
    return render(request,"core/company_profile.html",context)

def export_company_pdf(request):
    company = Company.objects.first()
    if not company: raise Http404("Company not found")
    context = {"company": company,"settings": company.settings}
    html_string = render_to_string("core/company_export.html",context)
    pdf = HTML(string=html_string,base_url=request.build_absolute_uri("/")).write_pdf()
    filename = f"{company.company_name}.pdf"
    response = HttpResponse( pdf,content_type="application/pdf")
    response["Content-Disposition"] = (f'attachment; filename="{filename}"')
    return response

def edit_company(request):
    company = Company.objects.first()
    if not company:return redirect("dashboard")
    if request.method == "POST":
        old_logo = company.logo
        form = CompanyForm(request.POST,request.FILES,instance=company)
        if form.is_valid():
            company = form.save()
            if (request.FILES.get("logo")and old_logo
                and old_logo.name != company.logo.name):
                old_logo.delete(save=False)
            return redirect("company_profile")
    else:form = CompanyForm(instance=company)
    return render( request,"core/company_edit.html", {"form": form,"company": company,})


def settings(request):
    system_settings = get_object_or_404(SystemSettings)
    if request.method == "POST":
        form = SystemSettingsForm(request.POST,instance=system_settings)
        if form.is_valid():
            form.save()
            return redirect("settings")
    else:form = SystemSettingsForm(instance=system_settings)
    return render(request,"core/systemsettings.html",{ "form": form, }, )


@require_GET
def color_search_api(request):
    """
    Lightweight JSON search endpoint used by Tom Select's `load` option
    on the color pickers. Only ever returns a small page of results so
    the settings page never has to render/ship the full color table.
    """
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


@require_POST
def color_create_api(request):
    """
    Creates a new Color from the "+ New Color" modal on the settings page
    and returns it as JSON so the front end can select it immediately
    without a full page reload.
    """
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