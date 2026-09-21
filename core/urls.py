from django.urls import path

from . import views


app_name = 'core'

urlpatterns = [
    path('about/', views.about, name='about'),
    path('news/', views.news, name='news'),
    path('news/<int:pk>/', views.news_detail, name='news_detail'),
    path('faq/', views.faq, name='faq'),
    path('contacts/', views.contacts, name='contacts'),
    path('privacy/', views.privacy, name='privacy'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('vacancies/create/', views.vacancy_create, name='vacancy_create'),
    path('vacancies/<int:pk>/update/', views.vacancy_update, name='vacancy_update'),
    path('vacancies/<int:pk>/delete/', views.vacancy_delete, name='vacancy_delete'),
    path('reviews/', views.reviews, name='reviews'),
    path('reviews/add/', views.add_review, name='add_review'),
    path('promo-codes/', views.promo_codes, name='promo_codes'),
]
