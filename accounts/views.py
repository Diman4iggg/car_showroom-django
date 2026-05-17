from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import RegistrationForm
from core.models import PromoCode
from sales.models import Client, Employee, Order, Sale


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
            return redirect('accounts:profile')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    profile = request.user.profile
    context = {
        'profile': profile,
        'client': None,
        'employee': None,
        'orders': Order.objects.none(),
        'sales': Sale.objects.none(),
        'active_promos': PromoCode.objects.none(),
    }

    today = timezone.localdate()

    if profile.role == 'employee':
        employee = Employee.objects.filter(user=request.user).first()
        context['employee'] = employee
        if employee:
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
