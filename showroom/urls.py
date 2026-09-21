from django.urls import path

from . import views

app_name = 'showroom'

urlpatterns = [
    path('', views.index, name='index'),
    path('cars/<int:car_id>/', views.car_detail, name='car_detail'),
    path('cars/<int:car_id>/buy/', views.buy_car, name='buy_car'),
]
