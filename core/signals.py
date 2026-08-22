from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .utils import log_action


@receiver(user_logged_in)
def handle_user_logged_in(sender, request, user, **kwargs):
    user_display = getattr(user, "full_name", user.username)
    log_action(
        user=user,
        action=f"User '{user_display}' logged into the system",
        action_type="LOGIN",
        request=request
    )


@receiver(user_logged_out)
def handle_user_logged_out(sender, request, user, **kwargs):
    if user and getattr(user, "is_authenticated", False):
        user_display = getattr(user, "full_name", user.username)
        log_action(
            user=user,
            action=f"User '{user_display}' logged out",
            action_type="LOGOUT",
            request=request
        )
