from django.shortcuts import redirect, render

from .forms import KitchenOrderForm
from .models import Kitchen, KitchenOrder


def kitchens(request):
    kitchens = Kitchen.objects.all()
    recent_orders = KitchenOrder.objects.select_related('kitchen').order_by('-created_at')[:10]
    return render(request, 'member.html', {'kitchens': kitchens, 'orders': recent_orders})


def kitchen_orders(request):
    orders = KitchenOrder.objects.select_related('kitchen').order_by('-created_at')
    return render(request, 'orders.html', {'orders': orders})


def create_kitchen_order(request):
    form = KitchenOrderForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('kitchen_orders')
    return render(request, 'order_form.html', {'form': form})


def restaurants(request):
    return kitchens(request)