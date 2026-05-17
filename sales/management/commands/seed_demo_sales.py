from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from sales.models import Client, Employee, Order, OrderItem, Sale
from showroom.models import Car, CarCategory, CarFeature, Manufacturer


class Command(BaseCommand):
    help = 'Create demo paid sales for March and April to support analytics trend examples.'

    def handle(self, *args, **options):
        sedan, _ = CarCategory.objects.get_or_create(
            name='Седан',
            defaults={'description': 'Легковые автомобили с классическим кузовом.'},
        )
        crossover, _ = CarCategory.objects.get_or_create(
            name='Кроссовер',
            defaults={'description': 'Автомобили повышенной вместимости и проходимости.'},
        )
        toyota, _ = Manufacturer.objects.get_or_create(name='Toyota', defaults={'country': 'Япония'})
        geely, _ = Manufacturer.objects.get_or_create(name='Geely', defaults={'country': 'Китай'})
        comfort, _ = CarFeature.objects.get_or_create(name='Климат-контроль')
        camera, _ = CarFeature.objects.get_or_create(name='Камера заднего вида')

        camry, _ = Car.objects.get_or_create(
            name='Toyota Camry',
            manufacturer=toyota,
            defaults={
                'category': sedan,
                'year': 2023,
                'price': Decimal('125000.00'),
                'stock': 3,
                'fuel_type': 'petrol',
                'color': 'Черный',
                'description': 'Демонстрационный автомобиль для аналитики.',
                'is_available': True,
            },
        )
        camry.features.add(comfort, camera)

        coolray, _ = Car.objects.get_or_create(
            name='Geely Coolray',
            manufacturer=geely,
            defaults={
                'category': crossover,
                'year': 2023,
                'price': Decimal('89000.00'),
                'stock': 4,
                'fuel_type': 'petrol',
                'color': 'Красный',
                'description': 'Демонстрационный автомобиль для аналитики.',
                'is_available': True,
            },
        )
        coolray.features.add(camera)

        client, _ = Client.objects.get_or_create(
            email='demo.client@carshowroom.by',
            defaults={
                'last_name': 'Демо',
                'first_name': 'Клиент',
                'middle_name': '',
                'birth_date': '1990-01-01',
                'phone': '+375 (29) 555-11-22',
                'city': 'Минск',
                'address': 'ул. Демонстрационная, 1',
            },
        )
        employee, _ = Employee.objects.get_or_create(
            email='demo.employee@carshowroom.by',
            defaults={
                'last_name': 'Демо',
                'first_name': 'Сотрудник',
                'middle_name': '',
                'position': 'Менеджер по продажам',
                'birth_date': '1988-02-02',
                'phone': '+375 (29) 555-33-44',
            },
        )

        demo_sales = [
            (camry, Decimal('125000.00'), timezone.datetime(2026, 3, 15, 10, 30, tzinfo=timezone.get_current_timezone())),
            (coolray, Decimal('89000.00'), timezone.datetime(2026, 4, 12, 14, 45, tzinfo=timezone.get_current_timezone())),
        ]

        created_count = 0
        for car, price, paid_at in demo_sales:
            if Sale.objects.filter(paid_at=paid_at, total_amount=price, order__client=client).exists():
                continue

            order = Order.objects.create(
                client=client,
                employee=employee,
                status='paid',
                delivery_date=paid_at.date(),
                delivery_at=paid_at,
                comment='Демонстрационная продажа для аналитики.',
            )
            OrderItem.objects.create(
                order=order,
                car=car,
                quantity=1,
                unit_price=price,
            )
            Sale.objects.create(
                order=order,
                paid_at=paid_at,
                total_amount=price,
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created demo sales: {created_count}'))
