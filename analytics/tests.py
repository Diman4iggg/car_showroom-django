from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from showroom.models import CarCategory
from .views import build_category_revenue_chart, build_linear_forecast, build_sales_trend_chart


class ForecastTests(TestCase):
    def test_linear_forecast_uses_sales_trend(self):
        forecast = build_linear_forecast([
            {'paid_at__year': 2026, 'paid_at__month': 3, 'total': Decimal('100.00')},
            {'paid_at__year': 2026, 'paid_at__month': 4, 'total': Decimal('200.00')},
        ])

        self.assertEqual(forecast['slope'], 100)
        self.assertEqual(forecast['intercept'], 0)
        self.assertEqual(forecast['forecast'], 300)

    def test_linear_forecast_requires_at_least_two_points(self):
        forecast = build_linear_forecast([
            {'paid_at__year': 2026, 'paid_at__month': 3, 'total': Decimal('100.00')},
        ])

        self.assertIsNone(forecast['slope'])
        self.assertIsNone(forecast['forecast'])

    def test_matplotlib_chart_builders_return_image_data(self):
        category = CarCategory(name='Sedan')
        category.revenue = Decimal('1000.00')
        forecast = build_linear_forecast([
            {'paid_at__year': 2026, 'paid_at__month': 3, 'total': Decimal('100.00')},
            {'paid_at__year': 2026, 'paid_at__month': 4, 'total': Decimal('200.00')},
        ])

        self.assertIsInstance(build_category_revenue_chart([category]), str)
        self.assertIsInstance(build_sales_trend_chart(forecast), str)


class AnalyticsAccessTests(TestCase):
    def test_dashboard_requires_superuser(self):
        user = User.objects.create_user('client', 'client@example.com', 'StrongPass12345')
        self.client.force_login(user)

        response = self.client.get(reverse('analytics:dashboard'))

        self.assertRedirects(response, reverse('accounts:profile'))

    def test_superuser_can_open_dashboard(self):
        user = User.objects.create_superuser('admin', 'admin@example.com', 'StrongPass12345')
        self.client.force_login(user)

        response = self.client.get(reverse('analytics:dashboard'))

        self.assertEqual(response.status_code, 200)
