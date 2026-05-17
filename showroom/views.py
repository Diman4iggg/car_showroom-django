from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Car, CarCategory
from sales.models import Client, Order, OrderItem


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

    context = {
        'cars': cars,
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
        messages.error(request, 'Оформлять покупку может только пользователь с ролью клиента.')
        return redirect('showroom:index')

    client = Client.objects.filter(user=request.user).first()
    if not client:
        messages.error(request, 'Для покупки нужен профиль клиента.')
        return redirect('accounts:profile')

    if car.stock < 1:
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

    messages.success(request, f'Заказ №{order.id} создан. Он появился в личном кабинете.')
    return redirect('accounts:profile')
