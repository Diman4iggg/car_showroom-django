from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.urls import reverse

from accounts.models import UserProfile
from core.models import CompanyHistoryEvent, CompanyInfo
from sales.models import Order, OrderItem, Sale


pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_order_total_uses_saved_unit_price_not_current_catalog_price(customer, car):
    # Arrange
    order = Order.objects.create(client=customer[1])
    OrderItem.objects.create(order=order, car=car, quantity=2, unit_price=Decimal('100.00'))
    car.price = Decimal('999.00')
    car.save()
    # Act
    persisted = Order.objects.get(pk=order.pk)
    # Assert
    assert persisted.total_amount == Decimal('200.00')


def test_database_rejects_second_sale_for_same_order(customer):
    from django.utils import timezone

    # Arrange
    order = Order.objects.create(client=customer[1])
    Sale.objects.create(order=order, paid_at=timezone.now(), total_amount=100)
    # Act / Assert: savepoint keeps the test transaction usable after the error.
    with pytest.raises(IntegrityError), transaction.atomic():
        Sale.objects.create(order=order, paid_at=timezone.now(), total_amount=100)
    assert Sale.objects.filter(order=order).count() == 1


def test_company_history_year_is_unique_within_company():
    # Arrange
    company = CompanyInfo.objects.create(title='Company', text='History')
    CompanyHistoryEvent.objects.create(company=company, year=2026, description='Opened')
    # Act / Assert
    with pytest.raises(IntegrityError), transaction.atomic():
        CompanyHistoryEvent.objects.create(company=company, year=2026, description='Duplicate')
    assert company.history_events.count() == 1


def test_user_creation_signal_creates_exactly_one_profile(customer):
    # Arrange
    user = customer[0]
    # Act
    user.first_name = 'Changed'
    user.save()
    # Assert
    assert UserProfile.objects.filter(user=user).count() == 1


def test_payment_rolls_back_order_items_sale_and_stock_on_persistence_failure(
    client, customer, car, payment_data, monkeypatch,
):
    # Arrange: simulate a failure after order creation, inside transaction.atomic.
    client.force_login(customer[0])
    client.post(reverse('sales:cart_add', args=[car.pk]), {'quantity': 2})

    def reject_sale(*args, **kwargs):
        raise ValueError('Simulated persistence failure')

    monkeypatch.setattr('sales.views.Sale.objects.create', reject_sale)
    # Act
    response = client.post(reverse('sales:payment'), payment_data)
    # Assert
    car.refresh_from_db()
    assert response.status_code == 302
    assert not Order.objects.exists()
    assert not OrderItem.objects.exists()
    assert not Sale.objects.exists()
    assert car.stock == 3
    assert client.session['cart'][str(car.pk)] == 2


def test_demo_sales_command_is_idempotent():
    # Arrange
    output = StringIO()
    # Act
    call_command('seed_demo_sales', stdout=output)
    call_command('seed_demo_sales', stdout=output)
    # Assert
    assert Order.objects.count() == 2
    assert OrderItem.objects.count() == 2
    assert Sale.objects.count() == 2
    assert 'Created demo sales: 2' in output.getvalue()
    assert 'Created demo sales: 0' in output.getvalue()
