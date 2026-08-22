from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from weasyprint import HTML

from core.models import Company, SystemSettings
from core.utils import log_action
from .decorators import owner_required

from .forms import LoginForm, ProfileDetailsForm, ProfileForm, StaffCreateForm, StaffDetailsForm, StaffEditForm
from .models import StaffProfile, User


class UserLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


@login_required
def profile(request):
    profile_obj, _ = StaffProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "staff_code": f"{'OWNER' if request.user.is_owner else 'STF'}{request.user.pk:05d}"
        }
    )
    if request.method == "POST":
        user_form = ProfileForm(request.POST, instance=request.user, is_owner=request.user.is_owner)
        details_form = ProfileDetailsForm(request.POST, request.FILES, instance=profile_obj)
        if user_form.is_valid() and details_form.is_valid():
            user_form.save()
            details_form.save()
            messages.success(request, "Your profile has been updated.")
            log_action(user=request.user, action="Updated personal profile details", action_type="UPDATE", request=request)
            return redirect("profile")
        else:
            messages.error(request, "Please correct the errors below to update your profile.")
    else:
        user_form = ProfileForm(instance=request.user, is_owner=request.user.is_owner)
        details_form = ProfileDetailsForm(instance=profile_obj)
    context = {"profile_obj": profile_obj, "user_form": user_form, "details_form": details_form}
    return render(request, "accounts/profile.html", context)


@owner_required
def staff_list(request):
    query = request.GET.get("q", "").strip()
    staff = StaffProfile.objects.select_related("user").filter(user__user_type=User.UserType.STAFF)
    if query:
        staff = staff.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(staff_code__icontains=query) |
            Q(user__phone__icontains=query)
        )
    page_obj = Paginator(staff.order_by("staff_code"), 12).get_page(request.GET.get("page"))

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("ajax") == "1":
        html_content = render_to_string("accounts/_staff_grid_fragment.html", {"page_obj": page_obj, "query": query, "request": request})
        return JsonResponse({"html": html_content, "count": page_obj.paginator.count})

    return render(request, "accounts/staff_list.html", {"page_obj": page_obj, "query": query})


@owner_required
def staff_create(request):
    if request.method == "POST":
        form = StaffCreateForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.user_type = User.UserType.STAFF
                user.is_active = True
                pwd = form.cleaned_data["password"]
                user.set_password(pwd)
                user.raw_password = pwd
                user.save()
                profile_obj = user.staff_profile
                profile_obj.joining_date = form.cleaned_data["joining_date"]
                profile_obj.salary = form.cleaned_data["salary"]
                profile_obj.commission_enabled = form.cleaned_data["commission_enabled"]
                profile_obj.profile_photo = form.cleaned_data.get("profile_photo")
                profile_obj.notes = form.cleaned_data["notes"]
                profile_obj.save()
            messages.success(request, f"{user.full_name} was added to staff.")
            log_action(user=request.user, action=f"Created new staff member '{user.full_name}' ({profile_obj.staff_code})", action_type="CREATE", request=request)
            return redirect("staff_list")
    else:
        form = StaffCreateForm()
    return render(request, "accounts/staff_create.html", {"form": form})


@owner_required
def staff_profile(request, pk):
    profile_obj = get_object_or_404(StaffProfile.objects.select_related("user"), pk=pk, user__user_type=User.UserType.STAFF)
    return render(request, "accounts/staff_profile.html", {"profile_obj": profile_obj})


@owner_required
def staff_edit(request, pk):
    profile_obj = get_object_or_404(StaffProfile.objects.select_related("user"), pk=pk, user__user_type=User.UserType.STAFF)
    if request.method == "POST":
        user_form = StaffEditForm(request.POST, instance=profile_obj.user)
        details_form = ProfileDetailsForm(request.POST, request.FILES, instance=profile_obj)
        if user_form.is_valid() and details_form.is_valid():
            user_form.save()
            details_form.save()
            messages.success(request, "Staff member updated.")
            log_action(user=request.user, action=f"Updated staff member details for '{profile_obj.user.full_name}'", action_type="UPDATE", request=request)
            return redirect("staff_profile", pk=profile_obj.pk)
    else:
        user_form = StaffEditForm(instance=profile_obj.user)
        details_form = StaffDetailsForm(instance=profile_obj)
    return render(request, "accounts/staff_edit.html", {"profile_obj": profile_obj, "user_form": user_form, "details_form": details_form})


from core.trash_utils import move_staff_to_trash


@owner_required
def staff_delete(request, pk):
    profile_obj = get_object_or_404(StaffProfile.objects.select_related("user"), pk=pk, user__user_type=User.UserType.STAFF)
    if request.method == "POST":
        name = profile_obj.user.full_name
        move_staff_to_trash(profile_obj, user=request.user, request=request)
        messages.success(request, f"Staff member '{name}' was moved to Trash Bin.")
        return redirect("staff_list")
    return render(request, "accounts/staff_delete.html", {"profile_obj": profile_obj})



@owner_required
@require_POST
def staff_activate(request, pk):
    profile_obj = get_object_or_404(StaffProfile, pk=pk, user__user_type=User.UserType.STAFF)
    profile_obj.user.is_active = True
    profile_obj.user.save(update_fields=["is_active"])
    messages.success(request, "Staff member activated.")
    log_action(user=request.user, action=f"Activated staff account for '{profile_obj.user.full_name}'", action_type="UPDATE", request=request)
    return redirect("staff_list")


@owner_required
@require_POST
def staff_deactivate(request, pk):
    profile_obj = get_object_or_404(StaffProfile, pk=pk, user__user_type=User.UserType.STAFF)
    profile_obj.user.is_active = False
    profile_obj.user.save(update_fields=["is_active"])
    messages.success(request, "Staff member deactivated.")
    log_action(user=request.user, action=f"Deactivated staff account for '{profile_obj.user.full_name}'", action_type="UPDATE", request=request)
    return redirect("staff_list")



@owner_required
def staff_export(request):
    company = Company.objects.first()
    settings_obj = SystemSettings.objects.select_related("primary_color", "secondary_color").first()
    primary_hex = "#7c5cff"
    secondary_hex = "#00d4c8"
    if settings_obj:
        if settings_obj.primary_color and settings_obj.primary_color.hex_code:
            primary_hex = settings_obj.primary_color.hex_code
        if settings_obj.secondary_color and settings_obj.secondary_color.hex_code:
            secondary_hex = settings_obj.secondary_color.hex_code

    staff_qs = StaffProfile.objects.select_related("user").filter(user__user_type=User.UserType.STAFF).order_by("staff_code")
    staff_list_all = list(staff_qs)
    staff_count = len(staff_list_all)
    active_count = sum(1 for s in staff_list_all if s.user.is_active)
    inactive_count = staff_count - active_count

    staff_pairs = [staff_list_all[i:i + 2] for i in range(0, staff_count, 2)]

    context = {
        "company": company,
        "staff_pairs": staff_pairs,
        "staff_count": staff_count,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "primary_color_hex": primary_hex,
        "secondary_color_hex": secondary_hex,
        "request": request,
    }
    html_string = render_to_string("accounts/staff_export_pdf.html", context, request=request)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()

    filename = "flymen-staff-directory-report.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
