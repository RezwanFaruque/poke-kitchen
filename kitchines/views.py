from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import EmailAuthenticationForm, KitchenOrderForm, RegistrationForm
from .models import Kitchen, KitchenOrder
from .suggestions import generate_order_suggestion


def kitchens(request):
    kitchens = Kitchen.objects.all()
    recent_orders = KitchenOrder.objects.none()
    if request.user.is_authenticated:
        recent_orders = KitchenOrder.objects.filter(created_by=request.user).select_related('kitchen').order_by('-created_at')[:10]
    return render(request, 'member.html', {'kitchens': kitchens, 'orders': recent_orders})


@login_required
def kitchen_orders(request):
    orders = KitchenOrder.objects.filter(created_by=request.user).select_related('kitchen')
    return render(
        request,
        'orders.html',
        {'orders': orders, 'status_choices': KitchenOrder.STATUS_CHOICES},
    )

def _get_user_order(request, order_id):
    order = get_object_or_404(
        KitchenOrder.objects.filter(created_by=request.user).select_related('kitchen'),
        pk=order_id,
    )
    return order


@login_required
def view_order(request, order_id):
    order = _get_user_order(request, order_id)
    return render(request, 'order_detail.html', {'order': order})

@login_required
@require_POST
def update_order_status(request, order_id):
    order = _get_user_order(request, order_id)
    status = request.POST.get('status')
    if status not in dict(KitchenOrder.STATUS_CHOICES):
        return HttpResponseBadRequest('Invalid order status.')

    order.status = status
    order.updated_at = timezone.now()
    order.save(update_fields=['status', 'updated_at'])
    return redirect('kitchen_orders')


def _safe_redirect_url(next_url):
    if next_url and next_url.startswith('/') and not next_url.startswith('//'):
        return next_url
    return reverse('kitchen_orders')


@login_required
@require_POST
def delete_kitchen_order(request, order_id):
    order = _get_user_order(request, order_id)
    order.delete()
    return redirect(_safe_redirect_url(request.POST.get('next')))


@login_required
def create_kitchen_order(request):
    form = KitchenOrderForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        order = form.save(commit=False)
        order.created_by = request.user
        order.save()
        form.save_m2m()
        return redirect('kitchen_orders')
    return render(request, 'order_form.html', {'form': form})


@login_required
@require_POST
def order_suggestions(request):
    item_name = request.POST.get('item_name', '').strip()
    notes = request.POST.get('notes', '').strip()
    kitchen_id = request.POST.get('kitchen_id', '').strip()
    if not (item_name or notes) or not kitchen_id.isdigit():
        return JsonResponse({'suggestion': None}, status=400)
    kitchen = get_object_or_404(Kitchen, pk=kitchen_id)
    query = f'Kitchen: {kitchen.name}. Item: {item_name}. Notes: {notes}'[:1000]
    suggestion = generate_order_suggestion(query, request.user.pk, kitchen.pk)
    return JsonResponse(
        {
            'suggestion': suggestion,
            'message': '' if suggestion else 'No past orders found for your account in this kitchen yet.',
        },
    )


def restaurants(request):
    return kitchens(request)


@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        auth_login(request, user)
        return redirect('home')
    return render(request, 'register.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect('home')
    return render(
        request,
        'login.html',
        {'form': form, 'next': request.POST.get('next') or request.GET.get('next', '')},
    )


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect('login')