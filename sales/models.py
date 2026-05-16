from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from showroom.models import Car


phone_validator = RegexValidator(
    regex=r'^\+375 \((29|33|44|25)\) \d{3}-\d{2}-\d{2}$',
    message='Телефон должен быть в формате +375 (29) XXX-XX-XX.',
)


def validate_adult(value):
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 18:
        raise ValidationError('Клиенты и сотрудники должны быть старше 18 лет.')


class Client(models.Model):
    last_name = models.CharField(max_length=80, verbose_name='Фамилия')
    first_name = models.CharField(max_length=80, verbose_name='Имя')
    middle_name = models.CharField(max_length=80, blank=True, verbose_name='Отчество')
    birth_date = models.DateField(verbose_name='Дата рождения', validators=[validate_adult])
    phone = models.CharField(max_length=19, verbose_name='Телефон', validators=[phone_validator])
    email = models.EmailField(verbose_name='Email')
    city = models.CharField(max_length=100, verbose_name='Город')
    address = models.CharField(max_length=255, verbose_name='Адрес')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    class Meta:
        verbose_name = 'клиент'
        verbose_name_plural = 'клиенты'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class Employee(models.Model):
    last_name = models.CharField(max_length=80, verbose_name='Фамилия')
    first_name = models.CharField(max_length=80, verbose_name='Имя')
    middle_name = models.CharField(max_length=80, blank=True, verbose_name='Отчество')
    position = models.CharField(max_length=120, verbose_name='Должность')
    birth_date = models.DateField(verbose_name='Дата рождения', validators=[validate_adult])
    phone = models.CharField(max_length=19, verbose_name='Телефон', validators=[phone_validator])
    email = models.EmailField(verbose_name='Email')
    clients = models.ManyToManyField(
        Client,
        related_name='employees',
        blank=True,
        verbose_name='Клиенты сотрудника',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    class Meta:
        verbose_name = 'сотрудник'
        verbose_name_plural = 'сотрудники'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('paid', 'Оплачен'),
        ('delivered', 'Выдан клиенту'),
        ('cancelled', 'Отменен'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Клиент',
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Сотрудник',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус',
    )
    order_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата заказа')
    delivery_date = models.DateField(null=True, blank=True, verbose_name='Дата доставки/выдачи')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-order_date']

    def __str__(self):
        return f'Заказ №{self.pk} для {self.client}'

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ',
    )
    car = models.ForeignKey(
        Car,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Автомобиль',
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Количество',
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Цена за единицу',
    )

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказа'

    def __str__(self):
        return f'{self.car} x {self.quantity}'

    @property
    def total_price(self):
        return self.quantity * self.unit_price


class Sale(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name='sale',
        verbose_name='Заказ',
    )
    paid_at = models.DateTimeField(verbose_name='Дата оплаты')
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Итоговая сумма',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    class Meta:
        verbose_name = 'продажа'
        verbose_name_plural = 'продажи'
        ordering = ['-paid_at']

    def __str__(self):
        return f'Продажа по заказу №{self.order_id}'
