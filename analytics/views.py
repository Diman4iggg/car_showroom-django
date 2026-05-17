import base64
from io import BytesIO
from statistics import mean, median, multimode

from django.contrib.auth.decorators import login_required
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.shortcuts import redirect, render
from django.contrib import messages

from sales.models import Client, Sale
from showroom.models import Car, CarCategory


def render_matplotlib_chart(draw_callback):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    fig, ax = plt.subplots(figsize=(8, 4))
    draw_callback(ax)
    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format='png')
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('ascii')


def build_category_revenue_chart(rows):
    labels = [row.name for row in rows]
    values = [float(row.revenue or 0) for row in rows]
    if not labels or not any(values):
        return None

    def draw(ax):
        ax.bar(labels, values, color='#4f7ccf')
        ax.set_title('Выручка по категориям автомобилей')
        ax.set_xlabel('Категория')
        ax.set_ylabel('Выручка, BYN')
        ax.tick_params(axis='x', rotation=25)

    return render_matplotlib_chart(draw)


def build_sales_trend_chart(forecast_data):
    points = forecast_data['points']
    if len(points) < 2 or forecast_data['slope'] is None:
        return None

    labels = [point['label'] for point in points] + ['прогноз']
    x_values = [point['x'] for point in points]
    y_values = [point['value'] for point in points]
    forecast_x = len(points) + 1
    forecast_y = forecast_data['forecast']
    trend_values = [
        forecast_data['slope'] * x + forecast_data['intercept']
        for x in x_values + [forecast_x]
    ]

    def draw(ax):
        ax.plot(x_values, y_values, marker='o', label='Фактическая выручка')
        ax.plot(x_values + [forecast_x], trend_values, linestyle='--', label='Линейный тренд')
        ax.scatter([forecast_x], [forecast_y], color='red', label='Прогноз')
        ax.set_title('Линейный тренд продаж')
        ax.set_xlabel('Месяц')
        ax.set_ylabel('Выручка, BYN')
        ax.set_xticks(x_values + [forecast_x])
        ax.set_xticklabels(labels, rotation=25)
        ax.legend()

    return render_matplotlib_chart(draw)


def build_linear_forecast(monthly_rows):
    points = []
    for index, row in enumerate(monthly_rows, start=1):
        points.append({
            'x': index,
            'label': f"{row['paid_at__month']}/{row['paid_at__year']}",
            'value': float(row['total'] or 0),
        })

    if len(points) < 2:
        return {
            'points': points,
            'slope': None,
            'intercept': None,
            'forecast': None,
        }

    n = len(points)
    sum_x = sum(point['x'] for point in points)
    sum_y = sum(point['value'] for point in points)
    sum_xy = sum(point['x'] * point['value'] for point in points)
    sum_x2 = sum(point['x'] ** 2 for point in points)
    denominator = n * sum_x2 - sum_x ** 2

    if denominator == 0:
        return {
            'points': points,
            'slope': None,
            'intercept': None,
            'forecast': None,
        }

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    next_x = n + 1
    forecast = max(0, slope * next_x + intercept)

    return {
        'points': points,
        'slope': round(slope, 2),
        'intercept': round(intercept, 2),
        'forecast': round(forecast, 2),
    }


@login_required
def dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, 'Аналитика доступна только администратору.')
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

    clients_by_city = (
        Client.objects.values('city')
        .annotate(total=Count('id'))
        .order_by('city')
    )

    client_sales_summary = (
        Client.objects.annotate(
            orders_count=Count('orders', filter=Q(orders__sale__isnull=False)),
            revenue=Sum('orders__sale__total_amount'),
        )
        .filter(orders_count__gt=0)
        .order_by('last_name', 'first_name')
    )

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

    monthly_sales = list(
        Sale.objects.values('paid_at__year', 'paid_at__month')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('paid_at__year', 'paid_at__month')
    )

    monthly_category_sales = (
        Sale.objects.values(
            'paid_at__year',
            'paid_at__month',
            'order__items__car__category__name',
        )
        .annotate(
            sold_count=Sum('order__items__quantity'),
            total=Sum(
                ExpressionWrapper(
                    F('order__items__quantity') * F('order__items__unit_price'),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            ),
        )
        .order_by('paid_at__year', 'paid_at__month', 'order__items__car__category__name')
    )

    annual_revenue = (
        Sale.objects.values('paid_at__year')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('paid_at__year')
    )

    sales_forecast = build_linear_forecast(monthly_sales)
    category_chart = build_category_revenue_chart(category_sales)
    trend_chart = build_sales_trend_chart(sales_forecast)

    context = {
        'price_list': price_list,
        'clients_by_city': clients_by_city,
        'client_sales_summary': client_sales_summary,
        'most_popular_car': most_popular_car,
        'unpopular_cars': unpopular_cars,
        'category_sales': category_sales,
        'category_sales_chart': category_chart,
        'monthly_sales': monthly_sales,
        'monthly_category_sales': monthly_category_sales,
        'sales_forecast': sales_forecast,
        'sales_trend_chart': trend_chart,
        'matplotlib_available': bool(category_chart or trend_chart),
        'annual_revenue': annual_revenue,
        'average_sale': average_sale,
        'median_sale': median_sale,
        'mode_sale': mode_sale,
    }
    return render(request, 'analytics/dashboard.html', context)
