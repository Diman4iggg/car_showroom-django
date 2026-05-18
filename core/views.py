from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ReviewForm, VacancyForm
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
    if request.user.is_superuser:
        context['vacancies'] = Vacancy.objects.all()
    else:
        context['vacancies'] = Vacancy.objects.filter(is_active=True)
    return render(request, 'core/vacancies.html', context)


@user_passes_test(lambda user: user.is_superuser)
def vacancy_create(request):
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Вакансия добавлена.')
            return redirect('core:vacancies')
    else:
        form = VacancyForm()

    return render(request, 'core/vacancy_form.html', {'form': form, 'title': 'Добавить вакансию'})


@user_passes_test(lambda user: user.is_superuser)
def vacancy_update(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    if request.method == 'POST':
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            form.save()
            messages.success(request, 'Вакансия обновлена.')
            return redirect('core:vacancies')
    else:
        form = VacancyForm(instance=vacancy)

    return render(request, 'core/vacancy_form.html', {'form': form, 'title': 'Редактировать вакансию'})


@user_passes_test(lambda user: user.is_superuser)
def vacancy_delete(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    if request.method == 'POST':
        vacancy.delete()
        messages.success(request, 'Вакансия удалена.')
        return redirect('core:vacancies')

    return render(request, 'core/vacancy_confirm_delete.html', {'vacancy': vacancy})


def reviews(request):
    context = base_context()
    context['reviews'] = Review.objects.filter(is_published=True)
    return render(request, 'core/reviews.html', context)


def add_review(request):
    context = base_context()
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:reviews')
    else:
        form = ReviewForm()

    context['form'] = form
    return render(request, 'core/add_review.html', context)


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
