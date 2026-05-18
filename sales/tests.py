from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase

from showroom.models import Car, CarCategory, Manufacturer
from .models import Client, Order, OrderItem, phone_validator, validate_adult


class SalesValidationTests(TestCase):
    def test_phone_validator_accepts_required_belarus_format(self):
        phone_validator('+375 (29) 123-45-67')

    def test_phone_validator_rejects_wrong_format(self):
        with self.assertRaises(ValidationError):
            phone_validator('8029 1234567')

    def test_validate_adult_rejects_minor(self):
        with self.assertRaises(ValidationError):
            validate_adult(date.today().replace(year=date.today().year - 17))


class OrderModelTests(TestCase):
    def test_order_total_amount_sums_items(self):
        category = CarCategory.objects.create(name='Sedan')
        manufacturer = Manufacturer.objects.create(name='Toyota', country='Japan')
        car = Car.objects.create(
            name='Camry',
            category=category,
            manufacturer=manufacturer,
            year=2024,
            price=Decimal('100000.00'),
            stock=2,
            fuel_type='petrol',
        )
        client = Client.objects.create(
            last_name='Ivanov',
            first_name='Ivan',
            birth_date=date(1990, 1, 1),
            phone='+375 (29) 123-45-67',
            email='ivan@example.com',
            city='Minsk',
            address='Lenina 1',
        )
        order = Order.objects.create(client=client)
        OrderItem.objects.create(order=order, car=car, quantity=2, unit_price=Decimal('100000.00'))

        self.assertEqual(order.total_amount, Decimal('200000.00'))
