from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from showroom.models import Car
from .forms import PaymentForm
from .models import Client, Order, OrderItem, Sale


CART_SESSION_KEY = 'cart'


def _get_client(user):
    profile = getattr(user, 'profile', None)
    if not profile or profile.role != 'client':
        return None
    return Client.objects.filter(user=user).first()


def _get_cart(request):
    cart = request.session.get(CART_SESSION_KEY, {})
    normalized = {}
    for car_id, quantity in cart.items():
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue
        if str(car_id).isdigit() and quantity > 0:
            normalized[str(car_id)] = quantity
    return normalized


def _cart_items(request):
    cart = _get_cart(request)
    cars = {
        str(car.id): car
        for car in Car.objects.filter(id__in=cart.keys(), is_available=True).select_related('manufacturer')
    }
    items = []
    cleaned_cart = {}
    total = Decimal('0.00')

    for car_id, quantity in cart.items():
        car = cars.get(car_id)
        if not car or car.stock < 1:
            continue
        quantity = min(quantity, car.stock)
        item_total = car.price * quantity
        cleaned_cart[car_id] = quantity
        items.append({'car': car, 'quantity': quantity, 'total_price': item_total})
        total += item_total

    if cleaned_cart != cart:
        request.session[CART_SESSION_KEY] = cleaned_cart
        request.session.modified = True

    return items, total


def _require_client(request):
    client = _get_client(request.user)
    if client:
        return client
    messages.error(request, 'Корзина доступна только пользователям с ролью клиента.')
    return None


@login_required
def cart_detail(request):
    if not _require_client(request):
        return redirect('showroom:index')
    items, total = _cart_items(request)
    return render(request, 'sales/cart.html', {'cart_items': items, 'cart_total': total})


@login_required
@require_POST
def cart_add(request, car_id):
    if not _require_client(request):
        return redirect('showroom:index')

    car = get_object_or_404(Car, id=car_id, is_available=True)
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except (TypeError, ValueError):
        quantity = 1

    cart = _get_cart(request)
    requested_quantity = cart.get(str(car.id), 0) + quantity
    cart[str(car.id)] = min(requested_quantity, car.stock)
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True

    if requested_quantity > car.stock:
        messages.warning(request, f'В корзину добавлено максимально доступное количество: {car.stock}.')
    else:
        messages.success(request, f'{car.name} добавлен в корзину.')
    return redirect('sales:cart_detail')


@login_required
@require_POST
def cart_update(request, car_id, action):
    if not _require_client(request):
        return redirect('showroom:index')

    car = get_object_or_404(Car, id=car_id, is_available=True)
    cart = _get_cart(request)
    quantity = cart.get(str(car.id), 0)

    if action == 'increase':
        if quantity < car.stock:
            cart[str(car.id)] = quantity + 1
        else:
            messages.warning(request, 'Нельзя добавить больше автомобилей, чем есть на складе.')
    elif action == 'decrease':
        if quantity <= 1:
            cart.pop(str(car.id), None)
        else:
            cart[str(car.id)] = quantity - 1

    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True
    return redirect('sales:cart_detail')


@login_required
@require_POST
def cart_remove(request, car_id):
    if not _require_client(request):
        return redirect('showroom:index')
    cart = _get_cart(request)
    cart.pop(str(car_id), None)
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True
    messages.success(request, 'Позиция удалена из корзины.')
    return redirect('sales:cart_detail')


@login_required
def payment(request):
    client = _require_client(request)
    if not client:
        return redirect('showroom:index')

    items, total = _cart_items(request)
    if not items:
        messages.error(request, 'Корзина пуста.')
        return redirect('sales:cart_detail')

    form = PaymentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cart = _get_cart(request)
        try:
            with transaction.atomic():
                locked_cars = {
                    str(car.id): car
                    for car in Car.objects.select_for_update().filter(id__in=cart.keys())
                }
                current_items = []
                current_total = Decimal('0.00')

                for car_id, quantity in cart.items():
                    car = locked_cars.get(car_id)
                    if not car or not car.is_available or quantity > car.stock:
                        raise ValueError('Состав корзины изменился. Проверьте доступное количество автомобилей.')
                    current_items.append((car, quantity))
                    current_total += car.price * quantity

                order = Order.objects.create(
                    client=client,
                    status='paid',
                    comment='Оплачено через демонстрационную форму сайта.',
                )
                for car, quantity in current_items:
                    OrderItem.objects.create(
                        order=order,
                        car=car,
                        quantity=quantity,
                        unit_price=car.price,
                    )
                    car.stock -= quantity
                    if car.stock == 0:
                        car.is_available = False
                    car.save(update_fields=['stock', 'is_available', 'updated_at'])

                Sale.objects.create(
                    order=order,
                    paid_at=timezone.now(),
                    total_amount=current_total,
                )
        except ValueError as error:
            messages.error(request, str(error))
            return redirect('sales:cart_detail')

        request.session[CART_SESSION_KEY] = {}
        request.session.modified = True
        messages.success(request, f'Заказ №{order.id} успешно оплачен.')
        return redirect('accounts:profile')

    return render(
        request,
        'sales/payment.html',
        {'form': form, 'cart_items': items, 'cart_total': total},
    )
