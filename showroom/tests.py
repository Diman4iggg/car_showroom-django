from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserProfile
from core.models import NewsArticle
from sales.models import Client, Order, OrderItem
from .models import Car, CarCategory, Manufacturer


def create_car(name='Camry', price=Decimal('100000.00'), stock=2):
    category, _ = CarCategory.objects.get_or_create(name='Sedan')
    manufacturer, _ = Manufacturer.objects.get_or_create(name='Toyota', defaults={'country': 'Japan'})
    return Car.objects.create(
        name=name,
        category=category,
        manufacturer=manufacturer,
        year=2024,
        price=price,
        stock=stock,
        fuel_type='petrol',
    )


class CatalogViewTests(TestCase):
    @patch('showroom.views.get_exchange_rates')
    def test_catalog_filters_cars_by_query(self, mocked_rates):
        mocked_rates.return_value = {'ok': False, 'error': 'offline'}
        create_car(name='Camry')
        create_car(name='Corolla')

        response = self.client.get(reverse('showroom:index'), {'q': 'Camry'})

        self.assertEqual(response.status_code, 200)
        cars = response.context['cars']
        self.assertEqual(len(cars), 1)
        self.assertEqual(cars[0].name, 'Camry')

    @patch('showroom.views.get_exchange_rates')
    def test_catalog_adds_usd_and_eur_prices(self, mocked_rates):
        mocked_rates.return_value = {'ok': True, 'usd': 0.3, 'eur': 0.25}
        create_car(price=Decimal('100000.00'))

        response = self.client.get(reverse('showroom:index'))

        car = response.context['cars'][0]
        self.assertEqual(car.price_usd, Decimal('30000.00'))
        self.assertEqual(car.price_eur, Decimal('25000.00'))

    @patch('showroom.views.get_exchange_rates')
    def test_home_page_shows_latest_published_article(self, mocked_rates):
        mocked_rates.return_value = {'ok': False, 'error': 'offline'}
        NewsArticle.objects.create(
            title='Old news',
            summary='Old summary',
            body='Old body',
            published_at=timezone.now() - timedelta(days=1),
        )
        latest = NewsArticle.objects.create(
            title='Latest showroom news',
            summary='Latest summary',
            body='Latest body',
            published_at=timezone.now(),
        )

        response = self.client.get(reverse('showroom:index'))

        self.assertEqual(response.context['latest_article'], latest)
        self.assertContains(response, 'Latest showroom news')

    def test_car_detail_shows_car_information_and_semantic_markup(self):
        car = create_car(name='Camry', price=Decimal('100000.00'))
        car.description = 'Comfortable family sedan'
        car.save(update_fields=['description'])

        response = self.client.get(reverse('showroom:car_detail', args=[car.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['car'], car)
        self.assertContains(response, 'Comfortable family sedan')
        self.assertContains(response, 'itemscope')
        self.assertContains(response, 'itemprop="name"')

    def test_car_detail_returns_404_for_unavailable_car(self):
        car = create_car()
        car.is_available = False
        car.save(update_fields=['is_available'])

        response = self.client.get(reverse('showroom:car_detail', args=[car.id]))

        self.assertEqual(response.status_code, 404)


class BuyCarViewTests(TestCase):
    def test_client_can_create_order_for_available_car(self):
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
        car = create_car(stock=2)
        self.client.force_login(user)

        response = self.client.post(reverse('showroom:buy_car', args=[car.id]))

        self.assertRedirects(response, reverse('accounts:profile'))
        order = Order.objects.get(client=client)
        self.assertEqual(order.status, 'new')
        self.assertTrue(OrderItem.objects.filter(order=order, car=car, quantity=1).exists())
        car.refresh_from_db()
        self.assertEqual(car.stock, 1)

    def test_employee_cannot_buy_car(self):
        user = User.objects.create_user('employee1', 'employee1@example.com', 'StrongPass12345')
        user.profile.role = 'employee'
        user.profile.save()
        car = create_car(stock=2)
        self.client.force_login(user)

        response = self.client.post(reverse('showroom:buy_car', args=[car.id]))

        self.assertRedirects(response, reverse('showroom:index'), fetch_redirect_response=False)
        self.assertEqual(Order.objects.count(), 0)
