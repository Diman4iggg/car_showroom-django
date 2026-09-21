from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile
from showroom.models import Car, CarCategory, Manufacturer
from .models import Client, Order, OrderItem, Sale, phone_validator, validate_adult


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


class CartViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('buyer', 'buyer@example.com', 'StrongPass12345')
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.role = 'client'
        profile.save()
        self.client_profile = Client.objects.create(
            user=self.user,
            last_name='Ivanov',
            first_name='Ivan',
            birth_date=date(1990, 1, 1),
            phone='+375 (29) 123-45-67',
            email='buyer@example.com',
            city='Minsk',
            address='Lenina 1',
        )
        category = CarCategory.objects.create(name='Crossover')
        manufacturer = Manufacturer.objects.create(name='Geely', country='China')
        self.car = Car.objects.create(
            name='Coolray',
            category=category,
            manufacturer=manufacturer,
            year=2025,
            price=Decimal('90000.00'),
            stock=3,
            fuel_type='petrol',
        )
        self.client.force_login(self.user)

    def test_client_can_add_car_and_open_semantic_cart_table(self):
        response = self.client.post(
            reverse('sales:cart_add', args=[self.car.id]),
            {'quantity': 2},
        )

        self.assertRedirects(response, reverse('sales:cart_detail'))
        self.assertEqual(self.client.session['cart'][str(self.car.id)], 2)

        response = self.client.get(reverse('sales:cart_detail'))
        self.assertContains(response, '<caption>')
        self.assertContains(response, 'headers="price-header')
        self.assertContains(response, '180000,00 BYN')

    def test_cart_quantity_cannot_exceed_stock(self):
        self.client.post(
            reverse('sales:cart_add', args=[self.car.id]),
            {'quantity': 10},
        )

        self.assertEqual(self.client.session['cart'][str(self.car.id)], self.car.stock)

    def test_cart_item_can_be_increased_decreased_and_removed(self):
        self.client.post(reverse('sales:cart_add', args=[self.car.id]), {'quantity': 1})

        self.client.post(reverse('sales:cart_update', args=[self.car.id, 'increase']))
        self.assertEqual(self.client.session['cart'][str(self.car.id)], 2)

        self.client.post(reverse('sales:cart_update', args=[self.car.id, 'decrease']))
        self.assertEqual(self.client.session['cart'][str(self.car.id)], 1)

        self.client.post(reverse('sales:cart_remove', args=[self.car.id]))
        self.assertNotIn(str(self.car.id), self.client.session['cart'])

    def test_valid_payment_creates_paid_order_sale_and_clears_cart(self):
        self.client.post(reverse('sales:cart_add', args=[self.car.id]), {'quantity': 2})
        next_year = date.today().year + 1

        response = self.client.post(
            reverse('sales:payment'),
            {
                'cardholder_name': 'IVAN IVANOV',
                'card_number': '4111111111111111',
                'expiry_month': '12',
                'expiry_year': str(next_year),
                'cvv': '123',
                'agreement': 'on',
            },
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        order = Order.objects.get(client=self.client_profile)
        self.assertEqual(order.status, 'paid')
        self.assertTrue(OrderItem.objects.filter(order=order, car=self.car, quantity=2).exists())
        self.assertTrue(Sale.objects.filter(order=order, total_amount=Decimal('180000.00')).exists())
        self.car.refresh_from_db()
        self.assertEqual(self.car.stock, 1)
        self.assertEqual(self.client.session['cart'], {})
