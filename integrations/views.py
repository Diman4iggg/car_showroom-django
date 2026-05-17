from django.shortcuts import render

from .services import get_test_drive_weather


def api_dashboard(request):
    city = request.GET.get('city', 'Minsk').strip() or 'Minsk'
    context = {
        'city': city,
        'weather': get_test_drive_weather(city),
    }
    return render(request, 'integrations/api_dashboard.html', context)
