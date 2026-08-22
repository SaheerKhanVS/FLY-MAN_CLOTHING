from django import template

register = template.Library()


@register.filter(name='optimized_url')
def optimized_url(image_field_or_url, params="f_auto,q_auto,w_400"):
    """
    Transforms Cloudinary image URLs to include automatic format/quality compression and width scaling.
    Usage: {{ profile.profile_photo|optimized_url:'f_auto,q_auto,w_300' }}
    """
    if not image_field_or_url:
        return ""

    if hasattr(image_field_or_url, 'url'):
        url = image_field_or_url.url
    else:
        url = str(image_field_or_url)

    if not url:
        return ""

    if "res.cloudinary.com" in url and "/upload/" in url:
        # Insert transformation flags after /upload/
        parts = url.split("/upload/")
        return f"{parts[0]}/upload/{params}/{parts[1]}"

    return url
