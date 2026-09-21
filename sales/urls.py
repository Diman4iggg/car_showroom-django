from django.urls import path, re_path

from . import views


app_name = 'sales'

urlpatterns = [
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:car_id>/', views.cart_add, name='cart_add'),
    re_path(
        r'^cart/(?P<car_id>\d+)/(?P<action>increase|decrease)/$',
        views.cart_update,
        name='cart_update',
    ),
    path('cart/remove/<int:car_id>/', views.cart_remove, name='cart_remove'),
    path('payment/', views.payment, name='payment'),
]
