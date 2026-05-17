import requests
from django.conf import settings


def get_exchange_rates():
    url = 'https://open.er-api.com/v6/latest/BYN'
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        return {
            'ok': False,
            'error': f'Не удалось получить курсы валют: {error}',
        }

    rates = data.get('rates', {})
    return {
        'ok': True,
        'base': data.get('base_code', 'BYN'),
        'usd': rates.get('USD'),
        'eur': rates.get('EUR'),
        'date': data.get('time_last_update_utc'),
    }


def get_test_drive_weather(city='Minsk'):
    if not settings.OPENWEATHER_API_KEY:
        return {
            'ok': False,
            'error': 'Добавьте OPENWEATHER_API_KEY в переменные окружения для работы OpenWeatherMap.',
        }

    url = 'https://api.openweathermap.org/data/2.5/weather'
    try:
        response = requests.get(
            url,
            params={
                'q': city,
                'units': 'metric',
                'lang': 'ru',
                'appid': settings.OPENWEATHER_API_KEY,
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        return {
            'ok': False,
            'error': f'Не удалось получить погоду OpenWeatherMap: {error}',
        }

    return {
        'ok': True,
        'city': data.get('name', city),
        'country': data.get('sys', {}).get('country', ''),
        'temperature': data.get('main', {}).get('temp'),
        'feels_like': data.get('main', {}).get('feels_like'),
        'pressure': data.get('main', {}).get('pressure'),
        'humidity': data.get('main', {}).get('humidity'),
        'wind_speed': data.get('wind', {}).get('speed'),
        'description': data.get('weather', [{}])[0].get('description'),
        'icon': data.get('weather', [{}])[0].get('icon'),
    }
