import pytest
from django.urls import reverse

from sales.models import Order


pytestmark = [pytest.mark.known_defect, pytest.mark.django_db]


@pytest.mark.xfail(strict=True, reason='ISSUE-002: quick purchase accepts GET')
def test_get_purchase_must_not_create_order(client, customer, car):
    # Arrange
    client.force_login(customer[0])
    # Act
    response = client.get(reverse('showroom:buy_car', args=[car.pk]))
    # Assert
    assert not Order.objects.exists()
    assert response.status_code == 405


@pytest.mark.xfail(strict=True, reason='ISSUE-003: invalid price causes HTTP 500')
def test_invalid_price_must_not_crash_catalog(client):
    # Arrange
    client.raise_request_exception = False
    # Act
    response = client.get(reverse('showroom:index'), {'min_price': 'abc'})
    # Assert
    assert response.status_code == 200


@pytest.mark.xfail(strict=True, reason='ISSUE-005: zero-stock car remains visible')
def test_zero_stock_car_must_be_hidden(client, car, monkeypatch):
    # Arrange
    car.stock = 0
    car.save()
    monkeypatch.setattr('showroom.views.get_exchange_rates', lambda: {'ok': False, 'error': 'offline'})
    # Act
    response = client.get(reverse('showroom:index'))
    # Assert
    assert car.pk not in [item.pk for item in response.context['cars']]


@pytest.mark.xfail(strict=True, reason='ISSUE-006: staff cannot take an online-paid order')
def test_staff_can_assign_and_deliver_online_paid_order(
    client, customer, car, payment_data, employee_factory,
):
    # Arrange: actual checkout creates a paid order with no assigned employee.
    user, employee = employee_factory()
    client.force_login(customer[0])
    client.post(reverse('sales:cart_add', args=[car.pk]), {'quantity': 1})
    client.post(reverse('sales:payment'), payment_data)
    order = Order.objects.get()
    # Act
    client.force_login(user)
    client.post(reverse('accounts:update_order_status', args=[order.pk, 'take']))
    client.post(reverse('accounts:update_order_status', args=[order.pk, 'deliver']))
    # Assert
    order.refresh_from_db()
    assert order.employee == employee
    assert order.status == 'delivered'
