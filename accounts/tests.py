from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import RegistrationForm
from .models import UserProfile
from sales.models import Client, Employee, Order, OrderItem, Sale
from showroom.models import Car, CarCategory, Manufacturer


def registration_data(**overrides):
    data = {
        'username': 'client1',
        'email': 'client1@example.com',
        'role': 'client',
        'last_name': 'Ivanov',
        'first_name': 'Ivan',
        'middle_name': '',
        'birth_date': date(1990, 1, 1),
        'phone': '+375 (29) 123-45-67',
        'city': 'Minsk',
        'address': 'Lenina 1',
        'position': '',
        'password1': 'StrongPass12345',
        'password2': 'StrongPass12345',
    }
    data.update(overrides)
    return data


def create_car(stock=2):
    category = CarCategory.objects.create(name='Sedan')
    manufacturer = Manufacturer.objects.create(name='Toyota', country='Japan')
    return Car.objects.create(
        name='Camry',
        category=category,
        manufacturer=manufacturer,
        year=2024,
        price=Decimal('100000.00'),
        stock=stock,
        fuel_type='petrol',
    )


def create_client_user():
    user = User.objects.create_user('client1', 'client1@example.com', 'StrongPass12345')
    user.profile.role = 'client'
    user.profile.save()
    client = Client.objects.create(
        user=user,
        last_name='Ivanov',
        first_name='Ivan',
        birth_date=date(1990, 1, 1),
        phone='+375 (29) 123-45-67',
        email='client1@example.com',
        city='Minsk',
        address='Lenina 1',
    )
    return user, client


def create_employee_user():
    user = User.objects.create_user('employee1', 'employee1@example.com', 'StrongPass12345')
    user.profile.role = 'employee'
    user.profile.save()
    employee = Employee.objects.create(
        user=user,
        last_name='Petrov',
        first_name='Petr',
        position='Manager',
        birth_date=date(1990, 1, 1),
        phone='+375 (33) 123-45-67',
        email='employee1@example.com',
    )
    return user, employee


class RegistrationFormTests(TestCase):
    def test_client_registration_creates_user_profile_and_client(self):
        response = self.client.post(reverse('accounts:register'), data=registration_data())

        self.assertRedirects(response, reverse('accounts:profile'))
        user = User.objects.get(username='client1')
        self.assertEqual(user.profile.role, 'client')
        self.assertTrue(Client.objects.filter(user=user, phone='+375 (29) 123-45-67').exists())

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(username='existing', email='client1@example.com', password='pass')

        form = RegistrationForm(data=registration_data(username='newuser'))

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_employee_registration_requires_position(self):
        form = RegistrationForm(data=registration_data(role='employee', city='', address='', position=''))

        self.assertFalse(form.is_valid())
        self.assertIn('position', form.errors)


class ProfileViewTests(TestCase):
    def test_superuser_without_profile_gets_admin_profile_page(self):
        user = User.objects.create_superuser('admin', 'admin@example.com', 'StrongPass12345')
        UserProfile.objects.filter(user=user).delete()
        self.client.force_login(user)

        response = self.client.get(reverse('accounts:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'analytics')

    def test_client_profile_contains_orders_and_promos(self):
        user, client = create_client_user()
        car = create_car()
        order = Order.objects.create(client=client)
        OrderItem.objects.create(order=order, car=car, quantity=1, unit_price=car.price)
        self.client.force_login(user)

        response = self.client.get(reverse('accounts:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['orders']), [order])


class OrderStatusViewTests(TestCase):
    def setUp(self):
        self.client_user, self.client_record = create_client_user()
        self.employee_user, self.employee_record = create_employee_user()
        self.car = create_car(stock=1)
        self.order = Order.objects.create(client=self.client_record)
        OrderItem.objects.create(order=self.order, car=self.car, quantity=1, unit_price=self.car.price)

    def test_client_can_cancel_new_order_and_restore_stock(self):
        self.client.force_login(self.client_user)

        response = self.client.post(reverse('accounts:cancel_order', args=[self.order.id]))

        self.assertRedirects(response, reverse('accounts:profile'))
        self.order.refresh_from_db()
        self.car.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')
        self.assertEqual(self.car.stock, 2)

    def test_employee_can_take_confirm_pay_and_deliver_order(self):
        self.client.force_login(self.employee_user)

        self.client.post(reverse('accounts:update_order_status', args=[self.order.id, 'take']))
        self.order.refresh_from_db()
        self.assertEqual(self.order.employee, self.employee_record)

        self.client.post(reverse('accounts:update_order_status', args=[self.order.id, 'confirm']))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')

        self.client.post(reverse('accounts:update_order_status', args=[self.order.id, 'pay']))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
        self.assertTrue(Sale.objects.filter(order=self.order).exists())

        self.client.post(reverse('accounts:update_order_status', args=[self.order.id, 'deliver']))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'delivered')
        self.assertIsNotNone(self.order.delivery_at)
