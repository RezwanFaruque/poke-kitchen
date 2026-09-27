from django.urls import path

from . import views


urlpatterns = [
    path('', views.kitchens, name='home'),
    path('kitchens/', views.kitchens, name='kitchens'),
    path('restaurants/', views.restaurants, name='restaurants'),
    path('orders/', views.kitchen_orders, name='kitchen_orders'),
    path('orders/create/', views.create_kitchen_order, name='create_kitchen_order'),
    path('orders/view/<int:order_id>', views.view_order,name='view_kitchen_order'),
    path('orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('restarurants/', views.restaurants, name='restaruant'),
]