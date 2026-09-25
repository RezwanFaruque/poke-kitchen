from django.urls import path
from . import views


urlpatterns = [
    path('', views.restaurants, name='home'),
    path('restaurants/', views.restaurants, name='restaurants'),
    path('restarurants/', views.restaurants, name='restaruant'),
]