from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from .services import get_exchange_rates, get_test_drive_weather


class IntegrationServiceTests(TestCase):
    @patch('integrations.services.requests.get')
    def test_exchange_rates_parse_usd_and_eur(self, mocked_get):
        response = Mock()
        response.json.return_value = {
            'base_code': 'BYN',
            'rates': {'USD': 0.3, 'EUR': 0.25},
            'time_last_update_utc': 'Mon, 18 May 2026 00:00:00 +0000',
        }
        response.raise_for_status.return_value = None
        mocked_get.return_value = response

        result = get_exchange_rates()

        self.assertTrue(result['ok'])
        self.assertEqual(result['usd'], 0.3)
        self.assertEqual(result['eur'], 0.25)

    @override_settings(OPENWEATHER_API_KEY='')
    def test_weather_requires_api_key(self):
        result = get_test_drive_weather('Minsk')

        self.assertFalse(result['ok'])
        self.assertIn('OPENWEATHER_API_KEY', result['error'])

    @override_settings(OPENWEATHER_API_KEY='test-key')
    @patch('integrations.services.requests.get')
    def test_weather_parses_openweathermap_response(self, mocked_get):
        response = Mock()
        response.json.return_value = {
            'name': 'Minsk',
            'sys': {'country': 'BY'},
            'main': {
                'temp': 20,
                'feels_like': 19,
                'pressure': 1015,
                'humidity': 60,
            },
            'wind': {'speed': 4},
            'weather': [{'description': 'clear sky', 'icon': '01d'}],
        }
        response.raise_for_status.return_value = None
        mocked_get.return_value = response

        result = get_test_drive_weather('Minsk')

        self.assertTrue(result['ok'])
        self.assertEqual(result['city'], 'Minsk')
        self.assertEqual(result['temperature'], 20)


class IntegrationViewTests(TestCase):
    @patch('integrations.views.get_test_drive_weather')
    def test_api_dashboard_passes_city_to_weather_service(self, mocked_weather):
        mocked_weather.return_value = {'ok': True, 'city': 'Brest'}

        response = self.client.get(reverse('integrations:api_dashboard'), {'city': 'Brest'})

        self.assertEqual(response.status_code, 200)
        mocked_weather.assert_called_once_with('Brest')
        self.assertEqual(response.context['city'], 'Brest')
