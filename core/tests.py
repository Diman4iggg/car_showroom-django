from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ReviewForm
from .models import CompanyInfo, ContactEmployee, FAQ, NewsArticle, PrivacyPolicy, PromoCode, Review, Vacancy


class ReviewFormTests(TestCase):
    def test_review_text_must_have_at_least_ten_characters(self):
        form = ReviewForm(data={
            'author_name': 'Ivan',
            'rating': 5,
            'text': 'short',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_review_form_accepts_valid_data(self):
        form = ReviewForm(data={
            'author_name': 'Ivan',
            'rating': 5,
            'text': 'Great showroom service',
        })

        self.assertTrue(form.is_valid())


class ReviewModelTests(TestCase):
    def test_review_rating_cannot_be_greater_than_five(self):
        review = Review(author_name='Ivan', rating=6, text='Great showroom service')

        with self.assertRaises(ValidationError):
            review.full_clean()


class CoreViewTests(TestCase):
    def test_content_pages_render_database_records(self):
        CompanyInfo.objects.create(title='About', text='About text')
        NewsArticle.objects.create(
            title='News',
            summary='Summary',
            body='Body',
            image='news/test.jpg',
            published_at=timezone.now(),
        )
        FAQ.objects.create(question='Question?', answer='Answer')
        ContactEmployee.objects.create(
            full_name='Ivan Ivanov',
            position='Manager',
            work_description='Sales',
            phone='+375 (29) 123-45-67',
            email='ivan@example.com',
        )
        PrivacyPolicy.objects.create(title='Privacy', text='')
        Vacancy.objects.create(title='Manager', description='Sales')
        Review.objects.create(author_name='Ivan', rating=5, text='Great showroom service')

        for url_name in ['about', 'news', 'faq', 'contacts', 'privacy', 'vacancies', 'reviews']:
            response = self.client.get(reverse(f'core:{url_name}'))
            self.assertEqual(response.status_code, 200)

    def test_news_page_shows_article_image(self):
        NewsArticle.objects.create(
            title='New car arrived',
            summary='Short summary',
            body='Full article',
            image='news/car.jpg',
            published_at=timezone.now(),
        )

        response = self.client.get(reverse('core:news'))

        self.assertContains(response, '/media/news/car.jpg')

    def test_add_review_saves_valid_review(self):
        response = self.client.post(reverse('core:add_review'), data={
            'author_name': 'Ivan',
            'rating': 5,
            'text': 'Great showroom service',
        })

        self.assertRedirects(response, reverse('core:reviews'))
        self.assertTrue(Review.objects.filter(author_name='Ivan').exists())

    def test_promo_codes_splits_active_and_archived(self):
        today = timezone.localdate()
        PromoCode.objects.create(
            code='ACTIVE',
            description='Active discount',
            discount_percent=10,
            starts_at=today - timedelta(days=1),
            ends_at=today + timedelta(days=1),
        )
        PromoCode.objects.create(
            code='OLD',
            description='Old discount',
            discount_percent=10,
            starts_at=today - timedelta(days=10),
            ends_at=today - timedelta(days=5),
        )

        response = self.client.get(reverse('core:promo_codes'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['active_promos'].values_list('code', flat=True)), ['ACTIVE'])
        self.assertEqual(list(response.context['archived_promos'].values_list('code', flat=True)), ['OLD'])
