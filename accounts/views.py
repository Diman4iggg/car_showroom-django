import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import RegistrationForm
from .models import UserProfile
from core.models import PromoCode
from sales.models import Client, Employee, Order, Sale


logger = logging.getLogger(__name__)


def restore_order_stock(order):
    for item in order.items.select_related('car'):
        car = item.car
        car.stock += item.quantity
        car.is_available = True
        car.save(update_fields=['stock', 'is_available', 'updated_at'])


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            user.profile.role = form.cleaned_data['role']
            user.profile.save()

            profile_data = {
                'user': user,
                'last_name': form.cleaned_data['last_name'],
                'first_name': form.cleaned_data['first_name'],
                'middle_name': form.cleaned_data['middle_name'],
                'birth_date': form.cleaned_data['birth_date'],
                'phone': form.cleaned_data['phone'],
                'email': form.cleaned_data['email'],
            }
            if form.cleaned_data['role'] == 'employee':
                Employee.objects.create(
                    **profile_data,
                    position=form.cleaned_data['position'],
                )
            else:
                Client.objects.create(
                    **profile_data,
                    city=form.cleaned_data['city'],
                    address=form.cleaned_data['address'],
                )

            login(request, user)
            logger.info(
                'User %s registered with role %s',
                user.username,
                form.cleaned_data['role'],
            )
            return redirect('accounts:profile')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    context = {
        'profile': profile,
        'admin_mode': False,
        'client': None,
        'employee': None,
        'new_orders': Order.objects.none(),
        'orders': Order.objects.none(),
        'sales': Sale.objects.none(),
        'active_promos': PromoCode.objects.none(),
    }

    if profile is None:
        if request.user.is_superuser:
            context['admin_mode'] = True
            logger.info('Superuser %s opened admin profile without UserProfile', request.user.username)
            return render(request, 'accounts/profile.html', context)

        profile = UserProfile.objects.create(user=request.user)
        logger.warning('Missing UserProfile was created automatically for user %s', request.user.username)
        context['profile'] = profile

    today = timezone.localdate()

    if profile.role == 'employee':
        employee = Employee.objects.filter(user=request.user).first()
        context['employee'] = employee
        if employee:
            context['new_orders'] = Order.objects.filter(status='new', employee__isnull=True).select_related('client')
            context['orders'] = Order.objects.filter(employee=employee).select_related('client')
            context['sales'] = Sale.objects.filter(order__employee=employee).select_related('order', 'order__client')
    else:
        client = Client.objects.filter(user=request.user).first()
        context['client'] = client
        if client:
            context['orders'] = Order.objects.filter(client=client).prefetch_related('items')

        context['active_promos'] = PromoCode.objects.filter(
            is_active=True,
            starts_at__lte=today,
            ends_at__gte=today,
        )

    return render(request, 'accounts/profile.html', context)


@login_required
@require_POST
def cancel_order(request, order_id):
    client = Client.objects.filter(user=request.user).first()
    order = get_object_or_404(Order, id=order_id, client=client)

    if order.status != 'new':
        logger.warning(
            'Client %s tried to cancel order %s with status %s',
            client.id if client else None,
            order.id,
            order.status,
        )
        messages.error(request, 'Можно отменить только новый заказ.')
        return redirect('accounts:profile')

    restore_order_stock(order)
    order.status = 'cancelled'
    order.save(update_fields=['status', 'updated_at'])
    logger.info('Client %s cancelled order %s', client.id if client else None, order.id)
    messages.success(request, f'Заказ №{order.id} отменен.')
    return redirect('accounts:profile')


@login_required
@require_POST
def update_order_status(request, order_id, action):
    if request.user.profile.role != 'employee':
        logger.warning('User %s tried to manage order %s without employee role', request.user.username, order_id)
        messages.error(request, 'Управлять заказами может только сотрудник.')
        return redirect('accounts:profile')

    employee = Employee.objects.filter(user=request.user).first()
    if not employee:
        logger.warning('User %s has employee role but no linked Employee record', request.user.username)
        messages.error(request, 'Профиль сотрудника не найден.')
        return redirect('accounts:profile')

    order = get_object_or_404(Order.objects.select_related('employee'), id=order_id)

    if action == 'take':
        if order.employee and order.employee != employee:
            messages.error(request, 'Заказ уже закреплен за другим сотрудником.')
            return redirect('accounts:profile')
        if order.status != 'new':
            messages.error(request, 'В работу можно взять только новый заказ.')
            return redirect('accounts:profile')
        order.employee = employee
        order.save(update_fields=['employee', 'updated_at'])
        logger.info('Employee %s took order %s', employee.id, order.id)
        messages.success(request, f'Заказ №{order.id} закреплен за вами.')
        return redirect('accounts:profile')

    if order.employee != employee:
        messages.error(request, 'Можно изменять только заказы, закрепленные за вами.')
        return redirect('accounts:profile')

    if action == 'confirm':
        if order.status != 'new':
            messages.error(request, 'Подтвердить можно только новый заказ.')
        else:
            order.status = 'confirmed'
            order.save(update_fields=['status', 'updated_at'])
            logger.info('Employee %s confirmed order %s', employee.id, order.id)
            messages.success(request, f'Заказ №{order.id} подтвержден.')

    elif action == 'cancel':
        if order.status in ['paid', 'delivered', 'cancelled']:
            messages.error(request, 'Этот заказ уже нельзя отменить.')
        else:
            restore_order_stock(order)
            order.status = 'cancelled'
            order.save(update_fields=['status', 'updated_at'])
            logger.info('Employee %s cancelled order %s', employee.id, order.id)
            messages.success(request, f'Заказ №{order.id} отменен.')

    elif action == 'pay':
        if order.status != 'confirmed':
            messages.error(request, 'Оплатить можно только подтвержденный заказ.')
        else:
            order.status = 'paid'
            order.save(update_fields=['status', 'updated_at'])
            Sale.objects.get_or_create(
                order=order,
                defaults={
                    'paid_at': timezone.now(),
                    'total_amount': order.total_amount,
                },
            )
            logger.info('Employee %s marked order %s as paid', employee.id, order.id)
            messages.success(request, f'Заказ №{order.id} отмечен как оплаченный.')

    elif action == 'deliver':
        if order.status != 'paid':
            messages.error(request, 'Выдать можно только оплаченный заказ.')
        else:
            order.status = 'delivered'
            order.delivery_date = timezone.localdate()
            order.delivery_at = timezone.now()
            order.save(update_fields=['status', 'delivery_date', 'delivery_at', 'updated_at'])
            logger.info('Employee %s delivered order %s', employee.id, order.id)
            messages.success(request, f'Заказ №{order.id} выдан клиенту.')

    else:
        messages.error(request, 'Неизвестное действие с заказом.')

    return redirect('accounts:profile')
