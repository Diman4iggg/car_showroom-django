from django.contrib import admin

from .models import Client, Employee, Order, OrderItem, Sale


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'city', 'phone', 'email', 'created_at')
    list_filter = ('city',)
    search_fields = ('last_name', 'first_name', 'middle_name', 'phone', 'email', 'city')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'position', 'phone', 'email')
    list_filter = ('position',)
    search_fields = ('last_name', 'first_name', 'middle_name', 'phone', 'email')
    filter_horizontal = ('clients',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ('car',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'employee', 'status', 'order_date', 'delivery_date')
    list_filter = ('status', 'order_date', 'delivery_date')
    search_fields = ('client__last_name', 'client__first_name', 'employee__last_name')
    autocomplete_fields = ('client', 'employee')
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'car', 'quantity', 'unit_price')
    search_fields = ('car__name', 'order__client__last_name')
    autocomplete_fields = ('order', 'car')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('order', 'paid_at', 'total_amount')
    list_filter = ('paid_at',)
    search_fields = ('order__client__last_name', 'order__client__first_name')
    autocomplete_fields = ('order',)
