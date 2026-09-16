from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    class Meta:
        abstract = True


class CompanyInfo(TimeStampedModel):
    title = models.CharField(max_length=150, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')

    class Meta:
        verbose_name = 'информация о компании'
        verbose_name_plural = 'информация о компании'

    def __str__(self):
        return self.title


class PartnerCompany(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True, verbose_name='Название')
    website = models.URLField(verbose_name='Сайт')
    logo = models.ImageField(upload_to='partners/', blank=True, verbose_name='Логотип')
    description = models.CharField(max_length=255, blank=True, verbose_name='Краткое описание')
    is_active = models.BooleanField(default=True, verbose_name='Показывать на сайте')

    class Meta:
        verbose_name = 'компания-партнер'
        verbose_name_plural = 'компании-партнеры'
        ordering = ['name']

    def __str__(self):
        return self.name


class NewsArticle(TimeStampedModel):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    summary = models.CharField(max_length=300, verbose_name='Краткое содержание')
    body = models.TextField(verbose_name='Текст статьи')
    image = models.ImageField(upload_to='news/', blank=True, verbose_name='Картинка')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата публикации')

    class Meta:
        verbose_name = 'новость'
        verbose_name_plural = 'новости'
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title


class FAQ(TimeStampedModel):
    question = models.CharField(max_length=255, verbose_name='Вопрос')
    answer = models.TextField(verbose_name='Ответ')

    class Meta:
        verbose_name = 'вопрос и ответ'
        verbose_name_plural = 'словарь терминов и FAQ'
        ordering = ['question']

    def __str__(self):
        return self.question


class ContactEmployee(TimeStampedModel):
    full_name = models.CharField(max_length=180, verbose_name='ФИО')
    position = models.CharField(max_length=120, verbose_name='Должность')
    work_description = models.TextField(verbose_name='Описание работы')
    phone = models.CharField(max_length=30, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    photo = models.ImageField(upload_to='contacts/', blank=True, verbose_name='Фото')

    class Meta:
        verbose_name = 'контактный сотрудник'
        verbose_name_plural = 'контактные сотрудники'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Vacancy(TimeStampedModel):
    title = models.CharField(max_length=150, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'вакансия'
        verbose_name_plural = 'вакансии'
        ordering = ['title']

    def __str__(self):
        return self.title


class PrivacyPolicy(TimeStampedModel):
    title = models.CharField(max_length=150, default='Политика конфиденциальности', verbose_name='Заголовок')
    text = models.TextField(blank=True, verbose_name='Текст')

    class Meta:
        verbose_name = 'политика конфиденциальности'
        verbose_name_plural = 'политика конфиденциальности'

    def __str__(self):
        return self.title


class Review(TimeStampedModel):
    author_name = models.CharField(max_length=80, verbose_name='Имя')
    rating = models.PositiveSmallIntegerField(
        verbose_name='Оценка',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField(max_length=1000, verbose_name='Текст')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')

    class Meta:
        verbose_name = 'отзыв'
        verbose_name_plural = 'отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author_name}: {self.rating}/5'


class PromoCode(TimeStampedModel):
    code = models.CharField(max_length=40, unique=True, verbose_name='Код')
    description = models.TextField(verbose_name='Описание')
    discount_percent = models.PositiveSmallIntegerField(
        verbose_name='Скидка, %',
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    starts_at = models.DateField(verbose_name='Дата начала')
    ends_at = models.DateField(verbose_name='Дата окончания')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'промокод'
        verbose_name_plural = 'промокоды и купоны'
        ordering = ['-is_active', 'ends_at', 'code']

    def __str__(self):
        return self.code
