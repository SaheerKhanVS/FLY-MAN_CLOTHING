from .models import ActionHistory


def get_client_ip(request):
    """
    Extract client IP address from HTTP request headers or remote address.
    """
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_action(user=None, action="", action_type="SYSTEM", details=None, request=None):
    """
    Utility function to log user/system actions into ActionHistory.
    Trims oldest 10 records automatically if total history exceeds 100.
    """
    actual_user = None
    if user and getattr(user, "is_authenticated", False):
        actual_user = user
    elif request and getattr(request, "user", None) and request.user.is_authenticated:
        actual_user = request.user

    user_name = "System"
    if actual_user:
        user_name = getattr(actual_user, "full_name", None) or actual_user.username

    ip_address = get_client_ip(request)

    record = ActionHistory.objects.create(
        user=actual_user,
        user_name=user_name,
        action=action,
        action_type=action_type,
        details=details or "",
        ip_address=ip_address,
    )

    # Perform auto trim if history count > 100
    ActionHistory.trim_old_records()

    return record
