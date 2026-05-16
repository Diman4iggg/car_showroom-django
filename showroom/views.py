from django.shortcuts import render

from .models import Car, CarCategory


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
