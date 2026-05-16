from django.db import models


class CarCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'вид автомобиля'
        verbose_name_plural = 'виды автомобилей'
        ordering = ['name']

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    country = models.CharField(max_length=80, verbose_name='Страна')
    website = models.URLField(blank=True, verbose_name='Сайт')

    class Meta:
        verbose_name = 'изготовитель'
        verbose_name_plural = 'изготовители'
        ordering = ['name']

    def __str__(self):
        return self.name


class CarFeature(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')

    class Meta:
        verbose_name = 'характеристика'
        verbose_name_plural = 'характеристики'
        ordering = ['name']

    def __str__(self):
        return self.name


class Car(models.Model):
    FUEL_CHOICES = [
        ('petrol', 'Бензин'),
        ('diesel', 'Дизель'),
        ('hybrid', 'Гибрид'),
        ('electric', 'Электро'),
    ]

    name = models.CharField(max_length=150, verbose_name='Название')
    category = models.ForeignKey(
        CarCategory,
        on_delete=models.PROTECT,
        related_name='cars',
        verbose_name='Вид автомобиля',
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        related_name='cars',
        verbose_name='Изготовитель',
    )
    features = models.ManyToManyField(
        CarFeature,
        related_name='cars',
        blank=True,
        verbose_name='Характеристики',
    )
    year = models.PositiveSmallIntegerField(verbose_name='Год выпуска')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена')
    stock = models.PositiveIntegerField(default=0, verbose_name='Количество на складе')
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, verbose_name='Тип топлива')
    color = models.CharField(max_length=80, blank=True, verbose_name='Цвет')
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(upload_to='cars/', blank=True, verbose_name='Фото')
    is_available = models.BooleanField(default=True, verbose_name='Доступен для продажи')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    class Meta:
        verbose_name = 'автомобиль'
        verbose_name_plural = 'автомобили'
        ordering = ['manufacturer__name', 'name', '-year']

    def __str__(self):
        return f'{self.manufacturer} {self.name} ({self.year})'
