import logging
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from integrations.services import get_exchange_rates
from .models import Car, CarCategory
from sales.models import Client, Order, OrderItem


logger = logging.getLogger(__name__)


def add_currency_prices(cars, exchange_rates):
    if not exchange_rates.get('ok'):
        logger.warning('Exchange rates are unavailable on catalog page: %s', exchange_rates.get('error'))
        return cars

    usd_rate = Decimal(str(exchange_rates.get('usd') or 0))
    eur_rate = Decimal(str(exchange_rates.get('eur') or 0))

    if usd_rate <= 0 or eur_rate <= 0:
        return cars

    for car in cars:
        car.price_usd = (car.price * usd_rate).quantize(Decimal('0.01'))
        car.price_eur = (car.price * eur_rate).quantize(Decimal('0.01'))

    return cars


def index(request):
    cars = Car.objects.select_related('category', 'manufacturer').prefetch_related('features')
    cars = cars.filter(is_available=True)

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    sort = request.GET.get('sort', '').strip()

    if query:
        cars = cars.filter(name__icontains=query)

    if category_id:
        cars = cars.filter(category_id=category_id)

    if min_price:
        cars = cars.filter(price__gte=min_price)

    if max_price:
        cars = cars.filter(price__lte=max_price)

    sort_options = {
        'price_asc': 'price',
        'price_desc': '-price',
        'year_desc': '-year',
        'name_asc': 'name',
    }
    cars = cars.order_by(sort_options.get(sort, 'manufacturer__name'))
    cars = list(cars)
    exchange_rates = get_exchange_rates()
    add_currency_prices(cars, exchange_rates)

    context = {
        'cars': cars,
        'exchange_rates': exchange_rates,
        'categories': CarCategory.objects.all(),
        'selected_category': category_id,
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
    }
    return render(request, 'showroom/index.html', context)


@login_required
def buy_car(request, car_id):
    car = get_object_or_404(Car, id=car_id, is_available=True)

    if request.user.profile.role != 'client':
        logger.warning('User %s tried to buy car %s without client role', request.user.username, car_id)
        messages.error(request, 'Оформлять покупку может только пользователь с ролью клиента.')
        return redirect('showroom:index')

    client = Client.objects.filter(user=request.user).first()
    if not client:
        logger.warning('User %s has client role but no linked Client record', request.user.username)
        messages.error(request, 'Для покупки нужен профиль клиента.')
        return redirect('accounts:profile')

    if car.stock < 1:
        logger.warning('User %s tried to buy out-of-stock car %s', request.user.username, car_id)
        messages.error(request, 'Этот автомобиль сейчас отсутствует на складе.')
        return redirect('showroom:index')

    order = Order.objects.create(client=client, status='new')
    OrderItem.objects.create(
        order=order,
        car=car,
        quantity=1,
        unit_price=car.price,
    )

    car.stock -= 1
    if car.stock == 0:
        car.is_available = False
    car.save(update_fields=['stock', 'is_available', 'updated_at'])
    logger.info('Order %s created by client %s for car %s', order.id, client.id, car.id)

    messages.success(request, f'Заказ №{order.id} создан. Он появился в личном кабинете.')
    return redirect('accounts:profile')
