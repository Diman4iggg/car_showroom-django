from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from . import views


app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('orders/<int:order_id>/client-cancel/', views.cancel_order, name='cancel_order'),
    re_path(
        r'^orders/(?P<order_id>\d+)/(?P<action>take|confirm|cancel|pay|deliver)/$',
        views.update_order_status,
        name='update_order_status',
    ),
]
