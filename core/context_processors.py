from .models import SystemSettings

# Sensible fallbacks so the UI still looks right before any SystemSettings
# row / colors exist (fresh install, empty DB, etc).
DEFAULT_PRIMARY = "#7c5cff"
DEFAULT_SECONDARY = "#00d4c8"


def system_settings(request):
    """
    Makes the active SystemSettings (and its primary/secondary colors)
    available in every template as `system_settings`, `primary_color_hex`
    and `secondary_color_hex`. Used by base.html to theme the whole app.
    """
    settings_obj = (
        SystemSettings.objects.select_related(
            "primary_color", "secondary_color", "company", "currency"
        ).first()
    )

    primary_hex = DEFAULT_PRIMARY
    secondary_hex = DEFAULT_SECONDARY

    if settings_obj:
        if settings_obj.primary_color and settings_obj.primary_color.hex_code:
            primary_hex = settings_obj.primary_color.hex_code
        if settings_obj.secondary_color and settings_obj.secondary_color.hex_code:
            secondary_hex = settings_obj.secondary_color.hex_code

    return {
        "system_settings": settings_obj,
        "primary_color_hex": primary_hex,
        "secondary_color_hex": secondary_hex,
    }
