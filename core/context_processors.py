from django.core.cache import cache
from .models import SystemSettings

DEFAULT_PRIMARY = "#7c5cff"
DEFAULT_SECONDARY = "#00d4c8"
CACHE_KEY = "flymen_system_settings_context"
CACHE_TIMEOUT = 600  # 10 minutes


def clear_system_settings_cache():
    """
    Invalidates the cached system settings context.
    Call this whenever SystemSettings or Company is updated.
    """
    cache.delete(CACHE_KEY)
    cache.delete("flymen_theme_colors")


def system_settings(request):
    """
    Makes the active SystemSettings (and its primary/secondary colors, font & object sizes)
    available in every template. Cached in memory to avoid remote database queries on every page load.
    """
    cached_context = cache.get(CACHE_KEY)
    if cached_context is not None:
        return cached_context

    settings_obj = (
        SystemSettings.objects.select_related(
            "primary_color", "secondary_color", "company", "currency"
        ).first()
    )

    primary_hex = DEFAULT_PRIMARY
    secondary_hex = DEFAULT_SECONDARY
    font_size = "small"
    object_size = "small"

    if settings_obj:
        if settings_obj.primary_color and settings_obj.primary_color.hex_code:
            primary_hex = settings_obj.primary_color.hex_code
        if settings_obj.secondary_color and settings_obj.secondary_color.hex_code:
            secondary_hex = settings_obj.secondary_color.hex_code
        font_size = settings_obj.font_size or "small"
        object_size = settings_obj.object_size or "small"

    context = {
        "system_settings": settings_obj,
        "primary_color_hex": primary_hex,
        "secondary_color_hex": secondary_hex,
        "system_font_size": font_size,
        "system_object_size": object_size,
    }

    cache.set(CACHE_KEY, context, CACHE_TIMEOUT)
    return context
