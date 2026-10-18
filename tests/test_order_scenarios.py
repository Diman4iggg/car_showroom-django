import pytest
from django.test import Client as HttpClient
from django.urls import reverse

from sales.models import Order, OrderItem, Sale


pytestmark = [pytest.mark.scenario, pytest.mark.django_db]


def change_status(client, order, action):
    return client.post(reverse('accounts:update_order_status', args=[order.pk, action]))


def test_purchase_then_take_confirm_pay_deliver_reaches_terminal_state(
    client, customer, car, employee_factory,
):
    # Arrange
    staff_user, staff = employee_factory()
    client.force_login(customer[0])
    # Act / Assert: each request starts from the persisted state left by the preceding step.
    response = client.post(reverse('showroom:buy_car', args=[car.pk]))
    assert response.status_code == 302
    order = Order.objects.get(client=customer[1])
    assert order.status == 'new'
    car.refresh_from_db()
    assert car.stock == 2

    client.force_login(staff_user)
    assert change_status(client, order, 'take').status_code == 302
    order.refresh_from_db()
    assert order.employee == staff
    for action, expected in [('confirm', 'confirmed'), ('pay', 'paid'), ('deliver', 'delivered')]:
        assert change_status(client, order, action).status_code == 302
        order.refresh_from_db()
        assert order.status == expected
    assert Sale.objects.filter(order=order).count() == 1
    assert order.delivery_at is not None
    assert order.delivery_date is not None


def test_cart_payment_creates_paid_order_that_employee_cannot_take(
    client, customer, car, employee_factory, payment_data,
):
    # Arrange
    staff_user, _ = employee_factory()
    client.force_login(customer[0])
    # Act
    client.post(reverse('sales:cart_add', args=[car.pk]), {'quantity': 2})
    response = client.post(reverse('sales:payment'), payment_data)
    order = Order.objects.get(client=customer[1])
    staff_browser = HttpClient()
    staff_browser.force_login(staff_user)
    change_status(staff_browser, order, 'take')
    # Assert: captures the current assignment gap of the online-paid workflow.
    order.refresh_from_db()
    assert response.status_code == 302
    assert order.status == 'paid'
    assert order.employee_id is None
    assert Sale.objects.get(order=order).total_amount == 200
    assert client.session['cart'] == {}


@pytest.mark.parametrize('actor', ['client', 'employee'])
def test_cancel_new_order_restores_stock_only_once(client, customer, car, employee_factory, actor):
    # Arrange: create the reservation through the real purchase endpoint.
    staff_user, _ = employee_factory()
    client.force_login(customer[0])
    client.post(reverse('showroom:buy_car', args=[car.pk]))
    order = Order.objects.get()
    if actor == 'employee':
        client.force_login(staff_user)
        change_status(client, order, 'take')
        cancel = lambda: change_status(client, order, 'cancel')
    else:
        cancel = lambda: client.post(reverse('accounts:cancel_order', args=[order.pk]))
    # Act
    cancel()
    cancel()
    # Assert
    order.refresh_from_db()
    car.refresh_from_db()
    assert order.status == 'cancelled'
    assert car.stock == 3
    assert not Sale.objects.exists()


@pytest.mark.parametrize('initial,action', [
    ('new', 'pay'), ('new', 'deliver'), ('confirmed', 'deliver'),
    ('paid', 'confirm'), ('paid', 'cancel'), ('delivered', 'cancel'),
    ('cancelled', 'pay'), ('cancelled', 'confirm'),
])
def test_invalid_transition_keeps_order_and_stock_unchanged(
    client, customer, car, employee_factory, initial, action,
):
    # Arrange
    user, employee = employee_factory()
    order = Order.objects.create(client=customer[1], employee=employee, status=initial)
    OrderItem.objects.create(order=order, car=car, quantity=1, unit_price=car.price)
    client.force_login(user)
    # Act
    response = change_status(client, order, action)
    # Assert
    order.refresh_from_db()
    car.refresh_from_db()
    assert response.status_code == 302
    assert order.status == initial
    assert car.stock == 3
    assert not Sale.objects.exists()


def test_repeated_payment_creates_only_one_sale(client, customer, employee_factory):
    # Arrange
    user, employee = employee_factory()
    order = Order.objects.create(client=customer[1], employee=employee, status='confirmed')
    client.force_login(user)
    # Act
    change_status(client, order, 'pay')
    change_status(client, order, 'pay')
    # Assert
    assert Sale.objects.filter(order=order).count() == 1
    order.refresh_from_db()
    assert order.status == 'paid'


@pytest.mark.parametrize('action', ['take', 'confirm', 'pay', 'deliver', 'cancel'])
def test_other_employee_cannot_change_assigned_order(client, customer, employee_factory, action):
    # Arrange
    _, owner = employee_factory('owner')
    intruder, _ = employee_factory('other')
    order = Order.objects.create(client=customer[1], employee=owner)
    client.force_login(intruder)
    # Act
    response = change_status(client, order, action)
    # Assert
    order.refresh_from_db()
    assert response.status_code == 302
    assert order.employee == owner
    assert order.status == 'new'
    assert not Sale.objects.exists()


def test_another_client_cannot_cancel_customer_order(customer, car):
    # Arrange: second authenticated user has no ownership of the order.
    from django.contrib.auth.models import User

    order = Order.objects.create(client=customer[1])
    outsider = User.objects.create_user('outsider')
    browser = HttpClient()
    browser.force_login(outsider)
    # Act
    response = browser.post(reverse('accounts:cancel_order', args=[order.pk]))
    # Assert
    assert response.status_code == 404
    order.refresh_from_db()
    assert order.status == 'new'


@pytest.mark.parametrize('endpoint', ['sales:cart_detail', 'sales:payment', 'accounts:profile'])
def test_anonymous_user_is_redirected_to_login(client, endpoint):
    # Arrange / Act
    response = client.get(reverse(endpoint))
    # Assert
    assert response.status_code == 302
    assert '/accounts/login/' in response.url
