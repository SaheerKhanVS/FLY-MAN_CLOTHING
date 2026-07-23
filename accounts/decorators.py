from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def owner_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.user.is_owner:
            return view_func(request, *args, **kwargs)
        messages.error(request, "You do not have permission to access that page.")
        return redirect("dashboard")
    return wrapped
