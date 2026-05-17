from statistics import mean, median, multimode

from django.contrib.auth.decorators import login_required
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.shortcuts import redirect, render
from django.contrib import messages

from sales.models import Sale
from showroom.models import Car, CarCategory


@login_required
def dashboard(request):
    if not request.user.is_superuser and request.user.profile.role != 'employee':
        messages.error(request, 'Аналитика доступна только сотрудникам.')
        return redirect('accounts:profile')

    category_revenue_expression = ExpressionWrapper(
        F('cars__order_items__quantity') * F('cars__order_items__unit_price'),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

    sale_amounts = [float(value) for value in Sale.objects.values_list('total_amount', flat=True)]
    if sale_amounts:
        average_sale = round(mean(sale_amounts), 2)
        median_sale = round(median(sale_amounts), 2)
        modes = multimode(sale_amounts)
        mode_sale = round(modes[0], 2) if modes else None
    else:
        average_sale = None
        median_sale = None
        mode_sale = None

    price_list = Car.objects.select_related('category', 'manufacturer').order_by('category__name', 'price')

    cars_by_demand = (
        Car.objects.annotate(
            sold_count=Sum(
                'order_items__quantity',
                filter=Q(order_items__order__sale__isnull=False),
            )
        )
        .order_by('-sold_count', 'name')
    )
    most_popular_car = cars_by_demand.exclude(sold_count=None).first()
    unpopular_cars = cars_by_demand.filter(sold_count=None)

    category_sales = (
        CarCategory.objects.annotate(
            sold_count=Sum(
                'cars__order_items__quantity',
                filter=Q(cars__order_items__order__sale__isnull=False),
            ),
            revenue=Sum(
                category_revenue_expression,
                filter=Q(cars__order_items__order__sale__isnull=False),
            ),
        )
        .order_by('name')
    )

    monthly_sales = (
        Sale.objects.values('paid_at__year', 'paid_at__month')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('paid_at__year', 'paid_at__month')
    )

    annual_revenue = (
        Sale.objects.values('paid_at__year')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('paid_at__year')
    )

    context = {
        'price_list': price_list,
        'most_popular_car': most_popular_car,
        'unpopular_cars': unpopular_cars,
        'category_sales': category_sales,
        'monthly_sales': monthly_sales,
        'annual_revenue': annual_revenue,
        'average_sale': average_sale,
        'median_sale': median_sale,
        'mode_sale': mode_sale,
    }
    return render(request, 'analytics/dashboard.html', context)
