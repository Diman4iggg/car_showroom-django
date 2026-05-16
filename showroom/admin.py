from django.contrib import admin

from .models import Car, CarCategory, CarFeature, Manufacturer


@admin.register(CarCategory)
class CarCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'website')
    list_filter = ('country',)
    search_fields = ('name', 'country')


@admin.register(CarFeature)
class CarFeatureAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'manufacturer',
        'category',
        'year',
        'price',
        'stock',
        'is_available',
    )
    list_filter = ('category', 'manufacturer', 'fuel_type', 'is_available', 'year')
    search_fields = ('name', 'manufacturer__name', 'description')
    filter_horizontal = ('features',)
