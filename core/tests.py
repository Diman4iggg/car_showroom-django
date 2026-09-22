from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ReviewForm
from .models import CompanyHistoryEvent, CompanyInfo, ContactEmployee, FAQ, NewsArticle, PrivacyPolicy, PromoCode, Review, Vacancy


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
        article = NewsArticle.objects.create(
            title='New car arrived',
            summary='Short summary',
            body='Full article',
            image='news/car.jpg',
            published_at=timezone.now(),
        )

        response = self.client.get(reverse('core:news'))

        self.assertContains(response, '/media/news/car.jpg')
        self.assertContains(response, reverse('core:news_detail', args=[article.pk]))
        self.assertContains(response, 'Читать далее')
        self.assertNotContains(response, 'Full article')

    def test_news_detail_shows_full_article(self):
        article = NewsArticle.objects.create(
            title='New car arrived',
            summary='Short summary.',
            body='Full article text.',
            image='news/car.jpg',
            published_at=timezone.now(),
        )

        response = self.client.get(reverse('core:news_detail', args=[article.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Full article text.')
        self.assertContains(response, '<article itemscope')

    def test_unpublished_news_detail_returns_not_found(self):
        article = NewsArticle.objects.create(
            title='Draft',
            summary='Draft summary.',
            body='Draft body.',
            is_published=False,
        )

        response = self.client.get(reverse('core:news_detail', args=[article.pk]))

        self.assertEqual(response.status_code, 404)

    def test_faq_uses_native_expandable_elements_and_added_date(self):
        question = FAQ.objects.create(
            question='Что такое тест-драйв?',
            answer='Пробная поездка на выбранном автомобиле.',
        )

        response = self.client.get(reverse('core:faq'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<details')
        self.assertContains(response, '<summary itemprop="name">Что такое тест-драйв?</summary>')
        self.assertContains(response, 'https://schema.org/FAQPage')
        self.assertContains(response, question.created_at.strftime('%d/%m/%Y'))
        self.assertNotContains(response, 'Изменено:')

    def test_contacts_page_shows_employee_cards_with_full_information(self):
        employee = ContactEmployee.objects.create(
            full_name='Ivan Ivanov',
            position='Sales manager',
            work_description='Helps clients choose a car.',
            phone='+375 (29) 123-45-67',
            email='ivan@example.com',
            photo='contacts/ivan.jpg',
        )

        response = self.client.get(reverse('core:contacts'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="employee-grid"')
        self.assertContains(response, 'class="employee-card"')
        self.assertContains(response, '/media/contacts/ivan.jpg')
        self.assertContains(response, 'Helps clients choose a car.')
        self.assertContains(response, 'href="mailto:ivan@example.com"')
        self.assertContains(response, 'href="tel:+375291234567"')
        self.assertContains(response, 'https://schema.org/Person')

    def test_about_page_contains_semantic_and_responsive_content(self):
        company = CompanyInfo.objects.create(title='Our history', text='Company history')
        CompanyHistoryEvent.objects.create(company=company, year=2024, description='Company opened')

        response = self.client.get(reverse('core:about'))

        self.assertContains(response, '<article itemscope')
        self.assertContains(response, '<picture>')
        self.assertContains(response, 'media="(max-width: 700px)"')
        self.assertContains(response, 'banner-credit.png')
        self.assertContains(response, 'banner-test-drive.png')
        self.assertContains(response, '<blockquote')
        self.assertContains(response, '<iframe')
        self.assertContains(response, '<video')
        self.assertContains(response, 'company-tour.webm')
        self.assertContains(response, '2024')
        self.assertContains(response, 'Сертификат качества')
        self.assertContains(response, 'Логотип CarShowroom')
        self.assertContains(response, 'download="CarShowroom-details.txt"')

    def test_anonymous_user_cannot_add_review(self):
        response = self.client.get(reverse('core:add_review'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_client_add_review_saves_username_as_author(self):
        user = User.objects.create_user('client_ivan', 'client@example.com', 'StrongPass12345')
        self.client.force_login(user)

        response = self.client.post(reverse('core:add_review'), data={
            'author_name': 'Fake Name',
            'rating': 5,
            'text': 'Great showroom service',
        })

        self.assertRedirects(response, reverse('core:reviews'))
        self.assertTrue(Review.objects.filter(author_name='client_ivan').exists())
        self.assertFalse(Review.objects.filter(author_name='Fake Name').exists())

    def test_employee_cannot_add_review(self):
        user = User.objects.create_user('employee', 'employee@example.com', 'StrongPass12345')
        user.profile.role = 'employee'
        user.profile.save()
        self.client.force_login(user)

        response = self.client.post(reverse('core:add_review'), data={
            'rating': 5,
            'text': 'Great showroom service',
        })

        self.assertRedirects(response, reverse('core:reviews'))
        self.assertFalse(Review.objects.filter(author_name='employee').exists())

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

    def test_superuser_can_create_update_and_delete_vacancy_from_frontend(self):
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'StrongPass12345')
        self.client.force_login(admin)

        create_response = self.client.post(reverse('core:vacancy_create'), data={
            'title': 'Sales manager',
            'description': 'Work with showroom clients',
            'is_active': 'on',
        })

        self.assertRedirects(create_response, reverse('core:vacancies'))
        vacancy = Vacancy.objects.get(title='Sales manager')

        update_response = self.client.post(reverse('core:vacancy_update', args=[vacancy.pk]), data={
            'title': 'Senior sales manager',
            'description': 'Work with VIP clients',
            'is_active': '',
        })

        self.assertRedirects(update_response, reverse('core:vacancies'))
        vacancy.refresh_from_db()
        self.assertEqual(vacancy.title, 'Senior sales manager')
        self.assertFalse(vacancy.is_active)

        delete_response = self.client.post(reverse('core:vacancy_delete', args=[vacancy.pk]))

        self.assertRedirects(delete_response, reverse('core:vacancies'))
        self.assertFalse(Vacancy.objects.filter(pk=vacancy.pk).exists())

    def test_regular_user_cannot_open_vacancy_create_page(self):
        user = User.objects.create_user('client', 'client@example.com', 'StrongPass12345')
        self.client.force_login(user)

        response = self.client.get(reverse('core:vacancy_create'))

        self.assertEqual(response.status_code, 302)
