from django.urls import path

from . import views


app_name = 'core'

urlpatterns = [
    path('about/', views.about, name='about'),
    path('news/', views.news, name='news'),
    path('faq/', views.faq, name='faq'),
    path('contacts/', views.contacts, name='contacts'),
    path('privacy/', views.privacy, name='privacy'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('reviews/', views.reviews, name='reviews'),
    path('promo-codes/', views.promo_codes, name='promo_codes'),
]
