from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from sales.models import Client, Employee
from showroom.models import Car, CarCategory, Manufacturer


@pytest.fixture(autouse=True)
def block_external_http(monkeypatch):
    def blocked_send(*args, **kwargs):
        raise AssertionError('Unexpected HTTP request: install a transport stub in this test')

    monkeypatch.setattr('requests.sessions.Session.send', blocked_send)


@pytest.fixture
def car(db):
    return Car.objects.create(
        name='Test sedan',
        category=CarCategory.objects.create(name='Sedan'),
        manufacturer=Manufacturer.objects.create(name='Test Motors', country='BY'),
        year=2025, price=Decimal('100.00'), stock=3, fuel_type='petrol',
    )


@pytest.fixture
def customer(db):
    user = User.objects.create_user('buyer', password='TestPassword123!')
    record = Client.objects.create(
        user=user, first_name='Ivan', last_name='Ivanov', birth_date=date(1990, 1, 1),
        phone='+375 (29) 123-45-67', email='buyer@example.com', city='Minsk', address='Test 1',
    )
    return user, record


@pytest.fixture
def employee_factory(db):
    def create(name='manager'):
        user = User.objects.create_user(name, password='TestPassword123!')
        user.profile.role = 'employee'
        user.profile.save()
        record = Employee.objects.create(
            user=user, first_name='Petr', last_name='Petrov', position='Manager',
            birth_date=date(1990, 1, 1), phone='+375 (33) 123-45-67',
            email=f'{name}@example.com',
        )
        return user, record

    return create


@pytest.fixture
def payment_data():
    return {
        'cardholder_name': 'IVAN IVANOV', 'card_number': '4111111111111111',
        'expiry_month': '12', 'expiry_year': str(date.today().year + 1),
        'cvv': '123', 'agreement': 'on',
    }
