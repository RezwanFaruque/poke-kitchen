from django.contrib import admin

from .models import Kitchen, KitchenOrder


@admin.register(Kitchen)
class KitchenAdmin(admin.ModelAdmin):
    list_display = ('name', 'member', 'created_at')
    search_fields = ('name',)


@admin.register(KitchenOrder)
class KitchenOrderAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'item_name', 'kitchen', 'status', 'quantity', 'created_at')
    list_filter = ('status', 'kitchen')
    search_fields = ('customer_name', 'item_name', 'kitchen__name')
