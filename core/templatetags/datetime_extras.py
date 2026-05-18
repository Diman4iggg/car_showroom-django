from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django import template
from django.conf import settings
from django.utils import timezone


register = template.Library()


@register.filter
def local_and_utc(value, timezone_name=None):
    if not value:
        return 'не указана'

    try:
        user_timezone = ZoneInfo(timezone_name or settings.TIME_ZONE)
    except ZoneInfoNotFoundError:
        user_timezone = ZoneInfo(settings.TIME_ZONE)

    local_value = timezone.localtime(value, user_timezone)
    utc_value = timezone.localtime(value, ZoneInfo('UTC'))

    return (
        f'{user_timezone.key}: {local_value.strftime("%d/%m/%Y %H:%M")} | '
        f'UTC: {utc_value.strftime("%d/%m/%Y %H:%M")}'
    )
