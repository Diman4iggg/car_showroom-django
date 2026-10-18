from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError

from analytics.views import build_linear_forecast
from sales.forms import PaymentForm
from sales.models import phone_validator, validate_adult
from showroom.views import add_currency_prices


pytestmark = pytest.mark.unit


@pytest.mark.parametrize('birthday,valid', [
    (date(2008, 10, 15), True), (date(2008, 10, 16), True),
    (date(2008, 10, 17), False), (date(2009, 1, 1), False),
    (date(2027, 1, 1), False),
], ids=['adult-yesterday', 'adult-today', 'adult-tomorrow', 'minor', 'future'])
def test_age_validation_uses_full_birth_date(birthday, valid):
    # Arrange: freeze the dependency instead of relying on the execution date.
    with patch('sales.models.date') as clock:
        clock.today.return_value = date(2026, 10, 16)
        # Act / Assert
        if valid:
            assert validate_adult(birthday) is None
        else:
            with pytest.raises(ValidationError):
                validate_adult(birthday)


@pytest.mark.parametrize('phone,valid', [
    ('+375 (29) 123-45-67', True), ('+375 (25) 123-45-67', True),
    ('+375 (33) 123-45-67', True), ('+375 (44) 123-45-67', True),
    ('+375 (17) 123-45-67', False), ('80291234567', False),
    ('+375 (29) 123-45-6', False), ('', False),
])
def test_phone_validation_accepts_only_supported_format(phone, valid):
    # Arrange: parameter supplies valid and invalid operator/length combinations.
    # Act / Assert
    if valid:
        assert phone_validator(phone) is None
    else:
        with pytest.raises(ValidationError):
            phone_validator(phone)


@pytest.mark.parametrize('field,value', [
    ('card_number', '123'), ('card_number', 'a' * 16),
    ('cvv', '12'), ('cvv', '1234'), ('agreement', ''),
    ('expiry_month', '13'), ('cardholder_name', ''),
])
def test_payment_form_rejects_invalid_field(payment_data, field, value):
    # Arrange
    payment_data[field] = value
    form = PaymentForm(data=payment_data)
    # Act
    valid = form.is_valid()
    # Assert
    assert not valid
    assert field in form.errors


@pytest.mark.parametrize('month,valid', [('09', False), ('10', True), ('11', True)])
def test_payment_expiry_accepts_current_month_but_rejects_previous(payment_data, month, valid):
    # Arrange
    payment_data.update(expiry_month=month, expiry_year='2026')
    with patch('sales.forms.date') as clock:
        clock.today.return_value = date(2026, 10, 16)
        form = PaymentForm(payment_data)
        form.fields['expiry_year'].choices = [('2026', '2026')]
        # Act
        result = form.is_valid()
    # Assert
    assert result is valid
    if not valid:
        assert '__all__' in form.errors


@pytest.mark.parametrize('values,expected', [([], None), ([100], None),
    ([100, 200], 300), ([200, 100], 0), ([100, 100], 100)])
def test_forecast_handles_insufficient_flat_and_falling_sales(values, expected):
    # Arrange
    rows = [{'paid_at__year': 2026, 'paid_at__month': i, 'total': Decimal(value)}
            for i, value in enumerate(values, 1)]
    # Act
    forecast = build_linear_forecast(rows)
    # Assert
    assert forecast['forecast'] == expected
    assert len(forecast['points']) == len(values)


@pytest.mark.parametrize('rates', [{'ok': False, 'error': 'offline'},
    {'ok': True, 'usd': 0, 'eur': 1}, {'ok': True, 'usd': 1, 'eur': -1}])
def test_currency_conversion_does_not_add_prices_for_unusable_rates(rates):
    # Arrange: lightweight object replaces the database model.
    car = SimpleNamespace(price=Decimal('100.00'))
    # Act
    result = add_currency_prices([car], rates)
    # Assert
    assert result == [car]
    assert not hasattr(car, 'price_usd')


def test_currency_conversion_rounds_to_cents():
    # Arrange
    car = Mock(price=Decimal('10.01'))
    # Act
    add_currency_prices([car], {'ok': True, 'usd': 0.333, 'eur': 0.25})
    # Assert
    assert car.price_usd == Decimal('3.33')
    assert car.price_eur == Decimal('2.50')
