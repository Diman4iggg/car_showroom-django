import json
from urllib.parse import parse_qs, urlparse

import pytest
import requests
from django.urls import reverse

from integrations.services import get_test_drive_weather


pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def install_http_stub(monkeypatch, *, payload=None, status=200, error=None):
    calls = []

    def send(session, prepared_request, **kwargs):
        calls.append((prepared_request, kwargs))
        if error is not None:
            raise error
        response = requests.Response()
        response.status_code = status
        response.url = prepared_request.url
        response.request = prepared_request
        response.headers['Content-Type'] = 'application/json'
        response._content = json.dumps(payload or {}).encode('utf-8')
        return response

    monkeypatch.setattr(requests.Session, 'send', send)
    return calls


def test_catalog_uses_real_adapter_and_http_response_to_convert_db_prices(client, car, monkeypatch):
    # Arrange: only the HTTP transport is replaced; ORM, view and adapter are real.
    calls = install_http_stub(monkeypatch, payload={
        'base_code': 'BYN', 'rates': {'USD': 0.3, 'EUR': 0.25},
    })
    # Act
    response = client.get(reverse('showroom:index'))
    # Assert
    assert response.status_code == 200
    assert response.context['cars'][0].price_usd == car.price * 3 / 10
    assert len(calls) == 1
    request, options = calls[0]
    assert request.method == 'GET'
    assert request.url == 'https://open.er-api.com/v6/latest/BYN'
    assert options['timeout'] == 5


@pytest.mark.parametrize('failure', ['timeout', 'connection', 'http-503'])
def test_catalog_stays_available_when_currency_http_request_fails(client, car, monkeypatch, failure):
    # Arrange
    errors = {'timeout': requests.Timeout('timeout'),
              'connection': requests.ConnectionError('offline')}
    install_http_stub(monkeypatch, status=503, error=errors.get(failure))
    # Act
    response = client.get(reverse('showroom:index'))
    # Assert
    assert response.status_code == 200
    assert not response.context['exchange_rates']['ok']
    assert response.context['cars'][0].price == car.price


def test_weather_page_sends_city_units_language_and_key_over_http(client, monkeypatch, settings):
    # Arrange
    settings.OPENWEATHER_API_KEY = 'test-key'
    calls = install_http_stub(monkeypatch, payload={
        'name': 'Brest', 'main': {'temp': 18}, 'weather': [{'description': 'clear'}],
    })
    # Act
    response = client.get(reverse('integrations:api_dashboard'), {'city': 'Brest'})
    # Assert
    assert response.status_code == 200
    assert response.context['weather']['temperature'] == 18
    request, options = calls[0]
    query = parse_qs(urlparse(request.url).query)
    assert query == {'q': ['Brest'], 'units': ['metric'], 'lang': ['ru'], 'appid': ['test-key']}
    assert options['timeout'] == 5


@pytest.mark.parametrize('status', [401, 404, 429, 500])
def test_weather_adapter_returns_controlled_error_for_http_failure(monkeypatch, settings, status):
    # Arrange
    settings.OPENWEATHER_API_KEY = 'test-key'
    install_http_stub(monkeypatch, status=status)
    # Act
    result = get_test_drive_weather('Minsk')
    # Assert
    assert result['ok'] is False
    assert str(status) in result['error']


def test_missing_weather_key_does_not_make_http_request(settings):
    # Arrange: autouse fixture rejects any outgoing HTTP request.
    settings.OPENWEATHER_API_KEY = ''
    # Act
    result = get_test_drive_weather()
    # Assert
    assert not result['ok']
    assert 'OPENWEATHER_API_KEY' in result['error']
