from django.urls import path

from . import views


app_name = 'integrations'

urlpatterns = [
    path('', views.api_dashboard, name='api_dashboard'),
]
