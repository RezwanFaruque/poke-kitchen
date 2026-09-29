from django.urls import path

from . import views


urlpatterns = [
    path('', views.kitchens, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('kitchens/', views.kitchens, name='kitchens'),
    path('restaurants/', views.restaurants, name='restaurants'),
    path('orders/', views.kitchen_orders, name='kitchen_orders'),
    path('orders/create/', views.create_kitchen_order, name='create_kitchen_order'),
    path('orders/suggestions/', views.order_suggestions, name='order_suggestions'),
    path('orders/view/<int:order_id>', views.view_order,name='view_kitchen_order'),
    path('orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('orders/<int:order_id>/delete/', views.delete_kitchen_order, name='delete_kitchen_order'),
    path('restarurants/', views.restaurants, name='restaruant'),
]