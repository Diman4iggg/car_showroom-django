import calendar
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.utils import timezone


def get_user_timezone(request):
    timezone_name = settings.TIME_ZONE
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.timezone:
            timezone_name = profile.timezone

    try:
        return timezone_name, ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return settings.TIME_ZONE, ZoneInfo(settings.TIME_ZONE)


def time_context(request):
    timezone_name, user_timezone = get_user_timezone(request)
    now_utc = timezone.now()
    now_local = timezone.localtime(now_utc, user_timezone)

    return {
        'user_timezone': timezone_name,
        'current_date': now_local.strftime('%d/%m/%Y'),
        'current_time': now_local.strftime('%H:%M:%S'),
        'current_date_utc': timezone.localtime(now_utc, ZoneInfo('UTC')).strftime('%d/%m/%Y'),
        'current_time_utc': timezone.localtime(now_utc, ZoneInfo('UTC')).strftime('%H:%M:%S'),
        'text_calendar': calendar.TextCalendar(calendar.MONDAY).formatmonth(now_local.year, now_local.month),
    }
