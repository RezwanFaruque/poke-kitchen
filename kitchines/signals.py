from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Kitchen, KitchenOrder
from .vectorstore import delete_order, upsert_order


@receiver(post_save, sender=KitchenOrder)
def index_kitchen_order(sender, instance, **kwargs):
    upsert_order(instance)


@receiver(post_delete, sender=KitchenOrder)
def remove_kitchen_order(sender, instance, **kwargs):
    delete_order(instance.pk)


@receiver(post_save, sender=Kitchen)
def reindex_orders_for_kitchen(sender, instance, created, **kwargs):
    if created:
        return
    for order in instance.orders.select_related('kitchen').all():
        upsert_order(order)
