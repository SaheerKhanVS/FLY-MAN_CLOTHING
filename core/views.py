from cloudinary import models
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from .models import Company
from weasyprint import HTML
from django.template.loader import render_to_string
from .forms import CompanyForm



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