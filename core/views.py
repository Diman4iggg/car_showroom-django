from django.http import HttpResponse


def page_placeholder(request, title):
    return HttpResponse(f'<h1>{title}</h1><p>Страница будет наполнена данными из базы.</p>')


def about(request):
    return page_placeholder(request, 'О компании')


def news(request):
    return page_placeholder(request, 'Новости')


def faq(request):
    return page_placeholder(request, 'Словарь терминов и FAQ')


def contacts(request):
    return page_placeholder(request, 'Контакты')


def privacy(request):
    return page_placeholder(request, 'Политика конфиденциальности')


def vacancies(request):
    return page_placeholder(request, 'Вакансии')


def reviews(request):
    return page_placeholder(request, 'Отзывы')


def promo_codes(request):
    return page_placeholder(request, 'Промокоды и купоны')
