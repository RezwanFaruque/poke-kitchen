from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import KitchenOrderForm
from .models import Kitchen, KitchenOrder


def kitchens(request):
    kitchens = Kitchen.objects.all()
    recent_orders = KitchenOrder.objects.select_related('kitchen').order_by('-created_at')[:10]
    return render(request, 'member.html', {'kitchens': kitchens, 'orders': recent_orders})


def kitchen_orders(request):
    orders = KitchenOrder.objects.select_related('kitchen').order_by('-created_at')
    return render(
        request,
        'orders.html',
        {'orders': orders, 'status_choices': KitchenOrder.STATUS_CHOICES},
    )

def view_order(request, order_id):
    order = get_object_or_404(
        KitchenOrder.objects.select_related('kitchen'),
        pk=order_id,
    )
    return render(request, 'order_detail.html', {'order': order})

@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(KitchenOrder, pk=order_id)
    status = request.POST.get('status')
    if status not in dict(KitchenOrder.STATUS_CHOICES):
        return HttpResponseBadRequest('Invalid order status.')

    order.status = status
    order.updated_at = timezone.now()
    order.save(update_fields=['status', 'updated_at'])
    return redirect('kitchen_orders')


def create_kitchen_order(request):
    form = KitchenOrderForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('kitchen_orders')
    return render(request, 'order_form.html', {'form': form})


def restaurants(request):
    return kitchens(request)