from django.shortcuts import render
from django.utils import timezone

from .models import (
    CompanyInfo,
    ContactEmployee,
    FAQ,
    NewsArticle,
    PrivacyPolicy,
    PromoCode,
    Review,
    Vacancy,
)


def base_context():
    return {
        'current_date': timezone.localtime().strftime('%d/%m/%Y'),
    }


def about(request):
    context = base_context()
    context['company_info'] = CompanyInfo.objects.order_by('-updated_at').first()
    return render(request, 'core/about.html', context)


def news(request):
    context = base_context()
    context['articles'] = NewsArticle.objects.filter(is_published=True)
    return render(request, 'core/news.html', context)


def faq(request):
    context = base_context()
    context['questions'] = FAQ.objects.all()
    return render(request, 'core/faq.html', context)


def contacts(request):
    context = base_context()
    context['employees'] = ContactEmployee.objects.all()
    return render(request, 'core/contacts.html', context)


def privacy(request):
    context = base_context()
    context['policy'] = PrivacyPolicy.objects.order_by('-updated_at').first()
    return render(request, 'core/privacy.html', context)


def vacancies(request):
    context = base_context()
    context['vacancies'] = Vacancy.objects.filter(is_active=True)
    return render(request, 'core/vacancies.html', context)


def reviews(request):
    context = base_context()
    context['reviews'] = Review.objects.filter(is_published=True)
    return render(request, 'core/reviews.html', context)


def promo_codes(request):
    context = base_context()
    today = timezone.localdate()
    context['active_promos'] = PromoCode.objects.filter(
        is_active=True,
        starts_at__lte=today,
        ends_at__gte=today,
    )
    context['archived_promos'] = PromoCode.objects.exclude(
        is_active=True,
        starts_at__lte=today,
        ends_at__gte=today,
    )
    return render(request, 'core/promo_codes.html', context)
